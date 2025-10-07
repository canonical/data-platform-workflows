import argparse
import dataclasses
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


@dataclasses.dataclass(frozen=True, kw_only=True)
class Charm:
    directory: pathlib.Path
    name: str
    display_name: str
    oci_resources: tuple[tuple[str, str]]  # Use instead of dict so that `Charm` is hashable

    @classmethod
    def from_directory(cls, directory: pathlib.Path, /):
        metadata = yaml.safe_load((directory / "metadata.yaml").read_text())
        # (Only for Kubernetes charms) get OCI resources
        oci_resources = {}
        for resource_name, resource in metadata.get("resources", {}).items():
            if resource["type"] != "oci-image":
                continue
            oci_hash = resource["upstream-source"]
            if "@sha256:" not in oci_hash:
                raise ValueError(
                    "Unable to promote charm that does not pin all of its `oci-image` resources "
                    f"to a sha256 digest in metadata.yaml: {repr(resource['upstream-source'])}"
                )
            oci_resources[resource_name] = oci_hash
        return cls(
            directory=directory,
            name=metadata["name"],
            display_name=metadata["display-name"],
            oci_resources=tuple(oci_resources.items()),
        )

    @property
    def tag_prefix(self):
        if self.directory == pathlib.Path("."):
            return "rev"
        else:
            return f"{self.name}/rev"


def get_commit_sha_and_release_title(*, channel: str, charms_: list[Charm], channel_missing_ok=False):
    """Get (& verify) commit sha that all charm revisions on a Charmhub channel name were built from

    Checks revisions across all Charmhub channels (each charm has a Charmhub channel) with name

    Returns (commit sha, GitHub release title)
    """
    logging.info(f"Getting revisions on {repr(channel)}")
    revisions: dict[Charm, list[int]] = {}
    for charm in charms_:
        # One-time exception to requirement that charms in monorepo have the same track—to enable
        # MySQL Router charms to use monorepo. (VM 8.0 track is managed by another team for
        # historical reasons.) Refresh compatibility tag will still use "dpe".
        if charm.name == "mysql-router-k8s" and channel.startswith("dpe/"):
            logging.warning(
                "Exception for mysql-router-k8s on track 'dpe': using track '8.0' instead for "
                "Charmhub operations"
            )
            charm_channel = channel.replace("dpe/", "8.0/")
        else:
            charm_channel = channel

        response = requests.get(
            f"https://api.snapcraft.io/v2/charms/info/{charm.name}?fields=channel-map&channel={charm_channel}"
        )
        response.raise_for_status()
        channel_map = response.json()["channel-map"]
        revisions[charm] = sorted(item["revision"]["revision"] for item in channel_map)
    logging.info(
        f"Revisions on {repr(channel)}: "
        f"{repr({charm.name: charm_revisions for charm, charm_revisions in revisions.items()})}"
    )
    if channel_missing_ok and all(not charm_revisions for charm_revisions in revisions.values()):
        logging.info(f"No revisions exist (for any charm) on {repr(channel)}")
        return None
    elif missing := next(
        (charm for charm, charm_revisions in revisions.items() if not charm_revisions), False
    ):
        raise ValueError(f"No {repr(missing.name)} revisions exist on {repr(channel)}")

    logging.info("Checking that revisions were built from the same git commit")
    commit_shas = set()
    for charm, charm_revisions in revisions.items():
        for revision in charm_revisions:
            tag = f"{charm.tag_prefix}{revision}"
            try:
                commit_shas.add(
                    subprocess.run(
                        ["git", "rev-list", "-n", "1", tag],
                        capture_output=True,
                        check=True,
                        text=True,
                    ).stdout.strip()
                )
            except subprocess.CalledProcessError:
                logging.error(
                    f"Unable to find git tag {repr(tag)}. Was {repr(charm.name)} revision "
                    f"{revision} released with data-platform-workflows release_charm_edge.yaml?"
                )
                raise
    if len(commit_shas) != 1:
        raise ValueError(
            "Revisions "
            f"{repr({charm.name: charm_revisions for charm, charm_revisions in revisions.items()})} "
            "were built from different git commits: "
            f"{repr(commit_shas)}. Revisions must be built from the same git commit to correctly "
            "apply git tags for risk (e.g. '14/beta')"
        )
    commit_sha = commit_shas.pop()
    logging.info(f"All revisions on {repr(channel)} were built from git commit {repr(commit_sha)}")

    # Determine release title
    if len(charms_) == 1:
        charm_revisions = revisions[charms_[0]]
        if len(charm_revisions) == 1:
            release_title = f"Revision {charm_revisions[0]}"
        else:
            release_title = f"Revisions {', '.join(str(revision) for revision in charm_revisions)}"
    else:
        charm_names = [charm.name for charm in charms_]
        assert charm_names == sorted(charm_names)
        use_substrate_instead_of_name = (
            len(charm_names) == 2 and charm_names[1] == f"{charm_names[0]}-k8s"
        )
        title_parts = []
        for charm, charm_revisions in revisions.items():
            if use_substrate_instead_of_name:
                if charm.name.endswith("-k8s"):
                    parenthetical = "Kubernetes"
                else:
                    parenthetical = "machines"
            else:
                parenthetical = charm.name
            title_parts.append(
                f"{', '.join(str(revision) for revision in charm_revisions)} ({parenthetical})"
            )
        release_title = f"Revisions: {' | '.join(title_parts)}"

    return commit_sha, release_title


