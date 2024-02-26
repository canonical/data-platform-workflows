import argparse
import dataclasses
import json
import logging
import os
import pathlib
import subprocess
import sys

import yaml

from . import charmcraft


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


def main():
    # Remove `charmcraft.yaml` from working directory (directory that subprocess will run as) if it
    # exists.
    # Workaround for https://github.com/canonical/charmcraft/issues/1389
    pathlib.Path("charmcraft.yaml").unlink(missing_ok=True)

    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    parser = argparse.ArgumentParser()
    parser.add_argument("--charm-directory", required=True)
    parser.add_argument("--channel", required=True)
    args = parser.parse_args()
    charm_directory = pathlib.Path(args.charm_directory)

    # Upload charm file(s) & store revision
    charm_revisions: dict[charmcraft.Architecture, list[int]] = {}
    for charm_file in charm_directory.glob("*.charm"):
        # Examples of `charm_file.name`:
        # - "mysql-router-k8s_ubuntu-22.04-amd64.charm"
        # - "mysql-router-k8s_ubuntu-22.04-amd64-arm64.charm"
        architectures = (
            charm_file.name.split("_")[-1].removesuffix(".charm").split("-")[2:]
        )
        assert (
            len(architectures) == 1
        ), f"Multiple architectures ({architectures}) in one (charmcraft.yaml) base not supported. Use one base per architecture"
        architecture = charmcraft.Architecture(architectures[0])
        logging.info(f"Uploading {charm_file=} {architecture=}")
        output = run(["charmcraft", "upload", "--format", "json", charm_file])
        revision: int = json.loads(output)["revision"]
        logging.info(f"Uploaded charm {revision=}")
        charm_revisions.setdefault(architecture, []).append(revision)
    assert len(charm_revisions) > 0, "No charm packages found"

    metadata_file = yaml.safe_load((charm_directory / "metadata.yaml").read_text())
    charm_name = metadata_file["name"]

    # (Only for Kubernetes charms) upload OCI image(s) & store revision
    oci_resources: dict[charmcraft.Architecture, list[OCIResource]] = {}
    resources = metadata_file.get("resources", {})
    for resource_name, resource in resources.items():
        if resource["type"] != "oci-image":
            continue
        for architecture in charm_revisions.keys():
            # Format: ST111 - Multi-architecture `upstream-source` in charm OCI resources
            # https://docs.google.com/document/d/19pzpza7zj7qswDRSHBlpqdBrA7Ndcnyh6_75cCxMKSo/edit
            upstream_source = resource.get("upstream-source")
            if upstream_source is not None and "upstream-sources" in resource:
                raise ValueError(
                    "`upstream-sources` and `upstream-source` cannot be used simultaneously. Use only `upstream-sources`"
                )
            elif upstream_source:
                # Default to X64
                upstream_sources = {charmcraft.Architecture.X64.value: upstream_source}
            else:
                upstream_sources = resource["upstream-sources"]
            image_name = upstream_sources[architecture.value]
            logging.info(f"Downloading OCI image ({architecture=}): {image_name}")
            run(["docker", "pull", image_name])
            image_id = run(
                ["docker", "image", "inspect", image_name, "--format", "'{{.Id}}'"]
            )
            image_id = image_id.rstrip("\n").strip("'").removeprefix("sha256:")
            assert "\n" not in image_id, f"Multiple local images found for {image_name}"
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
                    image_id,
                ]
            )
            revision: int = json.loads(output)["revision"]
            logging.info(f"Uploaded charm resource {revision=}")
            oci_resources.setdefault(architecture, []).append(
                OCIResource(resource_name, revision)
            )

    # Release charm file(s)
    for architecture, revisions in charm_revisions.items():
        for charm_revision in revisions:
            logging.info(f"Releasing {charm_revision=} {architecture=}")
            command = [
                "charmcraft",
                "release",
                charm_name,
                "--revision",
                str(charm_revision),
                "--channel",
                args.channel,
            ]
            for oci in oci_resources[architecture]:
                command += ["--resource", f"{oci.resource_name}:{oci.revision}"]
            run(command)

    # Output GitHub release info
    release_tag = f"rev{max(charm_revisions)}"
    if len(charm_revisions) == 1:
        release_title = "Revision "
    else:
        release_title = "Revisions "
    release_title += ", ".join(str(revision) for revision in charm_revisions)
    oci_info = "OCI images:"
    for architecture, resources in oci_resources.items():
        oci_info += f"\n- {architecture}:"
        for oci in resources:
            oci_info += f"\n    - {dataclasses.asdict(oci)}"
    release_notes = f"Released to {args.channel}\n{oci_info}"
    with open("release_notes.txt", "w") as file:
        file.write(release_notes)
    output = f"release_tag={release_tag}\nrelease_title={release_title}"
    logging.info(output)
    with open(os.environ["GITHUB_OUTPUT"], "a") as file:
        file.write(output)
