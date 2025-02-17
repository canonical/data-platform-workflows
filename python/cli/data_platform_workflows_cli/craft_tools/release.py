import argparse
import dataclasses
import json
import logging
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


def run(command_: list, *, log_error=True):
    """Run subprocess command & log stderr

    Returns:
        stdout
    """
    process = subprocess.run(command_, capture_output=True, text=True)
    try:
        process.check_returncode()
    except subprocess.CalledProcessError as e:
        if log_error:
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
                f'docker://ghcr.io/canonical/{yaml_data["name"]}@{digest}',
            ]
        )
        logging.info(f"Uploaded rock {digest=}")
        digests.append(digest)
    logging.info("Creating multi-architecture image")
    # Example: "14.10-22.04_edge"
    tag = f'{yaml_data["version"]}-{yaml_data["base"].split("@")[-1]}_edge'
    multi_arch_image_name = f'ghcr.io/canonical/{yaml_data["name"]}:{tag}'
    command = ["docker", "manifest", "create", multi_arch_image_name]
    for digest in digests:
        command.extend(("--amend", f'ghcr.io/canonical/{yaml_data["name"]}@{digest}'))
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
    args = parser.parse_args()
    directory = pathlib.Path(args.directory)

    metadata_file = yaml.safe_load((directory / "metadata.yaml").read_text())
    charm_name = metadata_file["name"]

    # Upload charm file(s) & store revision
    charm_revisions: list[int] = []
    for charm_file in directory.glob("*.charm"):
        logging.info(f"Uploading {charm_file=}")
        try:
            output = run(["charmcraft", "upload", "--format", "json", charm_file], log_error=False)
        except subprocess.CalledProcessError as e:
            try:
                errors = json.loads(e.stdout)["errors"]
            except (json.JSONDecodeError, KeyError):
                logging.error(e.stderr)
                raise
            else:
                if len(errors) != 1:
                    logging.error(e.stderr)
                    raise
                error = errors[0]
                if error.get("code") != "review-error":
                    logging.error(e.stderr)
                    raise
                match = re.fullmatch(
                    r".*?Revision of the existing package is: (?P<revision>[0-9]+)",
                    error.get("message", ""),
                )
                if not match:
                    logging.error(e.stderr)
                    raise
                revision = int(match.group("revision"))
                logging.warning(f"{charm_file=} already uploaded. Using existing {revision=}")
        else:
            revision: int = json.loads(output)["revision"]
            logging.info(f"Uploaded charm {revision=}")
        charm_revisions.append(revision)
    assert len(charm_revisions) > 0, "No charm packages found"

    # (Only for Kubernetes charms) upload OCI image(s) & store revision
    oci_resources: list[OCIResource] = []
    resources = metadata_file.get("resources", {})
    for resource_name, resource in resources.items():
        if resource["type"] != "oci-image":
            continue
        logging.info(f"Uploading charm resource: {resource_name}")
        output = run(
            [
                "charmcraft",
                "upload-resource",
                "--format",
                "json",
                charm_name,
                resource_name,
                "--image",
                f'docker://{resource["upstream-source"]}',
            ]
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
            str(charm_revision),
            "--channel",
            args.channel,
        ]
        for oci in oci_resources:
            command += ["--resource", f"{oci.resource_name}:{oci.revision}"]
        run(command)

    if json.loads(args.create_tags) is not True:
        return
    if directory == pathlib.Path("."):
        tag_prefix = "rev"
    else:
        tag_prefix = f"{charm_name}/rev"
    logging.info("Pushing git tag(s)")
    tags = [f"{tag_prefix}{revision}" for revision in charm_revisions]
    for tag in tags:
        subprocess.run(["git", "tag", tag], check=True)
        subprocess.run(["git", "push", "origin", tag], check=True)
