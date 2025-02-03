import ast
import logging
import os
import warnings

import pytest

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def github_secrets() -> dict[str, str]:
    warnings.warn(
        # "\n::warning::" for https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/workflow-commands-for-github-actions#setting-a-warning-message
        "\n::warning::The `pytest-github-secrets` plugin is deprecated. Follow the migration instructions here: "
        "https://github.com/canonical/data-platform-workflows/blob/v29.1.0/.github/workflows/integration_test_charm_deprecation_notice.md",
        DeprecationWarning,
    )
    # Note: Exceptions are raised directly to avoid leaking secrets in stderr
    secrets_str = os.environ.get("SECRETS_FROM_GITHUB")
    if secrets_str is None:
        raise Exception("`SECRETS_FROM_GITHUB` environment variable not set")
    elif secrets_str == "":
        raise Exception("`SECRETS_FROM_GITHUB` is empty string")
    try:
        secrets = ast.literal_eval(secrets_str)
    except (SyntaxError, ValueError):
        secrets = None
    if not isinstance(secrets, dict):
        raise Exception(
            "Invalid format for `SECRETS_FROM_GITHUB`—must be a (string representation of a) Python dictionary"
        )
    for secret_name, secret in secrets.items():
        if not (isinstance(secret_name, str) and isinstance(secret, str)):
            raise Exception(
                "Invalid format for `SECRETS_FROM_GITHUB`—must be a Python dict[str, str]"
            )
    if set(secrets.values()) == {""}:
        logger.warning(
            "No GitHub secrets available: skipping tests that require GitHub secrets"
        )
        pytest.skip("Running on fork: no access to GitHub secrets")
    return secrets
