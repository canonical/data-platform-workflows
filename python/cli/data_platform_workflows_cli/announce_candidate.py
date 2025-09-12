#!/usr/bin/env python3
import argparse
import os
import sys
import logging
import subprocess

import requests

MATTERMOST_WEBHOOK_URL = os.environ["MATTERMOST_WEBHOOK_URL"]
REPO = os.environ["GITHUB_REPOSITORY"]
GH_TOKEN = os.environ.get("GITHUB_TOKEN")

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

ISSUE_BODY_TEMPLATE = """\
Release notes:  {release_notes_link}

{refresh_version} will be automatically released to stable once these conditions are met:
- this issue has `stable: Solutions QA tests passed` label
- this issue has `stable: release notes curated` label
- this issue has `stable: product manager approved` label
- this issue has `stable: engineering manager approved` label
"""


def get_release_notes_link(tag: str) -> str:
    """Retrieve the release notes link (URL) for a given tag using gh CLI."""
    logging.info(f"Fetching release notes link for tag {tag!r} from {REPO}")
    result = subprocess.run(
        [
            "gh",
            "release",
            "view",
            tag,
            "--repo",
            REPO,
            "--json",
            "url",
            "--jq",
            ".url",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"gh release view failed: {result.stderr.strip()}")
    return result.stdout.strip()


def create_issue(title: str, body: str) -> int:
    """Create a new GitHub issue and return its url."""
    cmd = [
        "gh",
        "issue",
        "create",
        "--repo",
        REPO,
        "--title",
        title,
        "--body",
        body,
    ]

    logging.info(f"Creating issue in {REPO} with title: {title!r}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"gh issue create failed: {result.stderr.strip()}")

    url = result.stdout.strip()
    logging.info(f"Issue created successfully: {url}")

    return url


def notify_mattermost(refresh_version, issue_url):
    """
    Send a MM message to notify about the candidate release.
    """
    repo_name = REPO.split("/")[1]
    message = (
        f"`{repo_name}` with refresh compat version {refresh_version} released to candidate\n\n"
        ""
    )
    f"Issue: {issue_url}\n\n"
    "Approvers required to promote to stable: TBD"
    response_ = requests.post(
        MATTERMOST_WEBHOOK_URL,
        headers={"Content-Type": "application/json"},
        json={"text": message},
    )
    response_.raise_for_status()


def main():
    parser = argparse.ArgumentParser(
        description="Create a GitHub issue to track releasing a refresh version to stable."
    )
    parser.add_argument(
        "--refresh-version",
        required=True,
        help="Version tag to release to stable (must match an existing GitHub release tag).",
    )
    args = parser.parse_args()

    refresh_version = args.refresh_version
    release_notes_link = get_release_notes_link(refresh_version)

    title = f"Release {refresh_version} to stable"
    body = ISSUE_BODY_TEMPLATE.format(
        release_notes_link=release_notes_link,
        refresh_version=refresh_version,
    )

    issue_url = create_issue(title, body)
    logging.info(f"Created candidate tracking issue {issue_url} for {refresh_version}.")

    notify_mattermost(refresh_version, issue_url)


if __name__ == "__main__":
    main()
