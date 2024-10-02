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
from typing import Optional, Dict, Tuple


def get_ubuntu_version(series: str) -> str:
    """Gets Ubuntu version (e.g. "22.04") from series (e.g. "jammy")."""
    return subprocess.run(
        ["ubuntu-distro-info", "--series", series, "--release"],
        capture_output=True,
        check=True,
        encoding="utf-8",
    ).stdout.split(" ")[0]


def fetch_charm_info_from_store(charm, charm_channel) -> Tuple[Dict, Dict]:
    """Returns, for a given channel, the necessary charm info from store endpoint."""
    response = requests.get(
        f"https://api.snapcraft.io/v2/charms/info/{charm}?fields=channel-map,default-release&channel={charm_channel}"
    )
    return response.json()["channel-map"], response.json()["default-release"].get("resources", [])


def fetch_latest_revision(channel_map, series=None) -> int:
    """Gets the latest charm revision number in channel."""
    revisions = []
    for channel in channel_map:
        if (
            channel["channel"]["base"]["architecture"] == "amd64"
            and (
                series is None
                or get_ubuntu_version(series) == channel["channel"]["base"]["channel"]
            )
        ):
            revisions.append(channel["revision"]["revision"])
    if not revisions:
        return None
    # If the charm supports multiple Ubuntu bases (and series=None), it's
    # possible that there is a different revision for each base.
    # Select the latest revision.
    return max(revisions)


def fetch_oci_image_metadata(download_url) -> Tuple[str, str, str]:
    """Retrieves remote OCI image path and credentials for download."""
    response = requests.get(download_url)
    image_name = response.json()["ImageName"]
    oci_username = response.json()["Username"]
    oci_password = response.json()["Password"]
    return f"docker://{image_name}", oci_username, oci_password


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
        channel_map, resources = fetch_charm_info_from_store(app['charm'], app['channel'])

        if latest_revision := fetch_latest_revision(channel_map, app.get("series", default_series)):
            app["revision"] = latest_revision
        else:
            raise ValueError(
                f"Revision not found for {app['charm']} on {app['channel']} for Ubuntu {app.get('series', default_series)}"
            )
        for resource in resources:
            if resource["type"] == "oci-image":
                image_path, oci_username, oci_password = fetch_oci_image_metadata(resource["download"]["url"])
                app["resources"] = {
                    resource["name"]: {
                        "revision": resource["revision"],
                        "oci-image": image_path,
                        "oci-password": oci_username,
                        "oci-username": oci_password,
                    }
                }
    with open(file_path, "w") as file:
        yaml.dump(file_data, file)

    github_actions.output["updates_available"] = json.dumps(old_file_data != file_data)
