def main():
    import ast
    import os
    import sys

    # Suppress stderr—an exception could leak secrets
    sys.stderr = None

    try:
        secrets_str = os.environ.get("SECRETS")
        if secrets_str is None:
            print("`SECRETS` environment variable not set")
            exit(1)
        elif secrets_str == "":
            print("No secrets")
            exit(0)
        try:
            secrets = ast.literal_eval(secrets_str)
        except (SyntaxError, ValueError):
            secrets = None
        if not isinstance(secrets, dict):
            print(
                "Invalid format for `integration-test` secret—must be a (string representation of a) Python dictionary"
            )
            exit(1)
        for secret_name, secret in secrets.items():
            if not (isinstance(secret_name, str) and isinstance(secret, str)):
                print(
                    "Invalid format for `integration-test` secret—must be a Python dict[str, str]"
                )
                exit(1)
            # Mask secret from GitHub Actions log
            # https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#masking-a-value-in-a-log
            print(f"::add-mask::{secret}")
    except SystemExit as e:
        exit(e.code)
    except:
        # An exception could leak secrets
        print("Uncaught exception")
        exit(1)
    print(f"{len(secrets)} secrets redacted")
