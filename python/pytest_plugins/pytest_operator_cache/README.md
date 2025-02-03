> [!WARNING]
> `pytest-operator-cache` is **deprecated**. Migration instructions: [integration_test_charm_deprecation_notice.md](../../../.github/workflows/integration_test_charm_deprecation_notice.md)

[pytest-operator](https://github.com/charmed-kubernetes/pytest-operator) plugin that overrides `ops_test.build_charm()` to return cached *.charm file instead of building new *.charm file.

Usage: [integration_test_charm.md](../../../.github/workflows/integration_test_charm.md)
