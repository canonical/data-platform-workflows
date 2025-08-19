import argparse
import logging
import pathlib
import sys
import tomllib
import zipfile

logging.basicConfig(level=logging.INFO, stream=sys.stdout)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", required=True)
    args = parser.parse_args()
    directory = pathlib.Path(args.directory)
    if not (directory / "refresh_versions.toml").exists():
        logging.info("refresh_versions.toml not found")
        return
    for charm_file in directory.glob("*.charm"):
        logging.info(f"Checking {charm_file.name}")
        with zipfile.ZipFile(charm_file, "r") as charm_zip:
            with zipfile.Path(charm_zip, "refresh_versions.toml").open("rb") as file:
                data = tomllib.load(file)
        charm_version = data.get("charm")
        if charm_version is None:
            raise ValueError(
                "Charm refresh compatibility version is missing from refresh_versions.toml. Docs: "
                "https://canonical-charm-refresh.readthedocs-hosted.com/latest/add-to-charm/charm-version/"
            )
        if not isinstance(charm_version, str):
            raise TypeError
        if charm_version.startswith("unknown/"):
            raise ValueError(
                "No charm refresh compatibility version git tags found during charm build. Docs: "
                "https://canonical-charm-refresh.readthedocs-hosted.com/latest/add-to-charm/charm-version/"
            )
        logging.info(
            f"Checked charm version in {charm_file.name} was built with access to charm refresh "
            "compatibility version git tags"
        )
