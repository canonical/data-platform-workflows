"""Check semantic version prefix

Args:
    Environment variable "MESSAGE": Message that should begin with semantic version prefix

Raises:
    PrefixValueError: If semantic version prefix is missing or invalid
"""

import os


class PrefixValueError(ValueError):
    def __init__(self, message_: str):
        super().__init__(
            f"Message does not contain valid semantic version prefix (see CONTRIBUTING.md). {message_=}"
        )


message = os.environ["MESSAGE"]
if ":" not in message:
    raise PrefixValueError(message)
prefix = message.split(":")[0]
for valid_prefix in ["patch", "compatible", "breaking"]:
    if prefix.startswith(valid_prefix):
        break
else:
    raise PrefixValueError(message)
