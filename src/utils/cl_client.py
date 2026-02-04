from typing import Any, Optional
from urllib.parse import urljoin

import requests
import structlog
from eth_typing import HexStr

logger = structlog.get_logger(__name__)


class CLClient:
    def __init__(self, url: str):
        self.url = url.rstrip("/") + "/"

    @staticmethod
    def _ensure_0x_prefix(pubkey: HexStr) -> str:
        """Ensure pubkey has 0x prefix for API calls."""
        if not pubkey.startswith("0x"):
            return f"0x{pubkey}"
        return pubkey

    def get_validators_by_indexes(self) -> dict[int, HexStr]:
        validators = self.get_all_validators()
        return {
            int(val["index"]): HexStr(val["validator"]["pubkey"]) for val in validators
        }

    def get_all_validators(self) -> list[dict[str, Any]]:
        response = requests.get(
            urljoin(self.url, "eth/v1/beacon/states/head/validators"), timeout=60
        )
        response.raise_for_status()
        return response.json()["data"]

    def get_validator_index_by_pubkey(self, pub_key: HexStr) -> int:
        pubkey_with_prefix = self._ensure_0x_prefix(pub_key)
        response = requests.get(
            urljoin(
                self.url, f"eth/v1/beacon/states/head/validators/{pubkey_with_prefix}"
            ),
            timeout=10,
        )
        response.raise_for_status()

        data = response.json()

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
            response = requests.get(
                urljoin(
                    self.url,
                    f"eth/v1/beacon/states/head/validators/{pubkey_with_prefix}",
                ),
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

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
            logger.error(
                {
                    "msg": "Failed to get validator from CL",
                    "pubkey": pub_key,
                    "error": str(e),
                    "cl_url": self.url,
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
