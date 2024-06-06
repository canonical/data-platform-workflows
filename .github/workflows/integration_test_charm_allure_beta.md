[Allure Report](https://allurereport.org/) for [integration_test_charm.yaml](integration_test_charm.md)

## Usage
> [!WARNING]
> This feature is in beta and **not part of the public interface**. It is subject to breaking changes or removal on a patch version bump.

1. `poetry add --group integration allure-pytest`
2. Add
```toml
allure-pytest-collection-report = {git = "https://github.com/canonical/data-platform-workflows", tag = "v0.0.0", subdirectory = "python/pytest_plugins/allure_pytest_collection_report"}
```
to your integration test dependencies in `pyproject.toml`.
3. Set `_beta_allure_report: true` for **one** instance of `integration_test_charm.yaml`. If `integration_test_charm.yaml` is called with a matrix, `_beta_allure_report` can only be `true` for one combination of the matrix.
4. Add permission to `integration_test_charm.yaml` job and all calling workflows
```yaml
    permissions:
      contents: write  # Needed for Allure Report beta
```
5. Create gh pages branch
https://github.com/canonical/data-platform-workflows/blob/5a2c81678ff8733345875235e579d0b1fffbc894/.github/workflows/integration_test_charm.yaml#L363-L371
6. Enable gh pages publishing at https://github.com/canonical/mysql-router-k8s-operator/settings/pages (replace `mysql-router-k8s-operator` with repository name)
    ![gh-pages](https://github.com/canonical/data-platform-workflows/assets/115640263/6ee80a1e-f75b-4d67-b11f-977358c32847)

Example for 1, 3-4: https://github.com/canonical/mysql-router-k8s-operator/pull/198

Example for 2:
