import dataclasses
import json
import os
import typing

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--collect-groups",
        action="store_true",
        help="Collect test groups (used by GitHub Actions)",
    )
    parser.addoption("--group", type=int, help="Integration test group number")


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "group: Parallelize tests in a file across GitHub runners"
    )
    if config.option.collect_groups:
        config.option.collectonly = True
        assert (
            config.option.group is None
        ), "--group should not be used with --collect-groups"


def _get_group_number(function) -> typing.Optional[int]:
    """Get group number from test function marker.

    This example has a group number of 1:
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
    group_number = marker_args[0]
    assert isinstance(group_number, int)
    return group_number


def _collect_groups(items):
    """Collect unique group numbers for each test module."""

    @dataclasses.dataclass(eq=True, order=True, frozen=True)
    class Group:
        path_to_test_file: str
        group_number: int
        job_name: str
        log_artifact_path: str

    groups: set[Group] = set()
    for function in items:
        if (group_number := _get_group_number(function)) is None:
            continue
        # Example: "integration.relations.test_database"
        name = function.module.__name__
        assert name.split(".")[0] == "integration"
        # Example: "tests/integration/relations/test_database.py"
        path_to_test_file = f"tests/{name.replace('.', '/')}.py"
        # Example: "relations/test_database.py | group 1"
        job_name = (
            f"{'/'.join(path_to_test_file.split('/')[2:])} | group {group_number}"
        )
        # Example: "relations/test_database.py/group-1"
        log_artifact_path = (
            f"{'/'.join(path_to_test_file.split('/')[2:])}/group-{group_number}"
        )
        groups.add(Group(path_to_test_file, group_number, job_name, log_artifact_path))
    sorted_groups: list[dict] = [
        dataclasses.asdict(group) for group in sorted(list(groups))
    ]
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
        # Remove tests that do not match the selected group number
        filtered_items = []
        for function in items:
            group_number = _get_group_number(function)
            if group_number is None:
                function.add_marker(pytest.mark.skip("Missing group number"))
                filtered_items.append(function)
            elif group_number == config.option.group:
                filtered_items.append(function)
        items[:] = filtered_items
