import argparse
import dataclasses
import json
import logging
import os
import pathlib
import subprocess
import sys

import yaml


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


logging.basicConfig(level=logging.INFO, stream=sys.stdout)
parser = argparse.ArgumentParser()
parser.add_argument("--charm-directory")
parser.add_argument("--channel")
args = parser.parse_args()
charm_directory = pathlib.Path(args.charm_directory)

# Upload charm file(s) & store revision
charm_revisions: list[int] = []
for charm_file in charm_directory.glob("*.charm"):
    logging.info(f"Uploading {charm_file=}")
    output = run(["charmcraft", "upload", "--format", "json", charm_file])
    revision: int = json.loads(output)["revision"]
    logging.info(f"Uploaded charm {revision=}")
    charm_revisions.append(revision)
assert len(charm_revisions) > 0, "No .charm files found"

metadata_file = yaml.safe_load((charm_directory / "metadata.yaml").read_text())
charm_name = metadata_file["name"]

# (Only for Kubernetes charms) upload OCI image(s) & store revision
oci_resources: list[OCIResource] = []
resources = metadata_file.get("resources", {})
for resource_name, resource in resources.items():
    if resource["type"] != "oci-image":
        continue
    image_name = resource["upstream-source"]
    logging.info(f"Downloading OCI image: {image_name}")
    run(["docker", "pull", image_name])
    logging.info(f"Uploading charm resource: {resource_name}")
    # Remove digest or tag from image name before passing to charmcraft
    # (charmcraft expects an image name without a digest or tag
    # [Note: charmcraft can accept a digest without an image name, but we're not using that here.])
    if "@" in image_name:
        image_name = image_name.split("@")[0]
    elif ":" in image_name:
        image_name = image_name.split(":")[0]
    output = run(
        [
            "charmcraft",
            "upload-resource",
            "--format",
            "json",
            charm_name,
            resource_name,
            "--image",
            image_name,
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
with open(os.environ["GITHUB_OUTPUT"], "a") as file:
    file.write(f"release_tag={release_tag}\nrelease_title={release_title}")
