Run integration tests on parallel GitHub runners

By default, [pytest-operator](https://github.com/charmed-kubernetes/pytest-operator) runs each test file (Python module) in a separate Juju model. Usually, on GitHub, each integration test file is run in parallel (on separate runners).

This plugin allows further parallelization—an individual test file can be split into multiple groups. Each group can run on a separate GitHub runner.

## Installation (Poetry)
### Step 1
Add
```toml
pytest-operator-groups = {git = "https://github.com/canonical/data-platform-workflows", tag = "v0.0.0", subdirectory = "python/pytest_plugins/pytest_operator_groups"}
```
to your integration test dependencies in `pyproject.toml`.

### Step 2
Disable Poetry's parallel installation for integration test dependencies.

Example `tox.ini`:
```ini
[testenv:integration]
set_env =
    {[testenv]set_env}
    # Workaround for https://github.com/python-poetry/poetry/issues/6958
    POETRY_INSTALLER_PARALLEL = false
```

### Step 3
If you're using tox, pass in the `GITHUB_OUTPUT` environment variable in `tox.ini`.
```ini
[testenv:integration]
pass_env =
    {[testenv]pass_env}
    GITHUB_OUTPUT
```

## Usage
### Split test functions into groups
Add
```python
@pytest.mark.group(1)
```
to every test function. Replace `1` with the group number.

#### Deciding how to split tests into groups
Take a look at this Discourse post: https://discourse.charmhub.io/t/faster-ci-results-by-running-integration-tests-in-parallel/8816

### Run tests
```
pytest test_file.py --group=1
```

### In CI, discover groups and provision a runner for each group
```
pytest --collect-groups
```
saves a JSON string to `GITHUB_OUTPUT`. Example JSON data:
```json
[
  {
    "path_to_test_file": "tests/integration/relations/test_database.py",
    "group_number": 1,
    "job_name": "relations/test_database.py | group 1"
  }
]
```

Use this output to create a GitHub Actions matrix. Example:
```yaml
jobs:
  collect-integration-tests:
    name: Collect integration test groups
    steps:
      - name: Checkout
      - name: Collect test groups
        id: collect-groups
        run: tox run -e integration -- --collect-groups
    outputs:
      groups: ${{ steps.collect-groups.outputs.groups }}

  integration-test:
    strategy:
      matrix:
        groups: ${{ fromJSON(needs.collect-integration-tests.outputs.groups) }}
    name: ${{ matrix.groups.job_name }}
    needs:
      - collect-integration-tests
    steps:
      - name: Checkout
      - name: Run integration tests
        run: tox run -e integration -- "${{ matrix.groups.path_to_test_file }}" --group="${{ matrix.groups.group_number }}"
```