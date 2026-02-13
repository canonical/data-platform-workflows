import argparse
import json
import subprocess

from . import github_actions


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--revisions")
    parser.add_argument("--revision")
    parser.add_argument("--channel", required=True)
    parser.add_argument("--revision-input-name", required=True)
    parser.add_argument("--channel-input-name", required=True)
    args = parser.parse_args()
    # Validate workflow usage (not user input to workflow)
    if args.revisions is not None and args.revision is not None:
        raise ValueError("Only one of `--revisions` or `--revision` can be used")
    elif args.revisions is None and args.revision is None:
        raise ValueError("`--revisions` or `--revision` is required")

    # Validate user input to workflow
    if args.revisions is not None:
        if args.revisions:
            invalid_type_message = (
                f"`{args.revision_input_name}` input must be JSON string with type dict[str, str]"
            )
            try:
                revisions = json.loads(args.revisions)
            except ValueError:
                raise ValueError(invalid_type_message)
            if not isinstance(revisions, dict):
                raise ValueError(invalid_type_message)
            if len(revisions) == 0:
                raise ValueError(f"`{args.revision_input_name}` input must not be empty dict")
            for key, value in revisions.items():
                if not (isinstance(key, str) and isinstance(value, str)):
                    raise ValueError(invalid_type_message)

            architecture = subprocess.run(
                ["dpkg", "--print-architecture"], capture_output=True, check=True, encoding="utf-8"
            ).stdout.strip()
            try:
                revision = revisions[architecture]
            except KeyError:
                raise KeyError(
                    f"{repr(architecture)} key missing from `{args.revision_input_name}` input"
                )
        else:
            revision = None
    else:
        revision = args.revision
    if revision:
        assert not args.channel, (
            f"`{args.channel_input_name}` input cannot be used if `{args.revision_input_name}` "
            "input is passed"
        )
        install_flag = f"'--revision={revision}'"
    elif args.channel:
        install_flag = f"'--channel={args.channel}'"
    else:
        install_flag = None
    github_actions.output["install_flag"] = install_flag
