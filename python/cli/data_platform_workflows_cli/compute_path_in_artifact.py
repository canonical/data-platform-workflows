import argparse
import pathlib
from . import github_actions


def main():
    """Replace "/" characters in path

    "/" not valid in GitHub Actions artifact name
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    args = parser.parse_args()
    # Normalize path
    path = str(pathlib.PurePath(args.path))

    path = path.replace("/", "-")
    github_actions.output["path"] = path
