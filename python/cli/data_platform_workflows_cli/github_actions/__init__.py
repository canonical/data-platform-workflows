"""Python API for GitHub Actions

Supports:
- Workflow commands: https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions
- Default environment variables: https://docs.github.com/en/actions/learn-github-actions/variables#default-environment-variables

Does not include support for GitHub REST API
"""

import collections.abc
import os
import pathlib
import sys

_OutputBaseType = collections.abc.MutableMapping[str, str | None]
_output_file = pathlib.Path(os.environ["GITHUB_OUTPUT"])


class _Output(_OutputBaseType):
    def __setitem__(self, key, value: str | None):
        if value is None:
            value = ""
        if "\n" in value:
            raise NotImplementedError(
                "Output of multi-line strings not supported by Python API. Write directly to GITHUB_OUTPUT file\n"
                "https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#setting-an-output-parameter"
            )
        with _output_file.open("a", encoding="utf-8") as file:
            file.write(f"{key}={value}\n")
        print(f"GitHub Actions step output: {key}={value}", flush=True)

    def __delitem__(self, key):
        self.__setitem__(key, None)

    def __getitem__(self, key):
        raise NotImplementedError(
            "Cannot read GitHub Actions output. Output is write-only"
        )

    def __iter__(self):
        raise NotImplementedError(
            "Cannot read GitHub Actions output. Output is write-only"
        )

    def __len__(self):
        raise NotImplementedError(
            "Cannot read GitHub Actions output. Output is write-only"
        )


class _ThisModule(sys.modules[__name__].__class__):
    """Contains properties for this module

    https://stackoverflow.com/a/34829743
    """

    _output = _Output()

    @property
    def output(self) -> _OutputBaseType:
        return self._output

    @output.setter
    def output(self, value: _OutputBaseType):
        # Clear file contents
        with _output_file.open(mode="w", encoding="utf-8"):
            pass

        self._output = _Output()
        self._output.update(value)


output: _OutputBaseType
"""Step outputs

https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#setting-an-output-parameter
"""

sys.modules[__name__].__class__ = _ThisModule


def begin_group(title: str):
    """Begin an expandable group in the log

    Anything printed to the log between `begin_group()` and `end_group()` is nested inside an
    expandable entry in the log.

    https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#grouping-log-lines
    """
    print(f"::group::{title}", flush=True)


def end_group():
    """End an expandable group in the log

    Anything printed to the log between `begin_group()` and `end_group()` is nested inside an
    expandable entry in the log.

    https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#grouping-log-lines
    """
    print("::endgroup::", flush=True)
