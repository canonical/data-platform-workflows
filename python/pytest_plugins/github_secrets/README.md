Access GitHub secrets from integration tests executed by [integration_test_charm.yaml](../../../.github/workflows/integration_test_charm.yaml)

Usage: [integration_test_charm.md](../../../.github/workflows/integration_test_charm.md)

Since reusable GitHub workflows do not support arbitrary secret inputs, all secrets must be encoded into a single string and passed as one secret. This plugin provides a pytest fixture that decodes the string.