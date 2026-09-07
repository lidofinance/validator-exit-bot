"""Tests for locating a VEBO exit requests submission inside a transaction.

Oracle members may submit reports directly to VEBO or through a forwarder
contract, so the submission is matched by its exit requests hash rather than by
decoding the outermost call.
"""

from typing import Any, cast
from unittest.mock import Mock

from eth_abi.abi import encode as abi_encode
from eth_typing import HexStr
from web3 import Web3

from src.blockchain.contracts.validator_exit_bus_oracle import (
    ValidatorExitBusOracleContract,
)
from src.trigger_exit_bot import TriggerExitBot, _exit_requests_hash

VEBO_ADDRESS = Web3.to_checksum_address("0x" + "11" * 20)
FORWARDER_ADDRESS = Web3.to_checksum_address("0x" + "22" * 20)

# 3 bytes moduleId | 5 bytes nodeOpId | 8 bytes valIndex | 8 bytes keyIndex | 48 bytes pubkey
CSM_V2_REQUEST = (
    (6).to_bytes(3, "big")
    + (1).to_bytes(5, "big")
    + (42).to_bytes(8, "big")
    + (0).to_bytes(8, "big")
    + b"\xab" * 48
)
DATA_FORMAT_WITH_KEY_INDEX = 2


def _vebo() -> ValidatorExitBusOracleContract:
    """VEBO contract bound to a provider-less Web3: encoding needs no node."""
    return cast(
        ValidatorExitBusOracleContract,
        Web3().eth.contract(
            address=VEBO_ADDRESS,
            ContractFactoryClass=ValidatorExitBusOracleContract,
        ),
    )


def _make_bot(vebo: ValidatorExitBusOracleContract) -> Any:
    bot = TriggerExitBot.__new__(TriggerExitBot)
    bot.w3 = Mock()
    bot.cl_client = Mock()
    bot.validators_map = {}
    bot.data_format_map = {}
    bot.data_bytes_map = {}
    bot.vebo = vebo
    bot.transaction_utils = Mock()
    return bot


def _submit_report_data_calldata(
    vebo: ValidatorExitBusOracleContract, data: bytes, data_format: int
) -> HexStr:
    return vebo.encode_abi(
        "submitReportData",
        args=[
            {
                "consensusVersion": 5,
                "refSlot": 3_875_007,
                "requestsCount": len(data) // 72,
                "dataFormat": data_format,
                "data": data,
            },
            4,
        ],
    )


def _submit_exit_requests_data_calldata(
    vebo: ValidatorExitBusOracleContract, data: bytes, data_format: int
) -> HexStr:
    return vebo.encode_abi(
        "submitExitRequestsData",
        args=[{"data": data, "dataFormat": data_format}],
    )


def _wrap_in_forwarder(inner_calldata: HexStr) -> HexStr:
    """Wrap calldata the way an oracle member proxy's `execute(address,bytes)` does."""
    selector = Web3.keccak(text="execute(address,bytes)")[:4]
    args = abi_encode(
        ["address", "bytes"], [VEBO_ADDRESS, Web3.to_bytes(hexstr=inner_calldata)]
    )
    return Web3.to_hex(selector + args)


