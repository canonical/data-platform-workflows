# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
"""Update charm revisions in bundle YAML file"""
import argparse
import ast
import copy
import json
import pathlib
import subprocess

import requests
import yaml

from . import github_actions
from typing import Dict, Tuple


def get_ubuntu_version(series: str) -> str:
    """Gets Ubuntu version (e.g. "22.04") from series (e.g. "jammy")."""
    return subprocess.run(
        ["ubuntu-distro-info", "--series", series, "--release"],
        capture_output=True,
        check=True,
        encoding="utf-8",
    ).stdout.split(" ")[0]


def fetch_var_from_py_file(text, variable):
    """Parses .py file and returns the value assigned to a given variable inside it."""
    parsed = ast.parse(text)
    for node in ast.walk(parsed):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == variable:
                    return ast.literal_eval(node.value)
    return None


def fetch_charm_info_from_store(charm, charm_channel) -> Tuple[Dict, Dict]:
    """Returns, for a given channel, the necessary charm info from store endpoint."""
    response = requests.get(
        f"https://api.snapcraft.io/v2/charms/info/{charm}?fields=channel-map,default-release&channel={charm_channel}"
    )
    return response.json()["channel-map"], response.json()["default-release"].get("resources", [])


def fetch_latest_charm_revision(channel_map, series=None) -> int:
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


def fetch_grafana_snaps():
    """Fetch grafana-agent snaps information."""
    response = requests.get("https://raw.githubusercontent.com/canonical/grafana-agent-operator/refs/heads/main/src/snap_management.py")
    content = response.text

    snap_name = fetch_var_from_py_file(content, "_grafana_agent_snap_name")
    snaps = fetch_var_from_py_file(content, "_grafana_agent_snaps")

    if snap_name and snaps:
        result = []
        for (confinement, arch), revision in snaps.items():
            if arch == "amd64":
                result.append({
                    "name": snap_name,
                    "revision": revision,
                    "channel": "latest/stable"
                })
        return result
    else:
        raise ValueError("Required grafana-agent snap variables not found in the file")


def fetch_mysql_snaps():
    """Fetch mysql-operator snaps information."""
    resp_revision = requests.get("https://raw.githubusercontent.com/canonical/mysql-operator/refs/heads/main/snap_revisions.json")
    resp_name = requests.get("https://raw.githubusercontent.com/canonical/mysql-operator/refs/heads/main/src/constants.py")
    
    snap_revision = resp_revision.json().get("x86_64")
    snap_name = fetch_var_from_py_file(resp_name.text, "CHARMED_MYSQL_SNAP_NAME")

    if snap_name and snap_revision:
        result = [{
            "name": snap_name,
            "revision": int(snap_revision),
            "channel": "8.0/edge",
        }]
        return result
    else:
        raise ValueError("Required mysql-operator snap variables not found in the file")


def fetch_mysql_router_snaps():
    """Fetch mysql-router snaps information."""
    response = requests.get("https://raw.githubusercontent.com/canonical/mysql-router-operator/refs/heads/main/src/snap.py")

    snap_name = fetch_var_from_py_file(response.text, "_SNAP_NAME")
    revisions = fetch_var_from_py_file(response.text, "REVISIONS")

    if snap_name and revisions:
        result = [{
            "name": snap_name,
            "revision": int(revisions["x86_64"]),
            "channel": "8.0/edge",
        }]
        return result
    else:
        raise ValueError("Required mysql-router snap variables not found in the file")


def fetch_postgresql_snaps():
    """Fetch postgresql-operator snaps information."""
    response = requests.get("https://raw.githubusercontent.com/canonical/postgresql-operator/refs/heads/main/src/constants.py")

    snap_list = fetch_var_from_py_file(response.text, "SNAP_PACKAGES")

    if snap_list:
        result = []
        for snap_name, snap_info in snap_list:
            result.append({
                "name": snap_name,
                "revision": int(snap_info["revision"]["x86_64"]),
                "channel": snap_info["channel"],
            })
        return result
    else:
        raise ValueError("Required postgresql-operator snap variables not found in the file")


def fetch_pgbouncer_snaps():
    """Fetch pgbouncer-operator snaps information."""
    response = requests.get("https://raw.githubusercontent.com/canonical/pgbouncer-operator/refs/heads/main/src/constants.py")

    snap_list = fetch_var_from_py_file(response.text, "SNAP_PACKAGES")

    if snap_list:
        result = []
        for snap_name, snap_info in snap_list:
            result.append({
                "name": snap_name,
                "revision": int(snap_info["revision"]["x86_64"]),
                "channel": snap_info["channel"],
            })
        return result
    else:
        raise ValueError("Required pgbouncer-operator snap variables not found in the file")


SNAP_FETCHERS_BY_CHARM = {
    "grafana-agent": fetch_grafana_snaps,
    "pgbouncer": fetch_pgbouncer_snaps,
    "postgresql": fetch_postgresql_snaps,
    "mysql": fetch_mysql_snaps,
    "mysql-router": fetch_mysql_router_snaps,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle_file_path")
    parser.add_argument("snaps_file_path")
    bundle_file_path = pathlib.Path(parser.parse_args().bundle_file_path)
    snaps_file_path = pathlib.Path(parser.parse_args().bundle_file_path)
    updates_available = False
    old_bundle_data = {}
    old_snaps_data = {}

    try:
        old_bundle_data = yaml.safe_load(bundle_file_path.read_text())
        old_snaps_data = yaml.safe_load(snaps_file_path.read_text())
    except FileNotFoundError:
        updates_available = True
    bundle_data = copy.deepcopy(old_bundle_data)
    snaps_data = {"packages": []}

    # Charm series detection is only supported for top-level and application-level "series" keys
    # Other charm series config (e.g. machine-level key) is not supported
    # Full list of possible series config (unsupported) can be found under "Charm series" at https://juju.is/docs/olm/bundle
    default_series = bundle_data.get("series")
    for app in bundle_data["applications"].values():
        channel_map, resources = fetch_charm_info_from_store(app['charm'], app['channel'])
        if latest_revision := fetch_latest_charm_revision(channel_map, app.get("series", default_series)):
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
        if app["charm"] in SNAP_FETCHERS_BY_CHARM:
            fetcher_func = SNAP_FETCHERS_BY_CHARM[app["charm"]]
            snaps_list = fetcher_func()
            for snaps in snaps_list:
                snaps_data['packages'].append({
                    "name": snaps["name"],
                    "revision": snaps["revision"],
                    "push_channel": snaps["channel"],
                })    

    with open(bundle_file_path, "w") as file:
        yaml.dump(bundle_data, file)
    with open(snaps_file_path, "w") as file:
        yaml.dump(snaps_data, file)

    if not updates_available and (old_bundle_data != bundle_data or old_snaps_data != snaps_data):
        updates_available = True

    github_actions.output["updates_available"] = json.dumps(updates_available)
