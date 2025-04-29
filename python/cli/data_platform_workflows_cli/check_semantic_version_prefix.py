import os
import re


def check(message: str, /, *, message_type="commit message") -> str:
    """Check that message begins with valid semantic version prefix and return prefix"""
    error_message = f"""{message_type[0].upper() + message_type[1:]} must contain prefix to increment semantic version

For backwards-incompatible changes to the public API, use 'breaking:' prefix
For backwards-compatible changes to the public API, use 'compatible:' prefix
For changes that do not affect the public API, use 'patch:' prefix
More info: https://semver.org/

An optional scope in parentheses may be included in the prefix. For example: 'breaking(kubernetes):'
Inside the parentheses, these characters are not allowed: `():`
    
Got invalid {message_type}: {repr(message)}
"""
    match = re.match(r"(?P<prefix>[^():]+)(?:\([^():]+\))?:", message)
    if not match:
        raise ValueError(error_message)
    prefix = match.group("prefix")
    if prefix not in ("breaking", "compatible", "patch"):
        raise ValueError(error_message)
    return prefix


def check_pr_title():
    check(os.environ["TITLE"], message_type="PR title")
