# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
"""Update charm revisions in bundle YAML file"""
import argparse
import ast
import copy
import dataclasses
import json
import pathlib
import re
import subprocess

import requests
import yaml

from . import github_actions


@dataclasses.dataclass(order=True, frozen=True)
class Snap:
    name: str
    revision: int
    push_channel: str


def get_ubuntu_version(series: str) -> str:
    """Gets Ubuntu version (e.g. "22.04") from series (e.g. "jammy")."""
    return subprocess.run(
        ["ubuntu-distro-info", "--series", series, "--release"],
        capture_output=True,
        check=True,
        encoding="utf-8",
    ).stdout.split(" ")[0]


def fetch_var_from_py_file(text, variable, safe=True):
    """Parses .py file and returns the value assigned to a given variable inside it."""
    # While `ast.literal_eval` is safer and prefered, some vars are defined in terms of
    # expressions (e.g. f-strings), not literals. In such cases, `exec` is the only way.
    if not safe:
        namespace = {}
        exec(text, namespace)
        return namespace[variable]

    parsed = ast.parse(text)
    for node in ast.walk(parsed):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == variable:
                    return ast.literal_eval(node.value)
    return None


def fetch_charm_info_from_store(charm, charm_channel) -> tuple[list[dict], list[dict]]:
    """Returns, for a given channel, the necessary charm info from store endpoint."""
    response = requests.get(
        f"https://api.snapcraft.io/v2/charms/info/{charm}?fields=channel-map,default-release&channel={charm_channel}"
    )
    response.raise_for_status()
    content = response.json()
    return content["channel-map"], content["default-release"].get("resources", [])


def fetch_latest_charm_revision(channel_map, series=None) -> int | None:
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


def fetch_grafana_snaps(charm_revision) -> list[Snap]:
    """Fetch grafana-agent snaps information."""
    response = requests.get(f"https://raw.githubusercontent.com/canonical/grafana-agent-operator/refs/tags/rev{charm_revision}/src/snap_management.py")
    response.raise_for_status()
    content = response.text

    snap_name = fetch_var_from_py_file(content, "_grafana_agent_snap_name")
    snaps = fetch_var_from_py_file(content, "_grafana_agent_snaps")

    if snap_name and snaps:
        result = []
        for (confinement, arch), revision in snaps.items():
            if arch == "amd64":
                result.append(Snap(
                    name=snap_name,
                    revision=int(revision),
                    push_channel= "latest/stable"
                ))
        return result
    else:
        raise ValueError("Required grafana-agent snap variables not found in the file")


def fetch_mysql_snaps(charm_revision) -> list[Snap]:
    """Fetch mysql-operator snaps information."""
    resp_revision = requests.get(f"https://raw.githubusercontent.com/canonical/mysql-operator/refs/tags/rev{charm_revision}/snap_revisions.json")
    resp_revision.raise_for_status()
    resp_name = requests.get(f"https://raw.githubusercontent.com/canonical/mysql-operator/refs/tags/rev{charm_revision}/src/constants.py")
    resp_name.raise_for_status()
    
    snap_revision = resp_revision.json().get("x86_64")
    snap_name = fetch_var_from_py_file(resp_name.text, "CHARMED_MYSQL_SNAP_NAME")

    if snap_name and snap_revision:
        result = [Snap(
            name=snap_name,
            revision=int(snap_revision),
            push_channel="8.0/edge",
        )]
        return result
    else:
        raise ValueError("Required mysql-operator snap variables not found in the file")


def fetch_mysql_router_snaps(charm_revision) -> list[Snap]:
    """Fetch mysql-router snaps information."""
    response = requests.get(f"https://raw.githubusercontent.com/canonical/mysql-router-operator/refs/tags/rev{charm_revision}/src/snap.py")
    response.raise_for_status()

    snap_name = fetch_var_from_py_file(response.text, "_SNAP_NAME")
    amd64_rev_number = re.search(r'"x86_64":\s*"(\d+)"', response.text)
    revision = amd64_rev_number.group(1) if amd64_rev_number else None

    if snap_name and revision:
        result = [Snap(
            name=snap_name,
            revision=int(revision),
            push_channel="8.0/edge",
        )]
        return result
    else:
        raise ValueError("Required mysql-router snap variables not found in the file")


def fetch_postgresql_snaps(charm_revision) -> list[Snap]:
    """Fetch postgresql-operator snaps information."""
    response = requests.get(f"https://raw.githubusercontent.com/canonical/postgresql-operator/refs/tags/rev{charm_revision}/src/constants.py")
    response.raise_for_status()

    snap_list = fetch_var_from_py_file(response.text, "SNAP_PACKAGES", False)

    if snap_list:
        result = []
        for snap_name, snap_info in snap_list:
            result.append(Snap(
                name=snap_name,
                revision=int(snap_info["revision"]["x86_64"]),
                push_channel="14/edge",
            ))
        return result
    else:
        raise ValueError("Required postgresql-operator snap variables not found in the file")


