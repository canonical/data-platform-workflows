# Deprecation notice

## Components that are deprecated
These components are deprecated & will be removed in a future release
- integration_test_charm.yaml
- python/pytest_plugins/pytest_operator_cache
- python/pytest_plugins/pytest_operator_groups
- python/pytest_plugins/allure_pytest_collection_report
- python/pytest_plugins/github_secrets
- python/pytest_plugins/microceph

## Migration instructions
### integration_test_charm.yaml
Use `charmcraft test`: https://canonical-charmcraft.readthedocs-hosted.com/en/stable/reference/commands/test/

And concierge: https://github.com/jnsgruk/concierge

Example: https://github.com/canonical/mysql-router-k8s-operator/pull/379

### python/pytest_plugins/pytest_operator_cache
In integration tests, instead of calling `ops_test.build_charm`, assume the *.charm file exists and fail the test if the *.charm file is missing. The charm should be built outside of the test

When running tests locally, if you would like the charm to be re-built each time the tests are run, consider using [charmcraftcache](https://github.com/canonical/charmcraftcache) (e.g. `ccc pack`) before the `pytest` command (e.g. in spread.yaml). If you have multiple charms, `ccc pack` needs to be called once for each charm

Example: https://github.com/canonical/mysql-router-k8s-operator/pull/379

### python/pytest_plugins/pytest_operator_groups
Use separate python files (modules) for each test group, or configure different spread (`charmcraft test`) tasks for each group (e.g. using pytest markers)

### python/pytest_plugins/allure_pytest_collection_report
Use https://github.com/canonical/allure-pytest-default-results instead

Example: https://github.com/canonical/mysql-router-k8s-operator/pull/379

### python/pytest_plugins/github_secrets
Use normal GitHub Actions syntax (https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions#using-secrets-in-a-workflow) to pass secrets as environment variables where `charmcraft test` is called

### python/pytest_plugins/microceph
Set up microceph using spread (`charmcraft test`) or create a pytest fixture to set up microceph
