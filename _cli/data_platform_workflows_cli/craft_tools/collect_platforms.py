# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
"""Collect platforms to build

charmcraft: Only ST124 shorthand notation `platforms` are supported
snapcraft: (ST124 not supported) core22 `architectures` and core24 shorthand `platforms` supported
rockcraft: (ST124 not supported) shorthand `platforms` supported

snaps & rocks are usually built on multiple architectures but only one Ubuntu version/base
charms (subordinate) can be built on multiple Ubuntu versions
"""

import argparse
import json
import logging
import pathlib
import sys

import yaml

from .. import github_actions
from . import craft
from . import charmcraft_platforms

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
RUNNERS = {
    craft.Architecture.X64: "ubuntu-latest",
    craft.Architecture.ARM64: "ubuntu-24.04-arm",
    # Use PS6 runners while PS7 runners unstable: https://chat.canonical.com/canonical/pl/3wcxtsrzo3ykdxe6rzp5uuus8h
    craft.Architecture.S390X: "self-hosted-linux-s390x-noble-edge",
}


def collect(craft_: craft.Craft):
    """Collect platforms to build from *craft.yaml"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", required=True)
    args = parser.parse_args()
    craft_file = pathlib.Path(args.directory, f"{craft_.value}craft.yaml")
    if craft_ is craft.Craft.SNAP:
        craft_file = craft_file.parent / "snap" / craft_file.name
    yaml_data = yaml.safe_load(craft_file.read_text())
    platforms = []
    if craft_ is craft.Craft.CHARM:
        for platform in charmcraft_platforms.get(craft_file):
            try:
                runner = RUNNERS[platform.architecture]
            except KeyError:
                print(
                    f"::warning::Skipped {repr(platform)} platform since the "
                    f"{repr(platform.architecture)} architecture is not currently supported by "
                    "build_charm.yaml. Please open an issue if you'd like this architecture to be "
                    "supported"
                )
                continue
            # Example `platform`: "ubuntu@22.04:amd64"
            platforms.append(
                {
                    "name": platform,
                    "runner": runner,
                    "name_in_artifact": platform.replace(":", "-"),
                }
            )
    elif craft_ is craft.Craft.ROCK:
        for platform in yaml_data["platforms"]:
            # Example `platform`: "amd64"
            try:
                architecture = craft.Architecture(platform)
                runner = RUNNERS[architecture]
            except (ValueError, KeyError):
                print(
                    f"::warning::Skipped {repr(platform)} architecture since it is not currently "
                    "supported by build_rock.yaml. Please open an issue if you'd like this "
                    "architecture to be supported"
                )
                continue
            platforms.append({"name": platform, "runner": runner})
    elif craft_ is craft.Craft.SNAP:
        if yaml_data["base"] == "core24":
            platforms_ = yaml_data["platforms"]
            if not isinstance(platforms_, dict):
                raise TypeError("Expected type 'dict' for snapcraft.yaml 'platforms'")
            for value in platforms_.values():
                if value is not None:
                    raise ValueError(
                        "Only shorthand notation supported in snapcraft.yaml 'platforms'. "
                        "'build-on' and 'build-for' not supported"
                    )
            for platform in platforms_:
                # Example `platform`: "amd64"
                try:
                    architecture = craft.Architecture(platform)
                    runner = RUNNERS[architecture]
                except (ValueError, KeyError):
                    print(
                        f"::warning::Skipped {repr(platform)} architecture since it is not "
                        "currently supported by build_snap.yaml. Please open an issue if you'd "
                        "like this architecture to be supported"
                    )
                    continue
                platforms.append({"name": platform, "runner": runner})
        elif yaml_data["base"] == "core22":
            for entry in yaml_data["architectures"]:
                # Example: ["amd64"]
                platforms_ = entry["build-on"]
                if not (isinstance(platforms_, list) and len(platforms_) == 1):
                    raise ValueError(
                        "Expected snapcraft.yaml 'build-on' value with type 'list' and length 1, "
                        f"got: {repr(platforms_)}"
                    )
                # Example: "amd64"
                platform = platforms_[0]
                try:
                    architecture = craft.Architecture(platform)
                    runner = RUNNERS[architecture]
                except (ValueError, KeyError):
                    print(
                        f"::warning::Skipped {repr(platform)} architecture since it is not "
                        "currently supported by build_snap.yaml. Please open an issue if you'd "
                        "like this architecture to be supported"
                    )
                    continue
                platforms.append({"name": platform, "runner": runner})
        else:
            raise ValueError(f'Unsupported snapcraft.yaml base: {repr(yaml_data["base"])}')
    else:
        raise ValueError
    github_actions.output["platforms"] = json.dumps(platforms)


def snap():
    collect(craft.Craft.SNAP)


def rock():
    collect(craft.Craft.ROCK)


def charm():
    collect(craft.Craft.CHARM)
