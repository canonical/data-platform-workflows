# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
"""Update charm revisions in bundle YAML file"""
import argparse
import copy
import json
import os
import pathlib
import subprocess

import requests
import yaml

from . import github_actions
from typing import Optional, Dict


def get_ubuntu_version(series: str) -> str:
    """Gets Ubuntu version (e.g. "22.04") from series (e.g. "jammy")."""
    return subprocess.run(
        ["ubuntu-distro-info", "--series", series, "--release"],
        capture_output=True,
        check=True,
        encoding="utf-8",
    ).stdout.split(" ")[0]


def fetch_latest_revision(charm, charm_channel, series=None) -> int:
    """Gets the latest charm revision number in channel."""
    response = requests.get(
        f"https://api.snapcraft.io/v2/charms/info/{charm}?fields=channel-map"
    )
    response.raise_for_status()
    channel_map = response.json()["channel-map"]
    track, risk = charm_channel.split("/")
    revisions = []
    for channel in channel_map:
        if (
            channel["channel"]["risk"] == risk
            and channel["channel"]["track"] == track
            and channel["channel"]["base"]["architecture"] == "amd64"
        ):
            if (
                series is None
                or get_ubuntu_version(series) == channel["channel"]["base"]["channel"]
            ):
                revisions.append(channel["revision"]["revision"])
    if not revisions:
        raise ValueError(
            f"Revision not found for {charm} on {charm_channel} for Ubuntu {series}"
        )
    # If the charm supports multiple Ubuntu bases (and series=None), it's
    # possible that there is a different revision for each base.
    # Select the latest revision.
    return max(revisions)


def fetch_oci_image_from_channel(charm, charm_channel) -> Optional[Dict[str,str]]:
    """Gets the OCI image source from metadata.yaml of latest revision released in channel."""
    response = requests.get(
        f"https://api.snapcraft.io/v2/charms/info/{charm}?fields=default-release&channel={charm_channel}"
    )
    response.raise_for_status()
    default_release = response.json()["default-release"]
    metadata = yaml.safe_load(default_release["revision"]["metadata-yaml"])
    for resource_name, resource_data in metadata.get("resources", {}).items():
        if resource_data.get("type") == "oci-image" and "upstream-source" in resource_data:
            return {resource_name: resource_data["upstream-source"]}
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file_path")
    file_path = pathlib.Path(parser.parse_args().file_path)
    old_file_data = yaml.safe_load(file_path.read_text())
    file_data = copy.deepcopy(old_file_data)

    # Charm series detection is only supported for top-level and application-level "series" keys
    # Other charm series config (e.g. machine-level key) is not supported
    # Full list of possible series config (unsupported) can be found under "Charm series" at https://juju.is/docs/olm/bundle
    default_series = file_data.get("series")
    for app in file_data["applications"].values():
        app["revision"] = fetch_latest_revision(
            app["charm"], app["channel"], app.get("series", default_series)
        )
        if oci_image := fetch_oci_image_from_channel(app["charm"], app["channel"]):
            app["resources"] = oci_image

    with open(file_path, "w") as file:
        yaml.dump(file_data, file)

    github_actions.output["updates_available"] = json.dumps(old_file_data != file_data)
