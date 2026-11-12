import json
from collections.abc import Mapping
from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)

# The file in the repo holds placeholders; the Docker build fills it from the
# BUILD_VERSION, BUILD_BRANCH and BUILD_COMMIT build args.
BUILD_INFO_PATH = Path(__file__).resolve().parents[2] / "build-info.json"
BUILD_INFO_KEYS: tuple[str, ...] = ("version", "branch", "commit")
UNKNOWN = "unknown"
APP_NAME = "validator-exit-bot"


def load_build_info(path: Path | None = None) -> dict[str, str]:
    """Return version, branch and commit of this build, "unknown" where missing."""
    path = path or BUILD_INFO_PATH
    info = dict.fromkeys(BUILD_INFO_KEYS, UNKNOWN)

    try:
        with open(path, encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        return info
    except (OSError, ValueError) as error:
        logger.warning(
            {
                "msg": "Failed to read build info.",
                "path": str(path),
                "error": str(error),
            }
        )
        return info

    if not isinstance(data, dict):
        logger.warning({"msg": "Build info is not a JSON object.", "path": str(path)})
        return info

    for key in BUILD_INFO_KEYS:
        value = data.get(key)
        if value:
            info[key] = str(value)

    return info


def user_agent(info: Mapping[str, str] | None = None) -> str:
    version = (info or load_build_info())["version"]
    # An HTTP header value must be latin-1; a version from a tag name may be any text.
    if not (version.isascii() and version.isprintable()):
        version = UNKNOWN
    return f"{APP_NAME}/{version}"
