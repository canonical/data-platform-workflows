# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
"""Collect ST124 shorthand notation platforms to build from charmcraft.yaml

TODO add ST124 support for snaps & rocks
"""

import argparse
import json
import logging
import pathlib
import sys

import yaml

from .. import github_actions
from . import craft

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
    if craft_ is craft.Craft.CHARM:
        # todo: run ccst124 validate
        platforms = []
        for platform in yaml_data["platforms"]:
            # Example `platform`: "ubuntu@22.04:amd64"
            architecture = craft.Architecture(platform.split(":")[-1])
            platforms.append(
                {
                    "name": platform,
                    "runner": RUNNERS[architecture],
                    "name_in_artifact": platform.replace(":", "-"),
                }
            )
        github_actions.output["platforms"] = json.dumps(platforms)
    else:
        raise ValueError("ST124 syntax not yet supported for snaps or rocks")
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
