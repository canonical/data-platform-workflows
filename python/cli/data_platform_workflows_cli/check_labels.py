#!/usr/bin/env python3
import argparse
import json
import os
import sys
import logging
import subprocess

REPO = os.environ["GITHUB_REPOSITORY"]
TOKEN = os.environ["GITHUB_TOKEN"]

required_labels = [
    "stable: Solutions QA tests passed",
    "stable: engineering manager approved",
    "stable: product manager approved",
    "stable: release notes curated",
]

logging.basicConfig(level=logging.INFO, stream=sys.stdout)


def fetch_issue(issue_number: int) -> dict:
    logging.info(f"Fetching issue #{issue_number} from {REPO}")
    result = subprocess.run(
        ["gh", "issue", "view", str(issue_number), "--repo", REPO, "--json", "labels"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"gh issue view failed: {result.stderr.strip()}")
    return json.loads(result.stdout)


def comment_and_close_issue(issue_number: int, message: str) -> None:
    """Post a comment and close the given issue."""
    logging.info(f"Closing issue #{issue_number} with comment: {message!r}")
    result = subprocess.run(
        [
            "gh",
            "issue",
            "close",
            str(issue_number),
            "--repo",
            REPO,
            "--comment",
            message,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"gh issue close failed: {result.stderr.strip()}")
    logging.info("Issue closed with comment successfully.")


def check_labels(issue_data: dict, required: list[str]) -> None:
    labels = [label["name"] for label in issue_data.get("labels", [])]
    logging.info(f"Labels on issue: {labels}")
    missing = [label for label in required if label not in labels]
    if missing:
        raise ValueError(f"Missing labels: {missing}")


def main():
    parser = argparse.ArgumentParser(
        description="Create a GitHub issue to track releasing a refresh version to stable."
    )
    parser.add_argument(
        "--issue-number",
        required=True,
        help="The number of the Github issue to check for labels.",
    )
    args = parser.parse_args()

    issue_number = args.issue_number

    issue_data = fetch_issue(issue_number)
    check_labels(issue_data, required_labels)
    logging.info("All required labels are present. Stable release approved!")
    comment_and_close_issue(issue_number, "Released to stable")


if __name__ == "__main__":
    main()
