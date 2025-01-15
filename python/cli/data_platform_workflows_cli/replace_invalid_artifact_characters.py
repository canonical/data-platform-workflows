import argparse
from . import github_actions


def main():
    """Replace characters in string that are not valid in GitHub Actions artifact name

    https://github.com/actions/upload-artifact/issues/22
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("string")
    args = parser.parse_args()
    string = args.string
    for character in '\\/":<>|*?':
        string.replace(character, "-")
    github_actions.output["artifact_string"] = string