class TestDecodeTransactionInput:
    def test_direct_submit_report_data(self):
        vebo = _vebo()
        bot = _make_bot(vebo)
        calldata = _submit_report_data_calldata(
            vebo, CSM_V2_REQUEST, DATA_FORMAT_WITH_KEY_INDEX
        )

        name, params = bot._decode_transaction_input(
            calldata,
            _exit_requests_hash(CSM_V2_REQUEST, DATA_FORMAT_WITH_KEY_INDEX),
        )

        assert name == "submitReportData"
        assert params["data"]["data"] == CSM_V2_REQUEST

    def test_direct_submit_exit_requests_data(self):
        vebo = _vebo()
        bot = _make_bot(vebo)
        calldata = _submit_exit_requests_data_calldata(
            vebo, CSM_V2_REQUEST, DATA_FORMAT_WITH_KEY_INDEX
        )

        name, params = bot._decode_transaction_input(
            calldata,
            _exit_requests_hash(CSM_V2_REQUEST, DATA_FORMAT_WITH_KEY_INDEX),
        )

        assert name == "submitExitRequestsData"
        assert params["request"]["data"] == CSM_V2_REQUEST

    def test_submission_wrapped_in_forwarder(self):
        vebo = _vebo()
        bot = _make_bot(vebo)
        calldata = _wrap_in_forwarder(
            _submit_report_data_calldata(
                vebo, CSM_V2_REQUEST, DATA_FORMAT_WITH_KEY_INDEX
            )
        )

        name, params = bot._decode_transaction_input(
            calldata,
            _exit_requests_hash(CSM_V2_REQUEST, DATA_FORMAT_WITH_KEY_INDEX),
        )

        assert name == "submitReportData"
        assert params["data"]["data"] == CSM_V2_REQUEST

    def test_doubly_wrapped_submission(self):
        vebo = _vebo()
        bot = _make_bot(vebo)
        calldata = _wrap_in_forwarder(
            _wrap_in_forwarder(
                _submit_report_data_calldata(
                    vebo, CSM_V2_REQUEST, DATA_FORMAT_WITH_KEY_INDEX
                )
            )
        )

        name, _ = bot._decode_transaction_input(
            calldata,
            _exit_requests_hash(CSM_V2_REQUEST, DATA_FORMAT_WITH_KEY_INDEX),
        )

        assert name == "submitReportData"

    def test_picks_the_submission_matching_the_event_hash(self):
        vebo = _vebo()
        bot = _make_bot(vebo)
        other_request = CSM_V2_REQUEST[:16] + b"\x00" * 8 + b"\xcd" * 48
        # Two submissions concatenated: only one belongs to the processed event.
        calldata = HexStr(
            _submit_report_data_calldata(
                vebo, other_request, DATA_FORMAT_WITH_KEY_INDEX
            )
            + _submit_report_data_calldata(
                vebo, CSM_V2_REQUEST, DATA_FORMAT_WITH_KEY_INDEX
            ).removeprefix("0x")
        )

        _, params = bot._decode_transaction_input(
            calldata,
            _exit_requests_hash(CSM_V2_REQUEST, DATA_FORMAT_WITH_KEY_INDEX),
        )

        assert params["data"]["data"] == CSM_V2_REQUEST

    def test_returns_none_when_no_submission_matches(self):
        vebo = _vebo()
        bot = _make_bot(vebo)
        calldata = _wrap_in_forwarder(
            _submit_report_data_calldata(
                vebo, CSM_V2_REQUEST, DATA_FORMAT_WITH_KEY_INDEX
            )
        )

        assert bot._decode_transaction_input(calldata, b"\x00" * 32) == (None, None)

    def test_returns_none_for_unrelated_transaction(self):
        vebo = _vebo()
        bot = _make_bot(vebo)

        assert bot._decode_transaction_input(
            Web3.to_hex(b"\xde\xad\xbe\xef" * 32),
            _exit_requests_hash(CSM_V2_REQUEST, DATA_FORMAT_WITH_KEY_INDEX),
        ) == (None, None)


class TestExitRequestsHash:
    def test_matches_onchain_formula(self):
        """VEBO computes `keccak256(abi.encode(data, dataFormat))`."""
        assert _exit_requests_hash(CSM_V2_REQUEST, 2) == Web3.keccak(
            abi_encode(["bytes", "uint256"], [CSM_V2_REQUEST, 2])
        )

    def test_reproduces_hoodi_empty_report_hash(self):
        """Observed on Hoodi: an empty format-2 report hashes to this value."""
        assert (
            _exit_requests_hash(b"", 2).hex()
            == "02d422a7d569da74f62075d0c54f39775363cc5c3be3c344c785b78975910af9"
        )
