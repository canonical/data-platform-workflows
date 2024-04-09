"""Convert Juju controller logsink to `juju debug-log --color` format"""

import argparse
import enum
import pathlib
import re
import subprocess

PATTERN = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}: (?P<entity>.*?) [0-9]{4}-[0-9]{2}-[0-9]{2} (?P<time>[0-9]{2}:[0-9]{2}:[0-9]{2}) (?P<level>TRACE|DEBUG|INFO|WARNING|ERROR|CRITICAL) (?P<message>.*)\n"
)


class Level(enum.Enum):
    TRACE = (0, "[39m")
    DEBUG = (1, "[32m")
    INFO = (2, "[94m")
    WARNING = (3, "[33m")
    ERROR = (4, "[91m")
    CRITICAL = (5, "[41;97m")

    def __lt__(self, other):
        if not isinstance(other, type(self)):
            raise TypeError
        return self.value[0] < other.value[0]

    def __str__(self):
        """Name with ANSI color code"""
        return f"{self.value[1]}{self.name}[0m"


def main():
    # Assumes `logging-config` of `<root>=INFO; unit=DEBUG`
    assert (
        subprocess.run(
            ["juju", "model-config", "logging-config"],
            capture_output=True,
            check=True,
            encoding="utf-8",
        ).stdout.rstrip("\n")
        == "<root>=INFO; unit=DEBUG"
    )
    parser = argparse.ArgumentParser()
    parser.add_argument("logsink_file")
    parser.add_argument("output_file")
    args = parser.parse_args()
    logsink = pathlib.Path(args.logsink_file).expanduser()
    output = pathlib.Path(args.output_file).expanduser()
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
                entity = match.group("entity")
                level = Level[match.group("level")]
                if entity.startswith("unit-"):
                    if level < Level.DEBUG:
                        skip = True
                else:
                    if level < Level.INFO:
                        skip = True
                # Example of original line:
                # "276ce0fa-a69d-4e2c-8793-031a46bac9e1: machine-3 2024-04-05 14:50:47 INFO juju.worker.leadership tracker.go:194 opensearch/2 promoted to leadership of opensearch "
                # Example of replaced line:
                # "machine-3: 14:50:47 [94mINFO[0m juju.worker.leadership tracker.go:194 opensearch/2 promoted to leadership of opensearch"
                line = f'{entity}: {match.group("time")} {level} {match.group("message").rstrip(" ")}\n'
            if not skip:
                output_file.write(line)
