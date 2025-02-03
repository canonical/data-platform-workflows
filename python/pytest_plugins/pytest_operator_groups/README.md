> [!WARNING]
> `pytest-operator-groups` is **deprecated**. Migration instructions: [integration_test_charm_deprecation_notice.md](../../../.github/workflows/integration_test_charm_deprecation_notice.md)

Run integration tests on parallel GitHub runners

Usage: [integration_test_charm.md](../../../.github/workflows/integration_test_charm.md)

By default, [pytest-operator](https://github.com/charmed-kubernetes/pytest-operator) runs each test file (Python module) in a separate Juju model. Usually, on GitHub, each integration test file is run in parallel (on separate runners).

This plugin allows further parallelization—an individual test file can be split into multiple groups. Each group can run on a separate GitHub runner.
