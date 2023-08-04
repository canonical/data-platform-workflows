Workflow file: [integration_test_charm.yaml](integration_test_charm.yaml)

## Usage
### Step 1: Create your workflow
```yaml
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.
jobs:
  build:
    name: Build charm
    uses: canonical/data-platform-workflows/.github/workflows/build_charms_with_cache.yaml@v0.0.0
    permissions:
      actions: write  # Needed to manage GitHub Actions cache

  integration-test:
    name: Integration test charm
    needs:
      - build
    uses: canonical/data-platform-workflows/.github/workflows/integration_test_charm.yaml@v0.0.0
    with:
      artifact-name: ${{ needs.build.outputs.artifact-name }}
      cloud: lxd
      juju-agent-version: 0.0.0
```

### Step 2: Install plugins for pytest-operator (Poetry)
#### Step A
Add
```toml
pytest-operator-cache = {git = "https://github.com/canonical/data-platform-workflows", tag = "v0.0.0", subdirectory = "python/pytest_plugins/pytest_operator_cache"}
pytest-operator-groups = {git = "https://github.com/canonical/data-platform-workflows", tag = "v0.0.0", subdirectory = "python/pytest_plugins/pytest_operator_groups"}
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

#### Step C
If you're using tox, pass in the `CI` and `GITHUB_OUTPUT` environment variables in `tox.ini`.
```ini
[testenv:integration]
pass_env =
    {[testenv]pass_env}
    CI
    GITHUB_OUTPUT
```

### Step 3: Split test functions into groups
Groups allow a test file (Python module) to be split across parallel GitHub runners. Each group gets its own runner.

Add
```python
@pytest.mark.group(1)
```
to every test function. Replace `1` with the group number.

#### Deciding how to split tests into groups
Take a look at this Discourse post: https://discourse.charmhub.io/t/faster-ci-results-by-running-integration-tests-in-parallel/8816

### (Optional) Step 4: Add secrets
#### Step A
Pass in a string representation of a Python dict[str, str] built from multiple GitHub secrets.

Do **not** put the string into a single GitHub secret—build the string from multiple GitHub secrets so that GitHub is more likely to redact the secrets in GitHub Actions logs.
```yaml
jobs:
  # ...
  integration-test:
    # ...
    uses: canonical/data-platform-workflows/.github/workflows/integration_test_charm.yaml@v0.0.0
    with:
      # ...
    secrets:
      integration-test: |
        {
          "AWS_ACCESS_KEY_ID": "${{ secrets.AWS_ACCESS_KEY_ID }}",
          "AWS_SECRET_ACCESS_KEY": "${{ secrets.AWS_SECRET_ACCESS_KEY }}",
        }
```

Python code to verify the string format:
```python
import ast
secrets = ast.literal_eval("")
assert isinstance(secrets, dict)
for key, value in secrets.items():
    assert isinstance(key, str) and isinstance(value, str)
```

#### Step B (Poetry)
Add
```toml
pytest-github-secrets = {git = "https://github.com/canonical/data-platform-workflows", tag = "v0.0.0", subdirectory = "python/pytest_plugins/github_secrets"}
```
to your integration test dependencies in `pyproject.toml`.

#### Step C
If you're using tox, pass in the `SECRETS_FROM_GITHUB` environment variable in `tox.ini`.
```ini
[testenv:integration]
pass_env =
    {[testenv]pass_env}
    # ...
    SECRETS_FROM_GITHUB
```

#### Step D
Access the secrets from the `github_secrets` [pytest fixture](https://docs.pytest.org/en/stable/how-to/fixtures.html).
```python
def test_foo(github_secrets):
    do_something(
        access_key_id=github_secrets["AWS_ACCESS_KEY_ID"],
        secret_access_key=github_secrets["AWS_SECRET_ACCESS_KEY"],
    )
```