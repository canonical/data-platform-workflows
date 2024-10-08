# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
"""Collect bases to build

charmcraft: "bases"
snapcraft: "architectures"
rockcraft: "platforms"

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

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
RUNNERS = {
    craft.Architecture.X64: "ubuntu-latest",
    craft.Architecture.ARM64: "Ubuntu_ARM64_4C_16G_02",
}


def get_bases(*, craft_: craft.Craft, yaml_data):
    """Get architecture for each base

    For charms, multiple bases can have the same architecture
    (e.g. Ubuntu 20.04 X64 and Ubuntu 22.04 X64)

    For snaps & rocks, the Ubuntu version is the same for all architectures.
    """
    if craft_ is craft.Craft.ROCK:
        # https://canonical-rockcraft.readthedocs-hosted.com/en/latest/reference/rockcraft.yaml/#platforms
        return [craft.Architecture(arch) for arch in yaml_data["platforms"]]
    if craft_ is craft.Craft.SNAP:
        bases = yaml_data.get("architectures")
        if not bases:
            # Default to X64
            return [craft.Architecture.X64]
    elif craft_ is craft.Craft.CHARM:
        bases = yaml_data["bases"]
    else:
        raise ValueError
    arch_for_bases = []
    for platform in bases:
        if craft_ is craft.Craft.SNAP:
            # https://snapcraft.io/docs/explanation-architectures
            build_on_architectures = platform["build-on"]
        elif craft_ is craft.Craft.CHARM:
            # https://discourse.charmhub.io/t/charmcraft-bases-provider-support/4713
            build_on = platform.get("build-on")
            if build_on:
                assert isinstance(build_on, list) and len(build_on) == 1
                platform = build_on[0]
            build_on_architectures = platform.get("architectures")
            if not build_on_architectures:
                # Default to X64
                arch_for_bases.append(craft.Architecture.X64)
                continue
        else:
            raise ValueError
        assert (
            len(build_on_architectures) == 1
        ), f"Multiple architectures ({build_on_architectures}) in one ({craft_.value}craft.yaml) base/architecture entry not supported. Use one entry per architecture"
        arch_for_bases.append(craft.Architecture(build_on_architectures[0]))
    return arch_for_bases


def collect(craft_: craft.Craft):
    """Collect bases to build from *craft.yaml"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", required=True)
    if craft_ is craft.Craft.CHARM:
        parser.add_argument("--cache", required=True)
    args = parser.parse_args()
    craft_file = pathlib.Path(args.directory, f"{craft_.value}craft.yaml")
    if craft_ is craft.Craft.SNAP:
        craft_file = craft_file.parent / "snap" / craft_file.name
    yaml_data = yaml.safe_load(craft_file.read_text())
    bases_ = get_bases(craft_=craft_, yaml_data=yaml_data)
    bases = []
    for index, architecture in enumerate(bases_):
        # id used to select base in `*craft pack`
        if craft_ is craft.Craft.CHARM:
            id_ = index
        else:
            id_ = architecture.value
        bases.append({"id": id_, "runner": RUNNERS[architecture]})
    github_actions.output["bases"] = json.dumps(bases)
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
