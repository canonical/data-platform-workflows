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


def run(command_: list, *, cwd=None):
    """Run subprocess command & log stderr

    Returns:
        stdout
    """
    process = subprocess.run(command_, capture_output=True, text=True, cwd=cwd)
    try:
        process.check_returncode()
    except subprocess.CalledProcessError as e:
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
    channel = args.channel

    if channel == "":
        raise ValueError("`channel` input must not be empty string")

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
        output = run(["snapcraft", "upload", "--release", channel, snap_file])
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
    subprocess.run(["git", "config", "user.name", "GitHub Actions"], check=True)
    subprocess.run(
        ["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"],
        check=True,
    )
    for tag in tags:
        subprocess.run(["git", "tag", tag, "--annotate", "-m", tag], check=True)
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
    subprocess.run(["git", "config", "user.name", "GitHub Actions"], check=True)
    subprocess.run(
        ["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"],
        check=True,
    )
    subprocess.run(["git", "tag", tag, "--annotate", "-m", tag], check=True)
    subprocess.run(["git", "push", "origin", tag], check=True)


def _charm(*, pr: bool):
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", required=True)
    parser.add_argument("--track", required=True)
    if pr:
        parser.add_argument("--pr-number", required=True, type=int)
    args = parser.parse_args()
    directory = pathlib.Path(args.directory)

    metadata_file = yaml.safe_load((directory / "metadata.yaml").read_text())
    charm_name = metadata_file["name"]

    track = args.track
    if track == "":
        raise ValueError("`track` input must not be empty string")
    channel = f"{track}/edge"
    if pr:
        channel += f"/pr-{args.pr_number}"

    # Release charm file(s) & store revision
    charm_revisions: list[int] = []
    for charm_file in directory.glob("*.charm"):
        logging.info(f"Releasing {charm_file=}")
        output = run(
            [
                "noctua",
                "charm",
                "release",
                charm_name,
                "--json",
                "--path",
                str(charm_file.relative_to(directory)),
                "--channel",
                channel,
            ],
            cwd=directory,
        )
        revision: int = json.loads(output)["revision"]
        logging.info(f"Released charm {revision=}")
        charm_revisions.append(revision)
    assert len(charm_revisions) > 0, "No charm packages found"

    if pr:
        return
    if directory == pathlib.Path("."):
        tag_prefix = "rev"
    else:
        tag_prefix = f"{charm_name}/rev"
    logging.info("Pushing git tag(s)")
    tags = [f"{tag_prefix}{revision}" for revision in charm_revisions]
    subprocess.run(["git", "config", "user.name", "GitHub Actions"], check=True)
    subprocess.run(
        ["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"],
        check=True,
    )
    for tag in tags:
        subprocess.run(["git", "tag", tag, "--annotate", "-m", tag], check=True)
        subprocess.run(["git", "push", "origin", tag], check=True)


def charm_edge():
    _charm(pr=False)


def charm_pr():
    _charm(pr=True)
