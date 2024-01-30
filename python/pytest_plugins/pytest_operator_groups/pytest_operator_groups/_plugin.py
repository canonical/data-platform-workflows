import dataclasses
import json
import os
import typing

import pytest

_Runner = typing.Union[str, tuple[str]]


def pytest_addoption(parser):
    parser.addoption(
        "--collect-groups",
        action="store_true",
        help="Collect test groups (used by GitHub Actions)",
    )
    parser.addoption("--group", help="Integration test group ID")


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "group(id): Parallelize tests in a file across GitHub runners"
    )
    config.addinivalue_line(
        "markers",
        "runner(runs_on): GitHub Actions `runs-on` label(s) (https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#jobsjob_idruns-on)",
    )
    if config.option.collect_groups:
        config.option.collectonly = True
        assert (
            config.option.group is None
        ), "--group should not be used with --collect-groups"


def _get_group_id(function) -> typing.Optional[str]:
    """Get group ID from test function marker.

    This example has a group ID of "1":
    @pytest.mark.group(1)
    def test_build_and_deploy():
        pass
    """
    group_markers = [
        marker for marker in function.own_markers if marker.name == "group"
    ]
    if not group_markers:
        return
    assert len(group_markers) == 1
    marker_args = group_markers[0].args
    assert len(marker_args) == 1
    group_id = marker_args[0]
    assert isinstance(group_id, int) or isinstance(group_id, str)
    group_id = str(group_id)
    for character in "\\/\"':<>|*?":
        # Invalid character for GitHub Actions artifact
        # (https://github.com/actions/upload-artifact/issues/22)
        assert (
            character not in group_id
        ), f"Invalid {character=} for GitHub Actions artifact"
    return str(group_id)


def _get_runner(function) -> typing.Optional[_Runner]:
    """Get runner from test function marker.

    Syntax: `runs-on` string
    https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#jobsjob_idruns-on

    This example has a runner of "ubuntu-latest":
    @pytest.mark.runner("ubuntu-latest")
    def test_build_and_deploy():
        pass
    """
    runner_markers = [
        marker for marker in function.own_markers if marker.name == "runner"
    ]
    if not runner_markers:
        return
    assert len(runner_markers) == 1
    marker_args = runner_markers[0].args
    assert len(marker_args) == 1
    runner = marker_args[0]
    if isinstance(runner, str):
        return runner
    elif isinstance(runner, tuple) or isinstance(runner, list):
        for item in runner:
            if not isinstance(item, str):
                break
        else:
            return tuple(runner)
    raise TypeError(
        f"`pytest.mark.runner(runs_on)` must be str, tuple[str], or list[str]"
    )


def _collect_groups(items):
    """Collect unique group IDs for each test module."""

    @dataclasses.dataclass(eq=True, order=True, frozen=True)
    class Group:
        path_to_test_file: str
        group_id: str
        job_name: str
        artifact_group_id: str

    @dataclasses.dataclass(eq=True, order=True, frozen=True)
    class GroupWithRunner(Group):
        runner: typing.Optional[_Runner]
        self_hosted: bool

        @classmethod
        def from_group(cls, group: Group, *, runner: typing.Optional[_Runner]):
            if isinstance(runner, tuple):
                self_hosted = "self-hosted" in runner
            else:
                self_hosted = False
            return cls(
                **dataclasses.asdict(group), runner=runner, self_hosted=self_hosted
            )

    group_to_runners: dict[Group, set[_Runner]] = {}
    for function in items:
        if (group_id := _get_group_id(function)) is None:
            raise Exception(
                f"{function} missing group ID. Docs: https://github.com/canonical/data-platform-workflows/blob/main/.github/workflows/integration_test_charm.md#step-3-split-test-functions-into-groups"
            )
        # Example: "integration.relations.test_database"
        name = function.module.__name__
        assert name.split(".")[0] == "integration"
        # Example: "tests/integration/relations/test_database.py"
        path_to_test_file = f"tests/{name.replace('.', '/')}.py"
        # Example: "relations/test_database.py | group 1"
        job_name = f"{'/'.join(path_to_test_file.split('/')[2:])} | group {group_id}"
        # Example: "relations-test_database.py-group-1"
        artifact_group_id = (
            f"{'-'.join(path_to_test_file.split('/')[2:])}-group-{group_id}"
        )
        runners = group_to_runners.setdefault(
            Group(path_to_test_file, group_id, job_name, artifact_group_id), set()
        )
        if runner := _get_runner(function):
            runners.add(runner)
    groups: list[GroupWithRunner] = []
    for group, runners in group_to_runners.items():
        assert len(runners) <= 1, "All tests in a group must use the same runner"
        try:
            runner = runners.pop()
        except KeyError:
            runner = None
        groups.append(GroupWithRunner.from_group(group, runner=runner))
    sorted_groups: list[dict] = [dataclasses.asdict(group) for group in sorted(groups)]
    assert (
        len(sorted_groups) > 0
    ), "Zero groups found. Add `pytest.mark.group(1)` to every test"
    output = f"groups={json.dumps(sorted_groups)}"
    print(f"\n\n{output}\n")
    output_file = os.environ["GITHUB_OUTPUT"]
    with open(output_file, "a") as file:
        file.write(output)


@pytest.hookimpl(trylast=True)  # Run after tests are deselected with `-m`
def pytest_collection_modifyitems(config, items):
    if config.option.collect_groups:
        _collect_groups(items)
    elif config.option.group:
        assert (
            len({function.module.__name__ for function in items}) == 1
        ), "Only 1 test module can be ran if --group is specified"
        # Remove tests that do not match the selected group ID
        filtered_items = []
        for function in items:
            group_id = _get_group_id(function)
            if group_id is None:
                raise Exception(
                    f"{function} missing group ID. Docs: https://github.com/canonical/data-platform-workflows/blob/main/.github/workflows/integration_test_charm.md#step-3-split-test-functions-into-groups"
                )
            elif group_id == config.option.group:
                filtered_items.append(function)
        items[:] = filtered_items
