import argparse
import dataclasses
import json
import logging
import os
import pathlib
import re
import subprocess
import sys

import yaml


logging.basicConfig(level=logging.INFO, stream=sys.stdout)


@dataclasses.dataclass
class OCIResource:
    """OCI image that has been uploaded to Charmhub as a charm resource"""

    resource_name: str
    revision: int


@dataclasses.dataclass
class Revision:
    value: str
    architecture: str


def run(command_: list, *, log: bool = True, cwd: str | None = None):
    """Run subprocess command & log stderr

    Returns:
        stdout
    """
    process = subprocess.run(command_, capture_output=True, encoding="utf-8", cwd=cwd)
    try:
        process.check_returncode()
    except subprocess.CalledProcessError as e:
        if log:
            logging.error(e.stderr)
        raise
    return process.stdout.strip()


def snap():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", required=True)
    parser.add_argument("--channel", required=True)
    parser.add_argument("--create-tags", required=True)
    args = parser.parse_args()
    directory = pathlib.Path(args.directory)

    snap_name = yaml.safe_load((directory / "snap/snapcraft.yaml").read_text())["name"]

    @dataclasses.dataclass
    class Revision:
        value: int
        architecture: str

    revisions = []
    for snap_file in directory.glob("*.snap"):
        # Example `snap_file.name`: "charmed-postgresql_14.11_amd64.snap"
        # Example: "amd64"
        architecture = snap_file.name.removesuffix(".snap").split("_")[-1]
        logging.info(f"Uploading {snap_file=}")
        output = run(["snapcraft", "upload", "--release", args.channel, snap_file])
        # Example `output`: "Revision 3 created for 'charmed-postgresql' and released to 'latest/edge'"
        match = re.match("Revision ([0-9]+) created for ", output)
        assert match, "Unable to parse revision"
        revision = int(match.group(1))
        logging.info(f"Uploaded snap {revision=} {architecture=}")
        revisions.append(Revision(value=revision, architecture=architecture))

    if json.loads(args.create_tags) is not True:
        return
    if directory == pathlib.Path("."):
        tag_prefix = "rev"
    else:
        tag_prefix = f"{snap_name}/rev"
    logging.info("Pushing git tag(s)")
    tags = [f"{tag_prefix}{revision.value}" for revision in revisions]
    for tag in tags:
        subprocess.run(["git", "tag", tag], check=True)
        subprocess.run(["git", "push", "origin", tag], check=True)


def rock():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", required=True)
    parser.add_argument("--create-tags", required=True)
    args = parser.parse_args()
    directory = pathlib.Path(args.directory)

    yaml_data = yaml.safe_load((directory / "rockcraft.yaml").read_text())
    digests = []
    for rock_file in directory.glob("*.rock"):
        digest = run(
            [
                "skopeo",
                "inspect",
                f"oci-archive:{rock_file.name}",
                "--format",
                "{{ .Digest }}",
            ]
        )
        logging.info(f"Uploading {rock_file=}")
        run(
            [
                "skopeo",
                "copy",
                f"oci-archive:{rock_file.name}",
                f"docker://ghcr.io/canonical/{yaml_data['name']}@{digest}",
            ]
        )
        logging.info(f"Uploaded rock {digest=}")
        digests.append(digest)
    logging.info("Creating multi-architecture image")
    # Example: "14.10-22.04_edge"
    tag = f"{yaml_data['version']}-{yaml_data['base'].split('@')[-1]}_edge"
    multi_arch_image_name = f"ghcr.io/canonical/{yaml_data['name']}:{tag}"
    command = ["docker", "manifest", "create", multi_arch_image_name]
    for digest in digests:
        command.extend(("--amend", f"ghcr.io/canonical/{yaml_data['name']}@{digest}"))
    run(command)
    logging.info("Created multi-architecture image. Uploading")
    run(["docker", "manifest", "push", multi_arch_image_name])
    logging.info("Uploaded multi-architecture image")
    # Potential race condition if another image uploaded to same GHCR tag before this command runs
    multi_arch_digest = (
        run(
            [
                "skopeo",
                "inspect",
                f"docker://{multi_arch_image_name}",
                "--format",
                "{{ .Digest }}",
            ]
        )
        .strip()
        .removeprefix("sha256:")
    )

    if json.loads(args.create_tags) is not True:
        return
    logging.info("Pushing git tag")
    tag = f"image-{multi_arch_digest}"
    subprocess.run(["git", "tag", tag], check=True)
    subprocess.run(["git", "push", "origin", tag], check=True)


