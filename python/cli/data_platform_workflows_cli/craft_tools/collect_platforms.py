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
    craft.Architecture.ARM64: "Ubuntu_ARM64_4C_16G_02",
}


def collect(craft_: craft.Craft):
    """Collect platforms to build from *craft.yaml"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", required=True)
    if craft_ is craft.Craft.CHARM:
        parser.add_argument("--cache", required=True)
    args = parser.parse_args()
    craft_file = pathlib.Path(args.directory, f"{craft_.value}craft.yaml")
    if craft_ is craft.Craft.SNAP:
        craft_file = craft_file.parent / "snap" / craft_file.name
    yaml_data = yaml.safe_load(craft_file.read_text())
    platforms = []
    if craft_ is craft.Craft.CHARM:
        for platform in charmcraft_platforms.get(craft_file):
            # Example `platform`: "ubuntu@22.04:amd64"
            platforms.append(
                {
                    "name": platform,
                    "runner": RUNNERS[platform.architecture],
                    "name_in_artifact": platform.replace(":", "-"),
                }
            )
    elif craft_ is craft.Craft.ROCK:
        for platform in yaml_data["platforms"]:
            # Example `platform`: "amd64"
            architecture = craft.Architecture(platform)
            platforms.append({"name": platform, "runner": RUNNERS[architecture]})
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
                architecture = craft.Architecture(platform)
                platforms.append({"name": platform, "runner": RUNNERS[architecture]})
        elif yaml_data["base"] == "core22":
            for entry in yaml_data["architectures"]:
                # Example: "amd64"
                platform = entry["build-on"]
                architecture = craft.Architecture(platform)
                platforms.append({"name": platform, "runner": RUNNERS[architecture]})
        else:
            raise ValueError(f'Unsupported snapcraft.yaml base: {repr(yaml_data["base"])}')
    else:
        raise ValueError
    github_actions.output["platforms"] = json.dumps(platforms)
    default_prefix = f'packed-{craft_.value}-{args.directory.replace("/", "-")}'
    if craft_ is craft.Craft.CHARM:
        default_prefix = f'packed-{craft_.value}-cache-{args.cache}-{args.directory.replace("/", "-")}'
    github_actions.output["default_prefix"] = default_prefix


def snap():
    collect(craft.Craft.SNAP)


def rock():
    collect(craft.Craft.ROCK)


def charm():
    collect(craft.Craft.CHARM)
