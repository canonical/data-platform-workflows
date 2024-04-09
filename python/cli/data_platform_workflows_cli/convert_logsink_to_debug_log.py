"""Convert Juju controller logsink to `juju debug-log --color` format"""

import argparse
import pathlib
import re

PATTERN = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}: (?P<entity>.*?) [0-9]{4}-[0-9]{2}-[0-9]{2} (?P<time>[0-9]{2}:[0-9]{2}:[0-9]{2}) (?P<level>DEBUG|INFO|WARNING|ERROR|CRITICAL) (?P<message>.*)\n"
)
LEVEL_COLORS = {
    "DEBUG": "[32m",
    "INFO": "[94m",
    "WARNING": "[33m",
    "ERROR": "[91m",
    "CRITICAL": "[41;97m",
}
LEVELS = {level: f"{color}{level}[0m" for level, color in LEVEL_COLORS.items()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("logsink_file")
    parser.add_argument("output_file")
    args = parser.parse_args()
    logsink = pathlib.Path(args.logsink_file).expanduser()
    output = pathlib.Path(args.output_file).expanduser()
    with logsink.open("r", encoding="utf-8") as logsink_file, output.open(
        "w", encoding="utf-8"
    ) as output_file:
        for line in logsink_file:
            match = re.fullmatch(PATTERN, line)
            if match:
                # Example of original line:
                # "276ce0fa-a69d-4e2c-8793-031a46bac9e1: machine-3 2024-04-05 14:50:47 INFO juju.worker.leadership tracker.go:194 opensearch/2 promoted to leadership of opensearch "
                # Example of replaced line:
                # "machine-3: 14:50:47 [94mINFO[0m juju.worker.leadership tracker.go:194 opensearch/2 promoted to leadership of opensearch"
                line = f'{match.group("entity")}: {match.group("time")} {LEVELS[match.group("level")]} {match.group("message").rstrip(" ")}\n'
            output_file.write(line)
