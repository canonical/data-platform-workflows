"""Convert Juju controller logsink to `juju debug-log --color` format"""

import argparse
import enum
import json
import pathlib
import re
import subprocess

PATTERN = re.compile(
    r"(?P<model>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}): (?P<entity>.*?) [0-9]{4}-[0-9]{2}-[0-9]{2} (?P<time>[0-9]{2}:[0-9]{2}:[0-9]{2}) (?P<level>TRACE|DEBUG|INFO|WARNING|ERROR|CRITICAL) (?P<message>.*)\n"
)
LINE_NUMBER_PATTERN = re.compile(r" \S+\.go:[0-9]+ ")


class Level(enum.Enum):
    TRACE = "[39m"
    DEBUG = "[32m"
    INFO = "[94m"
    WARNING = "[33m"
    ERROR = "[91m"
    CRITICAL = "[41;97m"

    def __str__(self):
        """Name with ANSI color code"""
        return f"{self.value[1]}{self.name}[0m"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("logsink_file")
    parser.add_argument("output_file")
    args = parser.parse_args()
    logsink = pathlib.Path(args.logsink_file).expanduser()
    output = pathlib.Path(args.output_file).expanduser()
    model = json.loads(
        subprocess.run(
            ["juju", "show-model", "--format", "json"],
            capture_output=True,
            check=True,
            encoding="utf-8",
        ).stdout
    )["test"]["controller-uuid"]
    print(model)
    with logsink.open("r", encoding="utf-8") as logsink_file, output.open(
        "w", encoding="utf-8"
    ) as output_file:
        # `skip` used for multi-line log messages
        skip = False
        for line in logsink_file:
            match = re.fullmatch(PATTERN, line)
            if match:
                # First line of log message
                skip = False
                if match.group("model") != model:
                    skip = True
                # Example of original line:
                # "276ce0fa-a69d-4e2c-8793-031a46bac9e1: machine-3 2024-04-05 14:50:47 INFO juju.worker.leadership tracker.go:194 opensearch/2 promoted to leadership of opensearch "
                # Example of replaced line:
                # "machine-3: 14:50:47 [94mINFO[0m juju.worker.leadership opensearch/2 promoted to leadership of opensearch"
                message = re.sub(
                    LINE_NUMBER_PATTERN,
                    " ",
                    match.group("message").rstrip(" "),
                    count=1,
                )
                line = f'{match.group("entity")}: {match.group("time")} {Level[match.group("level")]} {message}\n'
            if not skip:
                output_file.write(line)