def fetch_pgbouncer_snaps(charm_revision) -> list[Snap]:
    """Fetch pgbouncer-operator snaps information."""
    response = requests.get(f"https://raw.githubusercontent.com/canonical/pgbouncer-operator/refs/tags/rev{charm_revision}/src/constants.py")
    response.raise_for_status()

    snap_list = fetch_var_from_py_file(response.text, "SNAP_PACKAGES", False)

    if snap_list:
        result = []
        for snap_name, snap_info in snap_list:
            result.append(Snap(
                name=snap_name,
                revision=int(snap_info["revision"]["x86_64"]),
                push_channel="1/edge",
            ))
        return result
    else:
        raise ValueError("Required pgbouncer-operator snap variables not found in the file")


def fetch_ubuntu_advantage_snaps() -> list[Snap]:
    """Return canonical-livepatch latest revision in default channel (the way the charm deploys it)"""
    response = requests.get("https://api.snapcraft.io/v2/snaps/info/canonical-livepatch", headers = {'Snap-Device-Series': '16'})
    response.raise_for_status()
    default_channel = response.json()["channel-map"][0]
    snap = [Snap(
        name="canonical-livepatch",
        revision=int(default_channel['revision']),
        push_channel=f"{default_channel['channel']['track']}/{default_channel['channel']['risk']}",
    )]
    return snap


SNAP_FETCHERS_BY_CHARM = {
    "grafana-agent": fetch_grafana_snaps,
    "pgbouncer": fetch_pgbouncer_snaps,
    "postgresql": fetch_postgresql_snaps,
    "mysql": fetch_mysql_snaps,
    "mysql-router": fetch_mysql_router_snaps,
    "ubuntu-advantage": fetch_ubuntu_advantage_snaps,
}
SNAPS_YAML_PATH = "releases/latest/snaps.yaml"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle_file_path",  type=str)

    bundle_file_path = pathlib.Path(parser.parse_args().bundle_file_path)
    old_bundle_data = yaml.safe_load(bundle_file_path.read_text())
    bundle_data = copy.deepcopy(old_bundle_data)
    bundle_snaps = set()
    bundle_oci_resources = {}
    updates_available = False

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
                response = requests.get(resource["download"]["url"])
                response.raise_for_status()
                resource_data = response.json()

                app.setdefault("resources", {})
                app["resources"][resource["name"]] = int(resource["revision"])

                # Will be added separately, as comments to yaml file
                bundle_oci_resources[resource["name"]] = {
                    "revision": int(resource["revision"]),
                    "oci-image": f"docker://{resource_data['ImageName']}",
                    "oci-username": resource_data["Username"],
                    "oci-password": resource_data["Password"],
                }
        if app["charm"] in SNAP_FETCHERS_BY_CHARM:
            fetcher_func = SNAP_FETCHERS_BY_CHARM[app["charm"]]
            if app["charm"] == "ubuntu-advantage":
                snaps = fetcher_func()
            else:
                snaps = fetcher_func(app["revision"])
            bundle_snaps.update(snaps)

    if old_bundle_data != bundle_data:
        updates_available = True
        with open(bundle_file_path, "w") as file:
            yaml_string = yaml.dump(bundle_data)
            for oci_resource_name, oci_resource_data in bundle_oci_resources.items():
                comment = (
                    f"        # oci-image: {oci_resource_data['oci-image']}\n"
                    f"        # oci-password: {oci_resource_data['oci-password']}\n"
                    f"        # oci-username: {oci_resource_data['oci-username']}"
                )
                # Find where to insert the comment
                insertion_point = f"{oci_resource_name}: {oci_resource_data['revision']}"
                yaml_string = yaml_string.replace(insertion_point, f"{insertion_point}\n{comment}")
            file.write(yaml_string)

    if len(bundle_snaps) > 0:
        snaps_data = {"packages": [dataclasses.asdict(snap) for snap in sorted(bundle_snaps)]}
        try:
            old_snaps_data = yaml.safe_load(pathlib.Path(SNAPS_YAML_PATH).read_text())
        except FileNotFoundError:
            old_snaps_data = {}

        if old_snaps_data != snaps_data:
            updates_available = True
            with open(SNAPS_YAML_PATH, "w") as file:
                yaml.dump(snaps_data, file)

    github_actions.output["updates_available"] = json.dumps(updates_available)
