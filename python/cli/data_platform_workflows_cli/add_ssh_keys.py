import importlib.resources
import os
import pathlib

import requests

from . import static


def main():
    # TODO: use GitHub API to get list of users in `canonical/data-platform` team instead of
    # hard-coding (waiting for approval from IS on token request)
    # https://docs.github.com/en/rest/teams/members?apiVersion=2022-11-28#list-team-members
    user_file = importlib.resources.files(static) / "data_platform_usernames"
    users = user_file.read_text(encoding="utf-8").strip().split("\n")
    keys = []
    for user in users:
        response = requests.get(
            f"https://api.github.com/users/{user}/keys",
            headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "Authorization": f'Bearer {os.environ["GH_TOKEN"]}',
            },
        )
        response.raise_for_status()
        for key in response.json():
            keys.append(key["key"])
    authorized_keys = pathlib.Path("~/.ssh/authorized_keys").expanduser()
    with authorized_keys.open("a", encoding="utf-8") as file:
        file.writelines(f"{key}\n" for key in keys)
