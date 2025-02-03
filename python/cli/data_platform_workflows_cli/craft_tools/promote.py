import argparse
import enum
import logging
import pathlib
import subprocess
import sys

import requests
import yaml

logging.basicConfig(level=logging.INFO, stream=sys.stdout)


class Direction(enum.StrEnum):
    FROM = "from"
    TO = "to"


class Risk(enum.StrEnum):
    """Charmhub risk"""

    # In order from lowest to highest risk
    STABLE = "stable"
    CANDIDATE = "candidate"
    BETA = "beta"
    EDGE = "edge"

    @classmethod
    def get(cls, value, *, direction: Direction):  # Cannot override __call__ or __new__
        valid_risks = [risk.value for risk in cls]
        if direction is Direction.FROM:
            valid_risks.remove(Risk.STABLE.value)
        elif direction is Direction.TO:
            valid_risks.remove(Risk.EDGE.value)
        else:
            raise TypeError
        if value not in valid_risks:
            raise ValueError(
                f"`{direction.value}-risk` input must be one of {repr(valid_risks)}, got: "
                f"{repr(value)}"
            )
        return cls(value)

    def __lt__(self, other):
        if not isinstance(other, Risk):
            # Raise instead of `return NotImplemented` since this class inherits from `str`
            raise TypeError
        order = list(Risk)
        return order.index(self) < order.index(other)


def get_commit_sha_and_revisions(*, channel: str, charm_name: str, tag_prefix: str):
    """Get (& verify) commit sha that all charm revisions on a Charmhub channel were built from

    Returns (commit sha, charm revisions)
    """
    logging.info(f"Getting revisions on {repr(channel)}")
    response = requests.get(
        f"https://api.snapcraft.io/v2/charms/info/{charm_name}?fields=channel-map&channel={channel}"
    )
    response.raise_for_status()
    channel_map = response.json()["channel-map"]
    revisions: list[int] = [item["revision"]["revision"] for item in channel_map]
    if not revisions:
        raise ValueError(f"No revisions exist on {repr(channel)}")
    logging.info(f"Revisions on {repr(channel)}: {repr(revisions)}")

    logging.info("Checking that revisions were built from the same git commit")
    commit_shas = set()
    for revision in revisions:
        tag = f"{tag_prefix}{revision}"
        try:
            commit_shas.add(
                subprocess.run(
                    ["git", "rev-parse", tag], capture_output=True, check=True, text=True
                ).stdout.strip()
            )
        except subprocess.CalledProcessError:
            logging.error(
                f"Unable to find git tag {repr(tag)}. Was revision {revision} released with "
                "data-platform-workflows release_charm.yaml?"
            )
            raise
    if len(commit_shas) != 1:
        raise ValueError(
            f"Revisions {repr(revisions)} were built from different git commits: "
            f"{repr(commit_shas)}. Revisions must be built from the same git commit to correctly "
            "apply git tags for risk (e.g. '14/beta')"
        )
    commit_sha = commit_shas.pop()
    logging.info(f"All revisions on {repr(channel)} were built from git commit {repr(commit_sha)}")
    return commit_sha, revisions