def charm():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", required=True)
    parser.add_argument("--channel", required=True)
    parser.add_argument("--create-tags", required=True)
    parser.add_argument("--file-resource", required=False, default="None")
    args = parser.parse_args()
    directory = pathlib.Path(args.directory)
    cwd = directory.absolute()
    file_resource = (
        None if args.file_resource == "None" else pathlib.Path(args.file_resource)
    )

    metadata_file = yaml.safe_load((directory / "metadata.yaml").read_text())
    charm_name = metadata_file["name"]

    # Upload charm file(s) & store revision
    charm_revisions: list[Revision] = []
    for charm_file in directory.glob("*.charm"):
        architecture = charm_file.name.removesuffix(".charm").split("_")[-1]
        logging.info(f"Uploading {charm_file=}")
        existing_revision: int | None = None
        try:
            output = run(
                ["charmcraft", "upload", "--format", "json", charm_file.absolute()],
                cwd=cwd,
            )
        except subprocess.CalledProcessError as e:
            # Handle the issue when charmcraft crashes, but the charm is uploaded.
            # e.g. https://github.com/canonical/charmcraft/issues/2492
            raw_error = f"{e.stdout}\n{e.stderr}"
            if match := re.findall(
                "Revision of the existing package is: ([0-9]+)", raw_error
            ):
                existing_revision = int(match[0])
                logging.info(f"Using existing charm revision: {existing_revision}")
            else:
                raise
        revision: int = (
            existing_revision if existing_revision else json.loads(output)["revision"]
        )
        logging.info(f"Uploaded charm {revision=}")
        charm_revisions.append(Revision(architecture=architecture, value=revision))
    assert len(charm_revisions) > 0, "No charm packages found"

    oci_resources: list[OCIResource] = []
    resources = metadata_file.get("resources", {})
    for resource_name, resource in resources.items():
        is_oci_image = resource["type"] == "oci-image"
        if not is_oci_image and file_resource is None:
            continue
        logging.info(f"Uploading charm resource: {resource_name}")
        resource_args = (
            ["--image", f"docker://{resource['upstream-source']}"]
            if is_oci_image
            else ["--filepath", f"{file_resource.absolute()}"]
        )
        output = run(
            [
                "charmcraft",
                "upload-resource",
                "--format",
                "json",
                charm_name,
                resource_name,
                *resource_args,
            ],
            cwd=cwd,
        )
        revision: int = json.loads(output)["revision"]
        logging.info(f"Uploaded charm resource {revision=}")
        oci_resources.append(OCIResource(resource_name, revision))

    # Release charm file(s)
    for charm_revision in charm_revisions:
        logging.info(f"Releasing {charm_revision=}")
        command = [
            "charmcraft",
            "release",
            charm_name,
            "--revision",
            str(charm_revision.value),
            "--channel",
            args.channel,
        ]
        for oci in oci_resources:
            command += ["--resource", f"{oci.resource_name}:{oci.revision}"]
        run(command, cwd=cwd)

    if json.loads(args.create_tags) is not True:
        return
    if directory == pathlib.Path("."):
        tag_prefix = "rev"
    else:
        tag_prefix = f"{charm_name}/rev"
    subprocess.run(["git", "config", "user.name", "GitHub Actions"], check=True)
    subprocess.run(
        [
            "git",
            "config",
            "user.email",
            "41898282+github-actions[bot]@users.noreply.github.com",
        ],
        check=True,
    )
    logging.info("Pushing git tag(s)")
    tags = [f"{tag_prefix}{revision.value}" for revision in charm_revisions]
    for tag in tags:
        subprocess.run(["git", "tag", tag, "--annotate", "-m", tag], check=True)
        subprocess.run(["git", "push", "origin", tag], check=True)

    revisions_dict = {rev.architecture: rev.value for rev in charm_revisions}
    output: str = f"charm-revisions={json.dumps(revisions_dict)}"
    with open(os.environ["GITHUB_OUTPUT"], "a") as file:
        file.write(output)
