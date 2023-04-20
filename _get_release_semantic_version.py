"""Get release semantic version"""
import os
import re
import subprocess

# Get last release version
# Example: "foobar	Latest	v1.1.2	2023-02-15T17:50:06Z"
last_release = subprocess.check_output(
    [
        "gh",
        "release",
        "list",
        "--limit",
        "1",
        "--exclude-drafts",
        "--exclude-pre-releases",
    ],
    encoding="utf-8",
)
last_release_version = last_release.split("\t")[2]
assert re.fullmatch(
    r"v[0-9]+\.[0-9]+\.[0-9]+", last_release_version
), f"Invalid version format {last_release_version=}"
major, minor, patch = (
    int(component) for component in last_release_version[1:].split(".")
)

# Get prefixes (see CONTRIBUTING.md) of commits since last release
commits_since_last_release = subprocess.check_output(
    ["git", "log", f"{last_release_version}..HEAD", "--pretty=format:%s"],
    encoding="utf-8",
).splitlines()
prefixes = set()
for commit_subject in commits_since_last_release:
    if ":" not in commit_subject:
        continue
    prefix = commit_subject.split(":")[0]
    for valid_prefix in ["patch", "compatible", "breaking"]:
        if prefix.startswith(valid_prefix):
            prefixes.add(valid_prefix)
            break

# Pick new semantic version based on commit prefixes
if "breaking" in prefixes:
    major += 1
    minor = 0
    patch = 0
elif "compatible" in prefixes:
    minor += 1
    patch = 0
elif "patch" in prefixes:
    patch += 1
else:
    raise ValueError(
        "No commits since last release with valid prefix (see CONTRIBUTING.md)."
    )

output = f"full_version=v{major}.{minor}.{patch}\nmajor_version=v{major}"
print(output)
with open(os.environ["GITHUB_OUTPUT"], "a") as file:
    file.write(output)
