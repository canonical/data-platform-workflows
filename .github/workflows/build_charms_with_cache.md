Workflow file: [build_charms_with_cache.yaml](build_charms_with_cache.yaml)

## Usage
### Step 1: Create your workflow
```yaml
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.
jobs:
  build:
    name: Build charms
    uses: canonical/data-platform-workflows/.github/workflows/build_charms_with_cache.yaml@v0.0.0
    permissions:
      actions: write  # Needed to manage GitHub Actions cache

  integration-test:
    name: Integration tests
    needs:
      - build
    steps:
      - name: Checkout
      - name: Download packed charm(s)
        uses: actions/download-artifact@v0
        with:
          name: ${{ needs.build.outputs.artifact-name }}
      - name: Run integration tests
        run: tox run -e integration
```
If any workflows call your workflow (i.e. your workflow includes `on: workflow_call`), recursively add
```yaml
permissions:
  actions: write  # Needed to manage GitHub Actions cache
```
to every calling workflow job.

### Step 2: Install plugin for pytest-operator (Poetry)
#### Step A
Add
```toml
pytest-operator-cache = {git = "https://github.com/canonical/data-platform-workflows", tag = "v0.0.0", subdirectory = "python/pytest_plugins/pytest_operator_cache"}
```
to your integration test dependencies in `pyproject.toml`.

#### Step B
Disable Poetry's parallel installation for integration test dependencies.

Example `tox.ini`:
```ini
[testenv:integration]
set_env =
    {[testenv]set_env}
    # Workaround for https://github.com/python-poetry/poetry/issues/6958
    POETRY_INSTALLER_PARALLEL = false
```

### Step 3: Pass the CI environment variable
If you're using tox, pass in the `CI` environment variable in `tox.ini`.
```ini
[testenv:integration]
pass_env =
    {[testenv]pass_env}
    CI
```
