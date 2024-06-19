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

from . import craft

logging.basicConfig(level=logging.INFO, stream=sys.stdout)


@dataclasses.dataclass
class OCIResource:
    """OCI image that has been uploaded to Charmhub as a charm resource"""

    resource_name: str
    revision: int


def run(command_: list):
    """Run subprocess command & log stderr

    Returns:
        stdout
    """
    process = subprocess.run(command_, capture_output=True, encoding="utf-8")
    try:
        process.check_returncode()
    except subprocess.CalledProcessError as e:
        logging.error(e.stderr)
        raise
    return process.stdout


def snap():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", required=True)
    parser.add_argument("--channel", required=True)
    args = parser.parse_args()
    directory = pathlib.Path(args.directory)

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
        # Example `output`: "Revision 3 created for 'charmed-postgresql' and released to 'latest/edge'\n"
        match = re.match("Revision ([0-9]+) created for ", output)
        assert match, "Unable to parse revision"
        revision = int(match.group(1))
        logging.info(f"Uploaded snap {revision=} {architecture=}")
        revisions.append(Revision(value=revision, architecture=architecture))

    # Output GitHub release info
    release_tag = f"rev{max(revision.value for revision in revisions)}"
    if len(revisions) == 1:
        release_title = "Revision "
    else:
        release_title = "Revisions "
    release_title += ", ".join(str(revision.value) for revision in revisions)
    release_notes = f"Released to {args.channel}"
    for revision in revisions:
        release_notes += f"\n- {revision.architecture}: revision {revision.value}"
    with open("release_notes.txt", "w") as file:
        file.write(release_notes)
    output = f"release_tag={release_tag}\nrelease_title={release_title}"
    logging.info(output)
    with open(os.environ["GITHUB_OUTPUT"], "a") as file:
        file.write(output)


def rock():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", required=True)
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
        ).strip()
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
    command = [
        "docker",
        "manifest",
        "create",
        f'ghcr.io/canonical/{yaml_data["name"]}:{tag}',
    ]
    for digest in digests:
        command.extend(("--amend", f'ghcr.io/canonical/{yaml_data["name"]}@{digest}'))
    run(command)
    logging.info("Created multi-architecture image. Uploading")
    run(
        [
            "docker",
            "manifest",
            "push",
            f'ghcr.io/canonical/{yaml_data["name"]}:{tag}',
        ]
    )
    logging.info("Uploaded multi-architecture image")


def charm():
    # Remove `charmcraft.yaml` from working directory (directory that subprocess will run as) if it
    # exists.
    # Workaround for https://github.com/canonical/charmcraft/issues/1389
    pathlib.Path("charmcraft.yaml").unlink(missing_ok=True)

    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", required=True)
    parser.add_argument("--channel", required=True)
    args = parser.parse_args()
    directory = pathlib.Path(args.directory)

    # Upload charm file(s) & store revision
    charm_revisions: list[int] = []
    for charm_file in directory.glob("*.charm"):
        logging.info(f"Uploading {charm_file=}")
        output = run(["charmcraft", "upload", "--format", "json", charm_file])
        revision: int = json.loads(output)["revision"]
        logging.info(f"Uploaded charm {revision=}")
        charm_revisions.append(revision)
    assert len(charm_revisions) > 0, "No charm packages found"

    metadata_file = yaml.safe_load((directory / "metadata.yaml").read_text())
    charm_name = metadata_file["name"]

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

    # Output GitHub release info
    release_tag = f"rev{max(charm_revisions)}"
    if len(charm_revisions) == 1:
        release_title = "Revision "
    else:
        release_title = "Revisions "
    release_title += ", ".join(str(revision) for revision in charm_revisions)
    release_notes = f"Released to {args.channel}\nOCI images:\n" + "\n".join(
        f"- {dataclasses.asdict(oci)}" for oci in oci_resources
    )
    with open("release_notes.txt", "w") as file:
        file.write(release_notes)
    output = f"release_tag={release_tag}\nrelease_title={release_title}"
    logging.info(output)
    with open(os.environ["GITHUB_OUTPUT"], "a") as file:
        file.write(output)