def charm():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", required=True)
    parser.add_argument("--track", required=True)
    parser.add_argument("--from-risk", required=True)
    parser.add_argument("--to-risk", required=True)
    parser.add_argument("--ref", required=True)
    args = parser.parse_args()
    directory = pathlib.Path(args.directory)

    metadata_file = yaml.safe_load((directory / "metadata.yaml").read_text())
    charm_name = metadata_file["name"]
    charm_display_name = metadata_file["display-name"]

    track = args.track
    if "/" in track:
        raise ValueError(f"`track` input cannot contain '/' character: {repr(track)}")
    from_risk = Risk.get(args.from_risk, direction=Direction.FROM)
    to_risk = Risk.get(args.to_risk, direction=Direction.TO)
    if not to_risk < from_risk:
        raise ValueError(
            f"`to-risk` input ({repr(to_risk.value)}) must be lower risk than `from-risk` input "
            f"({repr(from_risk.value)})"
        )
    if to_risk is Risk.STABLE and from_risk is not Risk.CANDIDATE:
        raise ValueError(
            "Only the 'candidate' risk can be promoted to 'stable'. Promote "
            f"{repr(from_risk.value)} to 'candidate' first"
        )

    if not args.ref.startswith("refs/heads/"):
        raise ValueError(
            f"This workflow must be run on `workflow_dispatch` from the branch that contains track {repr(track)}"
        )
    target_branch = args.ref.removeprefix("refs/heads/")

    if not pathlib.Path(".github/release.yaml").exists():
        raise FileNotFoundError(
            "Repository must contain `.github/release.yaml` to automatically generate release "
            "notes in the correct format. See "
            "https://github.com/canonical/data-platform-workflows/blob/main/.github/workflows/promote_charm.md#step-3-add-githubreleaseyaml-file"
        )

    from_channel = f"{track}/{from_risk}"
    to_channel = f"{track}/{to_risk}"

    # `tag_prefix` format from release_charm.yaml
    if directory == pathlib.Path("."):
        tag_prefix = "rev"
    else:
        tag_prefix = f"{charm_name}/rev"

    logging.info("Checking that revisions that will be promoted are from the same git commit")
    # Check before promoting so that we fail early if `from_channel` revisions were built from
    # different git commits.
    # But don't store return value to avoid race condition if `from_channel` changes before
    # `charmcraft promote` is run. Instead, get commit sha again from `to_channel` after promoting
    get_commit_sha_and_revisions(channel=from_channel, charm_name=charm_name, tag_prefix=tag_prefix)

    logging.info(
        f"Promoting {repr(charm_name)} charm from {repr(from_channel)} to {repr(to_channel)}"
    )
    subprocess.run(
        [
            "charmcraft",
            "promote",
            "--name",
            charm_name,
            "--from-channel",
            from_channel,
            "--to-channel",
            to_channel,
            "--yes",
        ],
        check=True,
    )

    logging.info("Getting git commit of revisions that were promoted")
    promoted_commit_sha, charm_revisions = get_commit_sha_and_revisions(
        channel=to_channel, charm_name=charm_name, tag_prefix=tag_prefix
    )

    logging.info(f"Updating git tag {repr(to_channel)}")
    subprocess.run(["git", "tag", to_channel, promoted_commit_sha, "--force"], check=True)
    subprocess.run(["git", "push", "origin", to_channel, "--force"], check=True)

    github_release_tag = f"{tag_prefix}{max(charm_revisions)}"
    if to_risk is Risk.CANDIDATE:
        if len(charm_revisions) > 1:
            title = f"Revisions {', '.join(str(revision) for revision in charm_revisions)}"
        else:
            title = f"Revision {charm_revisions[0]}"
        subprocess.run(
            [
                "gh",
                "release",
                "create",
                github_release_tag,
                "--verify-tag",
                "--draft",
                "--generate-notes",
                # TODO: remove when charm refresh versioning implemented?
                # If `--draft` is passed, `--latest` appears to have no affect on release editing
                # in GitHub's UI (the UI will set latest by default regardless)
                "--latest=false",
                "--target",
                target_branch,
                "--title",
                title,
                "--notes",
                # Say "/stable" in release notes so that it's correct when the release is published
                f"""A new revision of {charm_display_name} has been published in the {track}/stable channel on [Charmhub](https://charmhub.io/{charm_name}).""",
            ],
            check=True,
        )
    elif to_risk is Risk.STABLE:
        # Publish GitHub release draft created during promotion to candidate risk
        subprocess.run(
            ["gh", "release", "edit", github_release_tag, "--verify-tag", "--draft=false"],
            check=True,
        )
