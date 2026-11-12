from collections.abc import Callable
from typing import Any, Optional
from urllib.parse import urljoin

import requests
import structlog
from eth_typing import HexStr

from src.utils.build_info import user_agent as default_user_agent

logger = structlog.get_logger(__name__)

# The endpoint refused or throttled this client: it said nothing about the validator.
ENDPOINT_FAILURE_STATUSES = frozenset({401, 403, 408, 429})

# The statuses of the Beacon API. Any other text is a malformed answer: read as a status,
# it would count as "not exited" and lead to an exit trigger.
VALIDATOR_STATUSES = frozenset(
    {
        "pending_initialized",
        "pending_queued",
        "active_ongoing",
        "active_exiting",
        "active_slashed",
        "exited_unslashed",
        "exited_slashed",
        "withdrawal_possible",
        "withdrawal_done",
    }
)


def _is_endpoint_failure(status_code: int) -> bool:
    return status_code >= 500 or status_code in ENDPOINT_FAILURE_STATUSES


def _is_validators_list(data: Any) -> bool:
    return isinstance(data, list)


def _is_validator_with_index(data: Any) -> bool:
    return isinstance(data, dict) and str(data.get("index")).isdecimal()


def _is_validator_with_status(data: Any) -> bool:
    if not isinstance(data, dict):
        return False
    status = data.get("status")
    return isinstance(status, str) and status.lower() in VALIDATOR_STATUSES


class CLClient:
    def __init__(self, urls: str | list[str], user_agent: Optional[str] = None):
        if isinstance(urls, str):
            urls = [urls]
        self.urls = [url.strip().rstrip("/") + "/" for url in urls if url.strip()]
        if not self.urls:
            raise ValueError("At least one Consensus Layer URL is required")

        self._session = requests.Session()
        self._session.headers["User-Agent"] = user_agent or default_user_agent()

    @staticmethod
    def _ensure_0x_prefix(pubkey: HexStr) -> str:
        """Ensure pubkey has 0x prefix for API calls."""
        if not pubkey.startswith("0x"):
            return f"0x{pubkey}"
        return pubkey

    def _get(
        self, path: str, timeout: int, is_valid_data: Callable[[Any], bool]
    ) -> dict[str, Any]:
        """
        Ask the endpoints in the configured order and return the first answer.

        An endpoint that gives no answer (network error, 5xx, refused client,
        malformed body) is skipped. An answer about the request itself is final,
        because an error must never turn into a validator status: a 404, a 400 or
        another 4xx is raised at once without asking the remaining endpoints, and
        a body with "error" is returned for the caller to handle.

        When no endpoint answered, the error of the last one is raised.
        """
        last_error: Exception = RuntimeError("No Consensus Layer endpoint was called")

        for index, base_url in enumerate(self.urls):
            status_code: int | None = None
            try:
                response = self._session.get(urljoin(base_url, path), timeout=timeout)
                response.raise_for_status()
                body = response.json()
            except requests.HTTPError as error:
                if error.response is not None:
                    status_code = error.response.status_code
                if status_code is not None and not _is_endpoint_failure(status_code):
                    logger.warning(
                        {
                            "msg": "CL endpoint rejected the request",
                            "endpoint": index,
                            "status_code": status_code,
                        }
                    )
                    raise
                last_error = error
            except requests.RequestException as error:
                last_error = error
            else:
                if isinstance(body, dict) and (
                    body.get("error") or is_valid_data(body.get("data"))
                ):
                    return body
                status_code = response.status_code
                last_error = ValueError("Malformed response from the CL API")

            is_last = index == len(self.urls) - 1
            outcome = "no endpoint left" if is_last else "trying the next one"
            logger.warning(
                {
                    "msg": f"CL endpoint failed, {outcome}",
                    "endpoint": index,
                    "error_type": type(last_error).__name__,
                    "status_code": status_code,
                }
            )

        raise last_error

    def get_validators_by_indexes(self) -> dict[int, HexStr]:
        validators = self.get_all_validators()
        return {
            int(val["index"]): HexStr(val["validator"]["pubkey"]) for val in validators
        }

    def get_all_validators(self) -> list[dict[str, Any]]:
        body = self._get(
            "eth/v1/beacon/states/head/validators",
            timeout=60,
            is_valid_data=_is_validators_list,
        )
        if body.get("error"):
            raise ValueError("CL API returned an error for the validators list")
        return body["data"]

    def get_validator_index_by_pubkey(self, pub_key: HexStr) -> int:
        pubkey_with_prefix = self._ensure_0x_prefix(pub_key)
        data = self._get(
            f"eth/v1/beacon/states/head/validators/{pubkey_with_prefix}",
            timeout=10,
            is_valid_data=_is_validator_with_index,
        )

        if data.get("error"):
            raise ValueError(f"Validator not found in CL for public key: {pub_key}")

        return int(data["data"]["index"])

    def get_validator_by_pubkey(self, pub_key: HexStr) -> Optional[dict]:
        """
        Get validator information by public key.

        Returns None if validator not found, otherwise returns validator data dict.
        """
        try:
            pubkey_with_prefix = self._ensure_0x_prefix(pub_key)
            data = self._get(
                f"eth/v1/beacon/states/head/validators/{pubkey_with_prefix}",
                timeout=10,
                is_valid_data=_is_validator_with_status,
            )

            if data.get("error"):
                logger.warning(
                    {
                        "msg": "CL API returned error for validator",
                        "pubkey": pub_key,
                        "error": data.get("error"),
                    }
                )
                return None

            return data.get("data")
        except Exception as e:
            # Neither the endpoint URL nor the error text: both can carry a provider key.
            logger.error(
                {
                    "msg": "Failed to get validator from CL",
                    "pubkey": pub_key,
                    "error_type": type(e).__name__,
                }
            )
            return None

    def is_validator_exited(self, pub_key: HexStr) -> tuple[bool, bool]:
        """
        Check if a validator has exited or is in the process of exiting.

        Returns:
            Tuple of (is_exited, is_error):
            - is_exited: True if validator is in one of the exit/exiting states
            - is_error: True if there was an error fetching validator data from CL

        Exited states include:
        - active_exiting (exit triggered, waiting for exit epoch)
        - exited_unslashed (has exited)
        - exited_slashed (slashed and exited)
        - withdrawal_possible (can withdraw)
        - withdrawal_done (fully withdrawn)
        """
        validator_data = self.get_validator_by_pubkey(pub_key)

        if validator_data is None:
            logger.error(
                {
                    "msg": "Could not get validator data from CL",
                    "pubkey": pub_key,
                }
            )
            return (False, True)

        status = validator_data.get("status", "").lower()

        exited_states = [
            "active_exiting",  # Exit has been triggered
            "exited_unslashed",  # Has exited
            "exited_slashed",  # Slashed and exited
            "withdrawal_possible",  # Can withdraw
            "withdrawal_done",  # Fully withdrawn
        ]

        is_exited = status in exited_states
        return (is_exited, False)  # (is_exited, is_error=False)
