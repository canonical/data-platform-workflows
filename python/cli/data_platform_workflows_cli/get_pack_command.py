import argparse
import json
import pathlib
import subprocess

from . import github_actions


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", required=True)
    parser.add_argument("--charm-directory", required=True)
    parser.add_argument("--bases-index", required=True)
    args = parser.parse_args()
    # Do not use tox env unless charmcraft.yaml in same directory as tox.ini
    # (e.g. if there's a charm in tests/integration, it should not be built using the tox wrapper)
    path = pathlib.Path(args.charm_directory)
    if (path / "tox.ini").exists():
        tox_environments = (
            subprocess.run(
                ["tox", "list", "--no-desc"],
                check=True,
                capture_output=True,
                cwd=path,
                encoding="utf-8",
            )
            .stdout.strip()
            .split("\n")
        )
    else:
        tox_environments = []
    cache = json.loads(args.cache)
    assert isinstance(cache, bool)
    if cache:
        if "build-dev" in tox_environments:
            command = f"tox run -e build-dev -- -v --bases-index='{args.bases_index}'"
        else:
            command = f"charmcraftcache pack -v --bases-index='{args.bases_index}'"
    else:
        if "build-production" in tox_environments:
            command = (
                f"tox run -e build-production -- -v --bases-index='{args.bases_index}'"
            )
        else:
            command = f"charmcraft pack -v --bases-index='{args.bases_index}'"
    github_actions.output["command"] = command
