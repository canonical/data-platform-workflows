import argparse
import os


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--revision", required=True)
    parser.add_argument("--channel", required=True)
    parser.add_argument("--revision-input-name", required=True)
    parser.add_argument("--channel-input-name", required=True)
    args = parser.parse_args()
    output = "install_flag="
    if args.revision:
        assert (
            not args.channel
        ), f"`{args.channel_input_name}` input cannot be used if `{args.revision_input_name}` input is passed"
        output += f"--revision={args.revision}"
    elif args.channel:
        output += f"--channel={args.channel}"

    print(output)
    with open(os.environ["GITHUB_OUTPUT"], "a") as file:
        file.write(output)
