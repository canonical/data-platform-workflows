# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
"""Collect charm bases to build from charmcraft.yaml"""

import argparse
import json
import logging
import os
import pathlib
import sys

import yaml

from . import charmcraft

RUNNERS = {
    charmcraft.Architecture.X64: "ubuntu-latest",
    charmcraft.Architecture.ARM64: [
        "self-hosted",
        "data-platform",
        "ubuntu",
        "ARM64",
        "4cpu16ram",
    ],
}


def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    parser = argparse.ArgumentParser()
    parser.add_argument("--charm-directory", required=True)
    parser.add_argument("--cache", required=True)
    args = parser.parse_args()
    yaml_data = yaml.safe_load(
        pathlib.Path(args.charm_directory, "charmcraft.yaml").read_text()
    )
    # GitHub runner for each base
    runners = []
    for base in yaml_data["bases"]:
        # Bases format: https://discourse.charmhub.io/t/charmcraft-bases-provider-support/4713
        architectures = (base.get("build-on") or base).get("architectures", ["amd64"])
        assert (
            len(architectures) == 1
        ), f"Multiple architectures ({architectures}) in one (charmcraft.yaml) base not supported. Use one base per architecture"
        architecture = charmcraft.Architecture(architectures[0])
        runners.append(RUNNERS[architecture])
    bases = [{"index": index, "runner": runner} for index, runner in enumerate(runners)]
    logging.info(f"Collected {bases=}")
    default_prefix = (
        f'packed-charm-cache-{args.cache}-{args.charm_directory.replace("/", "-")}'
    )
    logging.info(f"{default_prefix=}")
    with open(os.environ["GITHUB_OUTPUT"], "a") as file:
        file.write(f"bases={json.dumps(bases)}\ndefault_prefix={default_prefix}")
