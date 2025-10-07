# Copied from https://github.com/canonical/charmcraftcache/blob/main/charmcraftcache/_platforms.py
import pathlib

import yaml

_SYNTAX_DOCS = "https://github.com/canonical/data-platform-workflows/blob/main/.github/workflows/build_charm.md#required-charmcraftyaml-syntax"


class Platform(str):
    """Platform in charmcraft.yaml 'platforms' (e.g. 'ubuntu@22.04:amd64')"""

    def __new__(cls, value: str, /):
        try:
            _, architecture = value.split(":")
        except ValueError:
            raise ValueError(
                "Invalid ST124 shorthand notation in charmcraft.yaml 'platforms': "
                f"{repr(value)}\n\nMore info: {_SYNTAX_DOCS}"
            )
        instance: Platform = super().__new__(cls, value)
        instance.architecture = architecture
        return instance


def get(charmcraft_yaml: pathlib.Path, /):
    """Get platforms from charmcraft.yaml"""
    charmcraft_yaml_data = yaml.safe_load(charmcraft_yaml.read_text())
    for key in ("base", "bases"):
        if key in charmcraft_yaml_data:
            raise ValueError(
                f"'{key}' key in charmcraft.yaml not supported. Use 'platforms' key instead.\n\n"
                f"More info: {_SYNTAX_DOCS}"
            )
    yaml_platforms = charmcraft_yaml_data.get("platforms")
    if not yaml_platforms:
        raise ValueError(
            f"'platforms' key in charmcraft.yaml required\n\nMore info: {_SYNTAX_DOCS}"
        )
    if not isinstance(yaml_platforms, dict):
        raise TypeError(
            "Expected charmcraft.yaml 'platforms' with type 'dict', got "
            f"{repr(type(yaml_platforms).__name__)}: {repr(yaml_platforms)}\n\n"
            f"More info: {_SYNTAX_DOCS}"
        )
    for value in yaml_platforms.values():
        if value is not None:
            raise ValueError(
                "Shorthand notation required ('build-on' and 'build-for' not supported) in "
                f"charmcraft.yaml 'platforms'.\n\nMore info: {_SYNTAX_DOCS}"
            )
    # Validate format of keys in `yaml_platforms`
    platforms = [Platform(platform) for platform in yaml_platforms]

    return platforms