def get_github_release_tag(*, commit_sha: str) -> str:
    """Get GitHub release tag from commit"""
    charm_refresh_compatibility_version_tags = subprocess.run(
        ["git", "tag", "--list", "v*/*", "--points-at", commit_sha],
        capture_output=True,
        check=True,
        text=True,
    ).stdout.splitlines()
    if len(charm_refresh_compatibility_version_tags) != 1:
        raise ValueError(
            f"Expected 1 charm refresh compatibility version tags on commit {commit_sha}, got "
            f"{len(charm_refresh_compatibility_version_tags)} tags: "
            f"{repr(charm_refresh_compatibility_version_tags)}"
        )
    return charm_refresh_compatibility_version_tags[0]


def get_last_stable_release_tag(*, track: str, charms_: list[Charm]) -> str | None:
    """Get GitHub release tag for last stable release (if it exists) on `track`"""
    channel = f"{track}/{Risk.STABLE.value}"
    logging.info(f"Getting GitHub release tag for last {repr(channel)} release")
    output = get_commit_sha_and_release_title(
        channel=channel,
        charms_=charms_,
        channel_missing_ok=True,  # In case no previous stable release
    )
    if output is None:
        logging.warning(f"No existing release found on {repr(channel)}")
        return None
    commit_sha, _ = output
    tag = get_github_release_tag(commit_sha=commit_sha)
    logging.info(f"GitHub release tag for last {repr(channel)} release: {repr(tag)}")
    return tag


def oxford_comma(items: list[str], /):
    match items:
        case []:
            raise ValueError("List must not be empty")
        case [first]:
            return first
        case [first, second]:
            return f"{first} and {second}"
        case [*all_but_last, last]:
            return f"{', '.join(all_but_last)}, and {last}"


def _validate_promotion_and_create_release(
    *,
    dry_run: bool,
    charms_: list[Charm],
    track: str,
    channel: str,
    to_risk: Risk,
):
    if dry_run:
        logging.info("Checking that revisions that will be promoted are from the same git commit")
    else:
        logging.info("Getting git commit of revisions that were promoted")
    promoted_commit_sha, release_title = get_commit_sha_and_release_title(
        channel=channel, charms_=charms_
    )

    subprocess.run(["git", "checkout", promoted_commit_sha], check=True)

    for charm in charms_:
        try:
            # Check that OCI images are pinned to sha256 digest
            promoted_charm = Charm.from_directory(charm.directory)
        except FileNotFoundError:
            if dry_run:
                message = (
                    f"Charm at {repr(charm.directory)} exists on latest commit on branch but does "
                    f"not exist on commit on {repr(channel)}"
                )
            else:
                message = (
                    f"Charm at {repr(charm.directory)} was deleted or moved during promotion. "
                    "Invalid charm promoted"
                )
            raise FileNotFoundError(message)

        if promoted_charm.name != charm.name:
            if dry_run:
                message = (
                    f"Charm 'name' in metadata.yaml changed between latest commit on branch "
                    f"({repr(charm.name)}) and commit on {repr(channel)} "
                    f"({repr(promoted_charm.name)}). Unable to promote charm"
                )
            else:
                message = (
                    "Charm 'name' in metadata.yaml changed while charm was promoted. Invalid "
                    f"charm promoted. Expected charm name {repr(charm.name)}, got "
                    f"{repr(promoted_charm.name)} instead"
                )
            raise ValueError(message)

    github_release_tag = get_github_release_tag(commit_sha=promoted_commit_sha)

    if to_risk is Risk.CANDIDATE:
        if dry_run:
            logging.info(
                "Checking that the last stable release revisions are from the same git commit and "
                "that we can determine the GitHub release tag"
            )
        previous_github_release_tag = get_last_stable_release_tag(track=track, charms_=charms_)

    if dry_run:
        return

    if to_risk is Risk.CANDIDATE:
        charm_display_names = oxford_comma(
            [f"[{charm.display_name}](https://charmhub.io/{charm.name})" for charm in charms_]
        )
        # Say "/stable" in release notes so that it's correct when the release is published
        prepended_notes = f"""A new revision of {charm_display_names} has been published in the {track}/{Risk.STABLE.value} channel on Charmhub.
"""
        for charm in charms_:
            if not charm.oci_resources:
                continue
            prepended_notes += f"\n{charm.name} OCI image resources:\n"
            for resource_name, source in charm.oci_resources:
                prepended_notes += f"- `{resource_name}={source}`\n"
        command = [
            "gh",
            "release",
            "create",
            github_release_tag,
            "--verify-tag",
            "--draft",
            "--generate-notes",
            "--title",
            release_title,
            "--notes",
            prepended_notes,
        ]
        if previous_github_release_tag is not None:
            command.extend(("--notes-start-tag", previous_github_release_tag))
        logging.info("Creating GitHub draft release")
        subprocess.run(command, check=True)
    elif to_risk is Risk.STABLE:
        # Publish GitHub release draft created during promotion to candidate risk
        logging.info("Publishing GitHub release")
        subprocess.run(
            ["gh", "release", "edit", github_release_tag, "--verify-tag", "--draft=false"],
            check=True,
        )


