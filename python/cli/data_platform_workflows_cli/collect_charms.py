# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
"""Collect charms to build from charmcraft.yaml file(s)"""

import json
import logging
import os
import pathlib
import sys

import yaml


def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    charms = []
    for charmcraft_yaml in pathlib.Path(".").glob("**/charmcraft.yaml"):
        yaml_data = yaml.safe_load(charmcraft_yaml.read_text())
        if (type_ := yaml_data["type"]) != "charm":
            logging.info(f'{charmcraft_yaml} is {type_=} instead of "charm", skipping')
            continue
        path = charmcraft_yaml.parent
        charm_name = yaml.safe_load((path / "metadata.yaml").read_text())["name"]
        for bases_index, _ in enumerate(yaml_data["bases"]):
            charms.append(
                {
                    "job_display_name": f"Build {charm_name} charm | base #{bases_index}",
                    "bases_index": bases_index,
                    "directory_path": str(path),
                }
            )
    logging.info(f"Collected {charms=}")
    with open(os.environ["GITHUB_OUTPUT"], "a") as file:
        file.write(f"charms={json.dumps(charms)}")
