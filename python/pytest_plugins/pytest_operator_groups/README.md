Run integration tests on parallel GitHub runners

By default, [pytest-operator](https://github.com/charmed-kubernetes/pytest-operator) runs each test file (Python module) in a separate Juju model. Usually, on GitHub, each integration test file is run in parallel (on separate runners).

This plugin allows further parallelization—an individual test file can be split into multiple groups. Each group can run on a separate GitHub runner.

## Usage

### Installation
Add
```
git+https://github.com/canonical/data-platform-workflows@v2#subdirectory=python/pytest_plugins/pytest_operator_groups
```
to your integration test Python dependencies.

If your dependencies are managed with tox, replace `#` with `\#` (to escape comment syntax).

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
saves a JSON-encoded string to `GITHUB_OUTPUT`. Example:
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
        run: tox run -e integration -- "${{ matrix.groups.path_to_test_file }}" --group ${{ matrix.groups.group_number }}
```