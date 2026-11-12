"""Container health probe: exits 0 when the health server of the bot answers 2xx."""

import os
import sys
import urllib.request

# Below the 3 second timeout of the Docker HEALTHCHECK, so the probe reports the failure itself.
TIMEOUT_SECONDS = 2


def probe(url: str, timeout: float = TIMEOUT_SECONDS) -> int:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return 0 if 200 <= response.status < 300 else 1
    except OSError as error:
        print(f"Healthcheck failed: {error}", file=sys.stderr)
        return 1


def main() -> int:
    port = os.getenv("SERVER_PORT", "9010")
    return probe(f"http://127.0.0.1:{port}/health")


if __name__ == "__main__":
    sys.exit(main())
