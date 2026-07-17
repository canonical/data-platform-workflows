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
    """Snapcraft risk"""

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
                f"`{direction.value}-risk` input must be one of {repr(valid_risks)}. "
                f"Got: {repr(value)}"
            )
        return cls(value)


def get_snap_revisions(channel_name: str, snap_name: str, tag_prefix: str, raise_missing: bool):
    """Get the current snap revisions in the target channel."""
    logging.info(f"Getting revisions on {repr(channel_name)}")
    response = requests.get(
        f"https://api.snapcraft.io/v2/snaps/info/{snap_name}",
        headers={"Snap-Device-Series": "16"},
        params={"fields": "revision"},
    )

    response.raise_for_status()
    channels = response.json()["channel-map"]
    revisions = []
    for channel in channels:
        if channel["channel"]["name"] == channel_name:
            revisions.append(channel["revision"])

    if not revisions and raise_missing:
        raise ValueError(f"No revisions exist on {repr(channel_name)}")

    logging.info(f"Revisions on {repr(channel_name)}: {repr(revisions)}")
    logging.info("Checking that revisions were built from the same git commit")
    commit_shas = set()

    for revision in revisions:
        tag = f"{tag_prefix}{revision}"
        try:
            process = subprocess.run(
                ["git", "rev-list", "-n", "1", tag],
                capture_output=True,
                check=True,
                text=True,
            )
        except subprocess.CalledProcessError:
            logging.error(f"Unable to find git tag {repr(tag)}.")
            raise
        else:
            commit_shas.add(process.stdout.strip())

    if len(commit_shas) != 1:
        raise ValueError(
            f"Revisions {repr(revisions)} were built from different commits: {repr(commit_shas)}. "
            "Revisions must be built from the same git commit to correctly apply git tags for risk"
        )

    commit_sha = commit_shas.pop()
    logging.info(f"All revisions on {repr(channel_name)} were built from commit {repr(commit_sha)}")
    return commit_sha, revisions


def snaps():
    parser = argparse.ArgumentParser()
    parser.add_argument("--track", required=True)
    parser.add_argument("--from-risk", required=True)
    parser.add_argument("--to-risk", required=True)
    parser.add_argument("--ref", required=True)
    parser.add_argument("--directory", required=True)
    parser.add_argument("--default-branch", required=True)
    args = parser.parse_args()

    directory = pathlib.Path(args.directory)
    default_branch = args.default_branch

    track = args.track
    if track == "":
        raise ValueError("`track` input must not be empty string")
    if "/" in track:
        raise ValueError("`track` input cannot contain '/' character")

    from_risk = Risk.get(args.from_risk, direction=Direction.FROM)
    to_risk = Risk.get(args.to_risk, direction=Direction.TO)
    if not to_risk < from_risk:
        raise ValueError(
            f"`to-risk` input ({repr(to_risk.value)}) must be lower risk than "
            f"`from-risk` input ({repr(from_risk.value)})"
        )
    if to_risk is Risk.STABLE and from_risk is not Risk.CANDIDATE:
        raise ValueError(
            "Only the 'candidate' risk can be promoted to 'stable'. "
            f"Promote {repr(from_risk.value)} to 'candidate' first"
        )

    ref = args.ref
    # Remove safety precaution just to validate it on CI.
    # if not ref.startswith("refs/heads/"):
    #     raise ValueError(
    #         "This workflow must be run on `workflow_dispatch` from the branch that contains track "
    #         f"{repr(track)}"
    #     )

    if not pathlib.Path(".github/release.yaml").exists():
        raise FileNotFoundError(
            "Repository must contain `.github/release.yaml` to automatically generate "
            "release notes in the correct format. "
            "See https://github.com/canonical/data-platform-workflows/blob/main/.github/workflows/_promote_snaps.md"
        )

    from_channel = f"{track}/{from_risk}"
    to_channel = f"{track}/{to_risk}"

    current_snap_metadata = yaml.safe_load((directory / "snapcraft.yaml").read_text())
    current_snap_name = current_snap_metadata["name"]

    if directory in (pathlib.Path("."), pathlib.Path("snap")):
        tag_prefix = "rev"
    else:
        tag_prefix = f"{current_snap_name}/rev"

    logging.info("Checking that revisions that will be promoted are from the same commit")
    commit_sha, _ = get_snap_revisions(from_channel, current_snap_name, tag_prefix, True)

    subprocess.run(["git", "checkout", commit_sha], check=True)

    commit_snap_metadata = yaml.safe_load((directory / "snapcraft.yaml").read_text())
    commit_snap_name = commit_snap_metadata["name"]
    if commit_snap_name != current_snap_name:
        raise ValueError(
            "Snap name in snapcraft.yaml changed between latest commit on branch "
            f"({current_snap_name}) and commit on {from_channel} "
            f"({commit_snap_name}). Unable to promote charm"
        )

    subprocess.run(["git", "checkout", "-"], check=True)

    logging.info(f"Promoting {current_snap_name} snap")
    subprocess.run(
        [
            "snapcraft",
            "promote",
            current_snap_name,
            f"--from-channel={from_channel}",
            f"--to-channel={to_channel}",
            "--yes",
        ],
        check=True,
    )

    logging.info("Getting the revisions that were promoted")
    _, promoted_revisions = get_snap_revisions(to_channel, current_snap_name, tag_prefix, True)

    # Pick alphabetically first tag because of
    # https://github.com/orgs/community/discussions/149281#discussioncomment-12071170
    promoted_possible_release_tags = [f"{tag_prefix}{revision}" for revision in promoted_revisions]
    promoted_github_release_tag = sorted(promoted_possible_release_tags)[0]

    if to_risk is Risk.CANDIDATE:
        stable_channel = f"{track}/{Risk.STABLE.value}"

        logging.info(f"Getting the revisions for the {stable_channel} release")
        _, stable_revisions = get_snap_revisions(stable_channel, current_snap_name, tag_prefix, False)
        if not stable_revisions:
            logging.warning(f"No existing release found on {stable_channel}")
            stable_github_release_tag = None
        else:
            # Pick alphabetically first tag because of
            # https://github.com/orgs/community/discussions/149281#discussioncomment-12071170
            stable_possible_release_tags = [f"{tag_prefix}{revision}" for revision in stable_revisions]
            stable_github_release_tag = sorted(stable_possible_release_tags)[0]

        title = f"Revisions {', '.join(str(revision) for revision in sorted(promoted_revisions))}"
        notes = f"Revision for the {current_snap_name} snap have been published to the {stable_channel} channel"
        command = [
            "gh",
            "release",
            "create",
            promoted_github_release_tag,
            "--verify-tag",
            "--generate-notes",
            "--draft=true",
            "--latest=false",
            f"--title={title}",
            f"--notes={notes}",
        ]
        if stable_github_release_tag is not None:
            command.extend(("--notes-start-tag", stable_github_release_tag))
        logging.info("Creating GitHub draft release")
        subprocess.run(command, check=True)

    elif to_risk is Risk.STABLE:
        command = [
            "gh",
            "release",
            "edit",
            promoted_github_release_tag,
            "--verify-tag",
            "--draft=false",
        ]
        if ref != f"refs/heads/{default_branch}":
            command.append("--latest=false")
        logging.info("Creating GitHub release")
        subprocess.run(command, check=True)
