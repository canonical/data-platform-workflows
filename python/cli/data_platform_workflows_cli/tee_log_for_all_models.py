import argparse
import json
import pathlib
import subprocess

from . import github_actions


def main():
    """For each Juju model, run command and write command output to standard output and log file"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--log-command", required=True)
    parser.add_argument("--log-file-name", required=True)
    args = parser.parse_args()
    output = subprocess.run(
        ["juju", "models", "--format", "json"],
        check=True,
        capture_output=True,
        encoding="utf-8",
    ).stdout
    models: list[str] = [
        model["short-name"]
        for model in json.loads(output)["models"]
        if not model["is-controller"]
    ]
    multiple_models = len(models) > 1
    for model in models:
        log_path = pathlib.Path("~/logs")
        if multiple_models:
            github_actions.begin_group(f"Model: {model}")
            log_path = log_path / f"model_{model}"
        log_path = log_path / args.log_file_name
        subprocess.run(
            f"{args.log_command} --model '{model}' | tee {log_path}",
            shell=True,
            check=True,
        )
        if multiple_models:
            github_actions.end_group()