def charms():
    parser = argparse.ArgumentParser()
    parser.add_argument("--track", required=True)
    parser.add_argument("--from-risk", required=True)
    parser.add_argument("--to-risk", required=True)
    parser.add_argument("--ref", required=True)
    args = parser.parse_args()

    charms_: list[Charm] = []
    for path in pathlib.Path().glob("**/charmcraft.yaml"):
        if "tests" in path.parts:
            logging.info(f"Ignoring charm inside a 'tests' directory: {repr(path.parent)}")
            continue
        charms_.append(Charm.from_directory(path.parent))

    if len({charm.name for charm in charms_}) != len(charms_):
        raise ValueError(
            f"Duplicate charms with same 'name' in metadata.yaml not supported: {repr(charms_)}"
        )
    charms_ = sorted(charms_, key=lambda charm: charm.name)

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
            "This workflow must be run on `workflow_dispatch` from the branch that contains track "
            f"{repr(track)}"
        )

    if not pathlib.Path(".github/release.yaml").exists():
        raise FileNotFoundError(
            "Repository must contain `.github/release.yaml` to automatically generate release "
            "notes in the correct format. See "
            "https://github.com/canonical/data-platform-workflows/blob/main/.github/workflows/promote_charms.md#step-3-add-githubreleaseyaml-file"
        )

    from_channel = f"{track}/{from_risk}"
    to_channel = f"{track}/{to_risk}"

    _validate_promotion_and_create_release(
        dry_run=True, charms_=charms_, track=track, channel=from_channel, to_risk=to_risk
    )

    logging.info(f"Promoting charms from {repr(from_channel)} to {repr(to_channel)}")
    for charm in charms_:
        # One-time exception to requirement that charms in monorepo have the same track—to enable
        # MySQL Router charms to use monorepo. (VM 8.0 track is managed by another team for
        # historical reasons.) Refresh compatibility tag will still use "dpe".
        if charm.name == "mysql-router-k8s" and track == "dpe":
            logging.warning(
                "Exception for mysql-router-k8s on track 'dpe': using track '8.0' instead for "
                "Charmhub operations"
            )
            charm_from_channel = from_channel.replace("dpe/", "8.0/")
            charm_to_channel = to_channel.replace("dpe/", "8.0/")
        else:
            charm_from_channel = from_channel
            charm_to_channel = to_channel

        logging.info(
            f"Promoting {repr(charm.name)} charm from {repr(charm_from_channel)} to "
            f"{repr(charm_to_channel)}"
        )
        subprocess.run(
            [
                "charmcraft",
                "promote",
                "--name",
                charm.name,
                "--from-channel",
                charm_from_channel,
                "--to-channel",
                charm_to_channel,
                "--yes",
            ],
            check=True,
        )

    _validate_promotion_and_create_release(
        dry_run=False, charms_=charms_, track=track, channel=to_channel, to_risk=to_risk
    )
