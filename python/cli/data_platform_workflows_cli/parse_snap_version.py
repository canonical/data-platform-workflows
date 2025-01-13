import argparse

from . import github_actions


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--revision", required=True)
    parser.add_argument("--channel", required=True)
    parser.add_argument("--revision-input-name", required=True)
    parser.add_argument("--channel-input-name", required=True)
    args = parser.parse_args()
    if args.revision:
        assert (
            not args.channel
        ), f"`{args.channel_input_name}` input cannot be used if `{args.revision_input_name}` input is passed"
        install_flag = f"'--revision={args.revision}'"
    elif args.channel:
        install_flag = f"'--channel={args.channel}'"
    else:
        install_flag = None
    github_actions.output["install_flag"] = install_flag
