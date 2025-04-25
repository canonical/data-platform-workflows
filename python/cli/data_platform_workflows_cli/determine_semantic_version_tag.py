import dataclasses
import os
import re
import subprocess

from . import check_semantic_version_prefix


def main():
    # Get last release tag
    try:
        last_tag = subprocess.run(
            # Include "." in match so that we don't match major version tags (e.g. "v1") commonly
            # used in GitHub Actions
            ["git", "describe", "--abbrev=0", "--match", "v[0-9]*.*"],
            capture_output=True,
            check=True,
            text=True,
        ).stdout.strip()
    except subprocess.CalledProcessError as e:
        if "no names found" or "no annotated tags can describe" in e.stderr.lower():
            raise Exception(
                "Unable to find previous annotated git tag. If this repository is using the "
                "`release_python_package.yaml` workflow for the first time, see the instructions "
                "in `release_python_package.md` to create the initial git tag.\n\n"
                f"stderr:\n{e.stderr}"
            )
        print(f"{e.stderr=}")
        raise

    # Get commit prefixes since last release tag
    commit_subjects = subprocess.run(
        ["git", "log", f"{last_tag}..HEAD", "--pretty=format:%s"],
        capture_output=True,
        check=True,
        text=True,
    ).stdout.splitlines()
    assert len(commit_subjects) > 0
    prefixes = set()
    for subject in commit_subjects:
        prefixes.add(check_semantic_version_prefix.check(subject))

    @dataclasses.dataclass(frozen=True)
    class SemanticVersion:
        major: int
        minor: int
        patch: int

        @classmethod
        def from_tag(cls, tag: str, /):
            # Regular expression extracted from
            # https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string
            match = re.fullmatch(
                r"v(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)", tag
            )
            if not match:
                raise ValueError
            return cls(**{name: int(value) for name, value in match.groupdict().items()})

        def to_tag(self) -> str:
            return f"v{self.major}.{self.minor}.{self.patch}"

    try:
        last_version = SemanticVersion.from_tag(last_tag)
    except ValueError:
        raise ValueError(f"Last release tag is not a valid semantic version: {repr(last_tag)}")

    # Determine new version based on commit prefixes
    if "breaking" in prefixes and last_version.major > 0:
        new_version = SemanticVersion(last_version.major + 1, 0, 0)
    elif "breaking" in prefixes or "compatible" in prefixes:
        new_version = SemanticVersion(last_version.major, last_version.minor + 1, 0)
    elif "patch" in prefixes:
        new_version = SemanticVersion(
            last_version.major, last_version.minor, last_version.patch + 1
        )
    else:
        raise ValueError

    output = f"tag={new_version.to_tag()}\nmajor_version_tag=v{new_version.major}"
    print(output)
    with open(os.environ["GITHUB_OUTPUT"], "a") as file:
        file.write(output)
