import os
import re


def split_endpoints(value: str | None) -> list[str]:
    """Split a list of URLs written with commas, spaces or one URL per line."""
    return [item for item in re.split(r"[,\s]+", value or "") if item]


def from_file_or_env(env_name: str) -> str | None:
    """Return the content of the file named by `<env_name>_FILE` or, when it is not set, the value of `env_name`.

    The file form is for secrets mounted one per file. The file is read once, at startup, so a changed secret
    takes effect only after a restart: the bot must not change its key or its endpoints in the middle of a cycle.
    Trailing whitespace of the file is dropped; an empty file gives an empty string, which the caller treats
    like an unset variable.
    """
    filepath_env = f"{env_name}_FILE"
    filepath = os.getenv(filepath_env)

    if not filepath:
        return os.getenv(env_name)

    try:
        with open(filepath, encoding="utf-8") as file:
            return file.read().rstrip()
    except OSError as error:
        raise ValueError(
            f"{filepath_env} points to a file that cannot be read: {error}. "
            "Fix or remove the variable."
        ) from error
    except UnicodeDecodeError:
        # No details from the decoder and no chained cause: both would quote bytes of the secret in the traceback.
        raise ValueError(
            f"{filepath_env} points to {filepath}, which is not UTF-8 text. "
            "Fix or remove the variable."
        ) from None
