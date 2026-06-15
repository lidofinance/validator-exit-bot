"""Tests for new staking module support (ExitPenalties-based, non-NOR)."""

from unittest.mock import Mock

from eth_typing import ChecksumAddress, HexStr

from src.blockchain.contracts.exit_penalties import ExitPenaltiesContract
from src.blockchain.web3_extentions.lido_contracts import ZERO_ADDRESS, LidoContracts
from src.trigger_exit_bot import TriggerExitBot

PUBKEY = HexStr("0x" + "ab" * 48)
MODULE_ID = 3
NODE_OP_ID = 7
EXIT_PENALTIES_ADDR = ChecksumAddress("0x" + "12" * 20)
MODULE_ADDR = ChecksumAddress("0x" + "aa" * 20)
DATA_KEY = "deadbeef" * 8


def _make_bot(exit_penalties_map=None, nor_map=None):
    w3 = Mock()
    w3.lido.exit_penalties_map = exit_penalties_map or {}
    w3.lido.node_operator_registry_map = nor_map or {}
    bot = TriggerExitBot.__new__(TriggerExitBot)
    bot.w3 = w3
    bot.cl_client = Mock()
    bot.validators_map = {}
    bot.data_format_map = {}
    bot.data_bytes_map = {}
    bot.vebo = Mock()
    bot.transaction_utils = Mock()
    bot._trigger_exits_transaction = Mock()
    return bot


def _make_validator(pubkey=PUBKEY, module_id=MODULE_ID, node_op_id=NODE_OP_ID):
    return {
        "pubkey": pubkey,
        "moduleId": module_id,
        "nodeOpId": node_op_id,
        "valIndex": 0,
        "index": 0,
    }


def _seed_bot_state(bot, validators):
    bot.validators_map[DATA_KEY] = list(validators)
    bot.data_format_map[DATA_KEY] = 1
    bot.data_bytes_map[DATA_KEY] = b"\x00" * 64


class TestExitPenaltiesContractIsApplicable:
    def _mock_contract(self, delay_fee_is_value: bool):
        mock = Mock()
        mock.functions.getExitPenaltyInfo.return_value.call.return_value = (
            (0, delay_fee_is_value),  # delayFee: (value, isValue)
            (0, False),               # strikesPenalty
            (0, False),               # elWithdrawalRequestFee
        )
        return mock

    def test_true_when_delay_fee_is_set(self):
        mock_self = self._mock_contract(True)
        assert ExitPenaltiesContract.is_exit_delay_applicable(mock_self, NODE_OP_ID, PUBKEY) is True

    def test_false_when_delay_fee_not_set(self):
        mock_self = self._mock_contract(False)
        assert ExitPenaltiesContract.is_exit_delay_applicable(mock_self, NODE_OP_ID, PUBKEY) is False

    def test_pubkey_passed_as_bytes_without_0x(self):
        mock_self = self._mock_contract(False)
        ExitPenaltiesContract.is_exit_delay_applicable(mock_self, NODE_OP_ID, "0xabcd")
        called_pubkey = mock_self.functions.getExitPenaltyInfo.call_args[0][1]
        assert isinstance(called_pubkey, bytes)
        assert called_pubkey == bytes.fromhex("abcd")

    def test_pubkey_with_and_without_0x_produce_same_bytes(self):
        mock_self = self._mock_contract(False)
        ExitPenaltiesContract.is_exit_delay_applicable(mock_self, NODE_OP_ID, "0xabcd")
        ExitPenaltiesContract.is_exit_delay_applicable(mock_self, NODE_OP_ID, "abcd")
        calls = mock_self.functions.getExitPenaltyInfo.call_args_list
        assert calls[0][0][1] == calls[1][0][1]


class TestProbeExitPenalties:
    def _make_instance(self):
        instance = Mock(spec=LidoContracts)
        instance.w3 = Mock()
        return instance

    def test_returns_address_for_new_style_module(self):
        instance = self._make_instance()
        instance.w3.eth.contract.return_value.exit_penalties.return_value = EXIT_PENALTIES_ADDR

        result = LidoContracts._probe_exit_penalties(instance, MODULE_ADDR)

        assert result == EXIT_PENALTIES_ADDR

    def test_returns_none_when_call_reverts(self):
        instance = self._make_instance()
        instance.w3.eth.contract.return_value.exit_penalties.side_effect = Exception(
            "execution reverted"
        )

        result = LidoContracts._probe_exit_penalties(instance, MODULE_ADDR)

        assert result is None

    def test_returns_none_for_zero_address(self):
        instance = self._make_instance()
        instance.w3.eth.contract.return_value.exit_penalties.return_value = ZERO_ADDRESS

        result = LidoContracts._probe_exit_penalties(instance, MODULE_ADDR)

        assert result is None


class TestCheckAndTriggerExitsNewModule:
    def test_triggers_exit_when_delay_fee_is_set(self):
        mock_exit_penalties = Mock()
        mock_exit_penalties.is_exit_delay_applicable.return_value = True

        bot = _make_bot(exit_penalties_map={MODULE_ID: mock_exit_penalties})
        bot.cl_client.is_validator_exited.return_value = (False, False)
        _seed_bot_state(bot, [_make_validator()])

        bot._check_and_trigger_exits(DATA_KEY)

        bot._trigger_exits_transaction.assert_called_once()
        _, _, validators_to_trigger = bot._trigger_exits_transaction.call_args[0]
        assert len(validators_to_trigger) == 1

    def test_no_trigger_when_delay_fee_not_set(self):
        mock_exit_penalties = Mock()
        mock_exit_penalties.is_exit_delay_applicable.return_value = False

        bot = _make_bot(exit_penalties_map={MODULE_ID: mock_exit_penalties})
        bot.cl_client.is_validator_exited.return_value = (False, False)
        _seed_bot_state(bot, [_make_validator()])

        bot._check_and_trigger_exits(DATA_KEY)

        bot._trigger_exits_transaction.assert_not_called()
        assert len(bot.validators_map[DATA_KEY]) == 1

    def test_nor_path_not_reached_for_new_module(self):
        mock_exit_penalties = Mock()
        mock_exit_penalties.is_exit_delay_applicable.return_value = False
        mock_nor = Mock()

        bot = _make_bot(
            exit_penalties_map={MODULE_ID: mock_exit_penalties},
            nor_map={MODULE_ID: mock_nor},
        )
        bot.cl_client.is_validator_exited.return_value = (False, False)
        _seed_bot_state(bot, [_make_validator()])

        bot._check_and_trigger_exits(DATA_KEY)

        mock_nor.is_validator_exiting_key_reported.assert_not_called()

    def test_unknown_module_removed_from_state(self):
        # Module registered after bot started — not in either map, remove to avoid state accumulation
        bot = _make_bot()
        bot.cl_client.is_validator_exited.return_value = (False, False)
        _seed_bot_state(bot, [_make_validator()])

        bot._check_and_trigger_exits(DATA_KEY)

        bot._trigger_exits_transaction.assert_not_called()
        assert bot.validators_map[DATA_KEY] == []

    def test_exited_validator_removed_from_state(self):
        mock_exit_penalties = Mock()

        bot = _make_bot(exit_penalties_map={MODULE_ID: mock_exit_penalties})
        bot.cl_client.is_validator_exited.return_value = (True, False)
        _seed_bot_state(bot, [_make_validator()])

        bot._check_and_trigger_exits(DATA_KEY)

        bot._trigger_exits_transaction.assert_not_called()
        mock_exit_penalties.is_exit_delay_applicable.assert_not_called()
        assert bot.validators_map[DATA_KEY] == []
