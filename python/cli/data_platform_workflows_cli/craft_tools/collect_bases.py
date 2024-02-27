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
import enum
import json
import logging
import os
import pathlib
import sys

import yaml

from . import craft

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
RUNNERS = {
    craft.Architecture.X64: "ubuntu-latest",
    craft.Architecture.ARM64: [
        "self-hosted",
        "data-platform",
        "ubuntu",
        "ARM64",
        "4cpu16ram",
    ],
}


class Craft(str, enum.Enum):
    SNAP = "snap"
    ROCK = "rock"
    CHARM = "charm"


def get_bases(*, craft_: Craft, yaml_data):
    """Get architecture for each base

    For charms, multiple bases can have the same architecture
    (e.g. Ubuntu 20.04 X64 and Ubuntu 22.04 X64)

    For snaps & rocks, the Ubuntu version is the same for all architectures.
    """
    if craft_ is Craft.ROCK:
        # https://canonical-rockcraft.readthedocs-hosted.com/en/latest/reference/rockcraft.yaml/#platforms
        return [craft.Architecture(arch) for arch in yaml_data["platforms"]]
    if craft_ is Craft.SNAP:
        bases = yaml_data.get("architectures")
        if not bases:
            # Default to X64
            return [craft.Architecture.X64]
    elif craft_ is Craft.CHARM:
        bases = yaml_data["bases"]
    else:
        raise ValueError
    arch_for_bases = []
    for platform in bases:
        if craft_ is Craft.SNAP:
            # https://snapcraft.io/docs/explanation-architectures
            build_on_architectures = platform["build-on"]
        elif craft_ is Craft.CHARM:
            # https://discourse.charmhub.io/t/charmcraft-bases-provider-support/4713
            build_on_architectures = (platform.get("build-on") or platform).get(
                "architectures"
            )
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


def collect(craft_: Craft):
    """Collect bases to build from *craft.yaml"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", required=True)
    if craft_ is Craft.CHARM:
        parser.add_argument("--cache", required=True)
    args = parser.parse_args()
    craft_file = pathlib.Path(args.directory, f"{craft_.value}craft.yaml")
    if craft_ is Craft.SNAP:
        craft_file = craft_file.parent / "snap" / craft_file.name
    yaml_data = yaml.safe_load(craft_file.read_text())
    bases_ = get_bases(craft_=craft_, yaml_data=yaml_data)
    bases = [
        {"index": index, "runner": RUNNERS[architecture]}
        for index, architecture in enumerate(bases_)
    ]
    logging.info(f"Collected {bases=}")
    default_prefix = f'packed-{craft_.value}-{args.directory.replace("/", "-")}'
    if craft_ is Craft.CHARM:
        default_prefix = f'packed-{craft_.value}-cache-{args.cache}-{args.directory.replace("/", "-")}'
    logging.info(f"{default_prefix=}")
    with open(os.environ["GITHUB_OUTPUT"], "a") as file:
        file.write(f"bases={json.dumps(bases)}\ndefault_prefix={default_prefix}")


def snap():
    collect(Craft.SNAP)


def rock():
    collect(Craft.ROCK)


def charm():
    collect(Craft.CHARM)
