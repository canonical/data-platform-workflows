import argparse
import logging
import pathlib
import subprocess
import sys
import tomllib

logging.basicConfig(level=logging.INFO, stream=sys.stdout)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--track", required=True)
    args = parser.parse_args()
    track = args.track

    if not pathlib.Path("refresh_versions.toml").exists():
        raise FileNotFoundError(
            "refresh_versions.toml not found. The tag_charm_edge.yaml workflow currently only "
            "supports git repositories that contain a single charm"
        )

    # Create charm refresh compatibility version tag
    # https://docs.google.com/document/d/1Jv1jhWLl8ejK3iJn7Q3VbCIM9GIhp8926bgXpdtx-Sg/edit?tab=t.0
    # TODO: replace link with refresh v3 dev doc link when dev docs added

    for character in "?*[":  # These characters have special meaning in `git describe --match`
        assert character not in track
    # Get last charm refresh compatibility version tag
    try:
        last_refresh_tag = subprocess.run(
            # Use `HEAD^` to exclude a tag created by a previous workflow run (on `HEAD`) if the
            # workflow was retried
            ["git", "describe", "--abbrev=0", "--match", f"v{track}/*", "HEAD^"],
            capture_output=True,
            check=True,
            text=True,
        ).stdout.strip()
    except subprocess.CalledProcessError as e:
        if "no names found" in e.stderr.lower():
            files_added_in_last_commit = subprocess.run(
                [
                    "git",
                    "diff-tree",
                    "--diff-filter=A",
                    "--name-only",
                    "--no-commit-id",
                    "HEAD",
                ],
                capture_output=True,
                check=True,
                text=True,
            ).stdout.splitlines()
            if "refresh_versions.toml" in files_added_in_last_commit:
                last_refresh_tag = None
                # charm-refresh was (most likely) added for the first time in the last commit
                logging.info("Detected that refresh_versions.toml was added in the last commit")
            else:
                raise Exception(
                    f"Unable to find previous charm refresh compatibility version git tag\n\n"
                    f"stderr:\n{e.stderr}"
                )
        else:
            print(f"{e.stderr=}")
            raise
    logging.info(f"Last charm refresh compatibility version tag: {last_refresh_tag}")

    with pathlib.Path("refresh_versions.toml").open("rb") as file:
        data = tomllib.load(file)
    try:
        new_charm_major = data["charm_major"]
    except KeyError:
        # TODO add link to refresh v3 dev docs
        raise KeyError("Required key missing from refresh_versions.toml")

    if last_refresh_tag is None:
        new_refresh_tag = f"v{track}/1.0.0"
    else:
        # Example `last_refresh_tag`: "v14/1.12.0"

        _, components = last_refresh_tag.split("/")
        last_charm_major, last_edge, last_backport = (
            int(component) for component in components.split(".")
        )
        if last_backport != 0:
            raise ValueError(
                "Expected last component of charm refresh compatibility version to be 0 on a "
                f"git branch that releases to edge, got {repr(last_backport)}: "
                f"{repr(last_refresh_tag)}"
            )

        if last_charm_major == new_charm_major:
            new_refresh_tag = f"v{track}/{new_charm_major}.{last_edge + 1}.0"
        else:
            new_refresh_tag = f"v{track}/{new_charm_major}.0.0"
    logging.info(f"Determined new charm refresh compatibility version tag: {new_refresh_tag}")

    logging.info("Checking if new charm refresh compatibility version tag already exists")
    try:
        tag_commit_sha = subprocess.run(
            ["git", "rev-list", "-n", "1", new_refresh_tag],
            capture_output=True,
            check=True,
            text=True,
        ).stdout.strip()
    except subprocess.CalledProcessError:
        logging.info("Charm refresh compatibility version tag does not already exist. Creating tag")
        subprocess.run(
            ["git", "tag", new_refresh_tag, "--annotate", "-m", new_refresh_tag], check=True
        )
        subprocess.run(["git", "push", "origin", new_refresh_tag], check=True)
    else:
        logging.info("Charm refresh compatibility version tag already exists. Verifying tag")
        head_commit_sha = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, check=True, text=True
        ).stdout.strip()
        if head_commit_sha == tag_commit_sha:
            logging.info("Verified existing tag points to the correct commit")
        else:
            raise ValueError(
                f"Attempted to create tag {new_refresh_tag} on commit {head_commit_sha} but tag "
                f"already exists on commit {tag_commit_sha}"
            )
