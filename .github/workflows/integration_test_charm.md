Workflow file: [integration_test_charm.yaml](integration_test_charm.yaml)

> [!WARNING]
> This workflow is **deprecated** & will be removed in a future release. Follow the migration instructions here: [integration_test_charm_deprecation_notice.md](integration_test_charm_deprecation_notice.md)

## Usage
### Step 1: Create your workflow
```yaml
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.
jobs:
  build:
    name: Build charm
    uses: canonical/data-platform-workflows/.github/workflows/build_charm.yaml@v0.0.0
    with:
      cache: true

  integration-test:
    name: Integration
    needs:
      - build
    uses: canonical/data-platform-workflows/.github/workflows/integration_test_charm.yaml@v0.0.0
    with:
      artifact-prefix: ${{ needs.build.outputs.artifact-prefix }}
      cloud: lxd
      juju-agent-version: 0.0.0
```

### Step 2: Install plugins for pytest-operator (Poetry)
#### Step A
Add
```toml
pytest-operator-groups = {git = "https://github.com/canonical/data-platform-workflows", tag = "v0.0.0", subdirectory = "python/pytest_plugins/pytest_operator_groups"}
```
to your integration test dependencies in `pyproject.toml`.

#### Step B
If you're using tox, pass in the `CI` and `GITHUB_OUTPUT` environment variables in `tox.ini`.
```ini
[testenv:integration]
pass_env =
    {[testenv]pass_env}
    CI
    GITHUB_OUTPUT
```

### Step 3: Split test functions into groups
Groups allow a test file (Python module) to be split across parallel GitHub runners. Each group (for each file) gets its own runner.

Add
```python
@pytest.mark.group(1)
```
to every test function. Replace `1` with the group ID.

#### Deciding how to split tests into groups
Take a look at this Discourse post: https://discourse.charmhub.io/t/faster-ci-results-by-running-integration-tests-in-parallel/8816

#### (Optional) Select different runner for a test
Use a different [runs-on](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#jobsjob_idruns-on) string with
```python
@pytest.mark.runner("ubuntu-20.04")
```

For self-hosted runners, use

```python
@pytest.mark.runner(["self-hosted", "linux", "X64", "jammy", "large"])
```
> [!WARNING]
> Support for self-hosted runners is **very limited**.[^1]

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
      # GitHub appears to redact each line of a multi-line secret
      # Avoid putting `{` or `}` on a line by itself so that it doesn't get redacted in logs
      integration-test: |
        { "AWS_ACCESS_KEY_ID": "${{ secrets.AWS_ACCESS_KEY_ID }}",
          "AWS_SECRET_ACCESS_KEY": "${{ secrets.AWS_SECRET_ACCESS_KEY }}", }
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

### (Optional) Step 5: Add microceph
#### Step A
Add
```toml
pytest-microceph = {git = "https://github.com/canonical/data-platform-workflows", tag = "v0.0.0", subdirectory = "python/pytest_plugins/microceph"}
```
to your integration test dependencies in `pyproject.toml`.

#### Step B
Access the S3 connection information from the `microceph` [pytest fixture](https://docs.pytest.org/en/stable/how-to/fixtures.html).

```python
import pytest_microceph


def test_foo(microceph: pytest_microceph.ConnectionInformation):
    do_something(
        access_key_id=microceph.access_key_id,
        secret_access_key=microceph.secret_access_key,
        bucket=microceph.bucket,
    )
```

[^1]: Self-hosted runners are more subject to breaking changes, may lack feature support, and will not be tested for regressions. For troubleshooting with self-hosted runners, please [contact IS on Mattermost](https://chat.canonical.com/canonical/channels/github-actions-self-hosted-runners) before contacting the maintainers of this repository. Bug reports on GitHub-hosted runners will have higher priority—if you find a bug that is not specific to self-hosted runners, please reproduce on GitHub-hosted runners before reporting.
