from typing import Any

import structlog
from eth_typing import ChecksumAddress, HexStr
from eth_utils.abi import function_signature_to_4byte_selector
from eth_utils.conversions import to_bytes
from web3.types import BlockIdentifier, EventData

from src.blockchain.contracts.base_interface import ContractInterface

logger = structlog.get_logger(__name__)

# VEBO entry points that carry packed exit requests data.
SUBMIT_FUNCTION_NAMES = ("submitReportData", "submitExitRequestsData")

SELECTOR_LENGTH = 4


class ValidatorExitBusOracleContract(ContractInterface):
    abi_path = "./interfaces/ValidatorExitBusOracle.json"

    def get_exit_data_processing_events(
        self, from_block: BlockIdentifier = 0, to_block: BlockIdentifier = "latest"
    ) -> list[EventData]:
        """Fetch all ExitDataProcessing events within the specified block range."""
        events = self.events.ExitDataProcessing.get_logs(
            from_block=from_block, to_block=to_block
        )
        logger.info(
            {
                "msg": "Fetched ExitDataProcessing events",
                "from_block": from_block,
                "to_block": to_block,
                "events_count": len(events),
            }
        )
        return events

    def _submit_selectors(self) -> dict[bytes, str]:
        """Map the 4-byte selector of every exit requests entry point to its name."""
        return {
            function_signature_to_4byte_selector(
                self.get_function_by_name(name).signature
            ): name
            for name in SUBMIT_FUNCTION_NAMES
        }

    def find_exit_requests_calls(
        self, input_data: HexStr
    ) -> list[tuple[str, dict[str, Any]]]:
        """
        Find every exit requests submission inside a transaction's calldata.

        Oracle members submit reports either directly to VEBO or through a
        forwarder contract (each member owns an `execute(address,bytes)` proxy on
        Hoodi), so the VEBO call can sit at any offset inside the outer calldata.
        Scanning for the known selectors instead of decoding the outer call keeps
        the bot independent of the submission path and of the wrapper's ABI.

        A hit is only a candidate: an arbitrary 4-byte window may coincide with a
        selector, so the caller must confirm the payload against the
        `exitRequestsHash` of the ExitDataProcessing event before acting on it.

        Returns:
            List of (function_name, decoded_params), ordered by calldata offset.
        """
        calldata = to_bytes(hexstr=input_data)
        selectors = self._submit_selectors()
        calls: list[tuple[str, dict[str, Any]]] = []

        for offset in range(len(calldata) - SELECTOR_LENGTH + 1):
            if calldata[offset : offset + SELECTOR_LENGTH] not in selectors:
                continue
            try:
                func, params = self.decode_function_input(
                    self.w3.to_hex(calldata[offset:])
                )
            except Exception as e:  # noqa: BLE001 - probing arbitrary offsets
                logger.debug(
                    {
                        "msg": "Selector match did not decode, skipping",
                        "offset": offset,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    }
                )
                continue
            calls.append((func.fn_name, params))

        logger.info(
            {
                "msg": "Scanned transaction calldata for exit requests submissions",
                "calldata_length": len(calldata),
                "candidates": [name for name, _ in calls],
            }
        )
        return calls

    def trigger_exits(
        self,
        exits_data: bytes,
        data_format: int,
        exit_data_indexes: list[int],
        refund_recipient: ChecksumAddress,
    ):
        """
        Trigger exits for validators specified by exit data indexes.

        This method builds a transaction to trigger validator exits. The actual exit messages
        will be sent to the Consensus Layer for the specified validators.

        Note: This function is payable and requires sending ETH for withdrawal request fees.
        The value must be passed separately to the transaction.send() method.

        Args:
            exits_data: Packed exit requests data (bytes)
            data_format: Data format identifier (usually 1 for DATA_FORMAT_LIST)
            exit_data_indexes: List of validator indexes to exit from the packed data
            refund_recipient: Address to receive any refund

        Returns:
            ContractFunction that can be executed or passed to transaction utilities

        Example:
            >>> vebo = w3.lido.validator_exit_bus_oracle
            >>> withdrawal_vault = w3.lido.withdrawal_vault
            >>> fee = withdrawal_vault.get_withdrawal_request_fee()
            >>> total_fee = fee * len(exit_data_indexes)
            >>> tx_function = vebo.trigger_exits(
            ...     exits_data=exit_requests_bytes,
            ...     data_format=1,
            ...     exit_data_indexes=[0, 1, 2],
            ...     refund_recipient=Web3.to_checksum_address("0x...")
            ... )
            >>> # Execute transaction with value
            >>> w3.transaction.send(tx_function, timeout_in_blocks=10, value=total_fee)
        """
        logger.info(
            {
                "msg": "Preparing triggerExits transaction",
                "data_format": data_format,
                "exit_data_indexes_count": len(exit_data_indexes),
                "exit_data_indexes": exit_data_indexes,
                "data_length": len(exits_data),
                "refund_recipient": refund_recipient,
            }
        )

        # Build the exitsData struct according to the ABI
        exits_data_struct = {"data": exits_data, "dataFormat": data_format}

        # Build and return the contract function
        return self.functions.triggerExits(
            exits_data_struct, exit_data_indexes, refund_recipient
        )
