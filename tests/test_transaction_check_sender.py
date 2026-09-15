"""Tests that the local transaction check calls as the bot's own account.

Without an explicit sender the node bills an eth_call to the zero address, so any call
carrying a value fails on that address's balance instead of on the contract's own logic -
and since send() runs only after check() passes, the bot could never submit at all.
"""

from unittest.mock import Mock

import pytest
from web3.types import Wei

from src import variables
from src.blockchain.web3_extentions.transaction import TransactionUtils

ACCOUNT_ADDRESS = "0x8943545177806ED17B9F23F0a21ee5948eCaa776"


@pytest.fixture
def transaction():
    tx = Mock()
    tx.call = Mock(return_value=None)
    return tx


@pytest.fixture
def with_account(monkeypatch):
    monkeypatch.setattr(variables, "ACCOUNT", Mock(address=ACCOUNT_ADDRESS))


@pytest.fixture
def without_account(monkeypatch):
    monkeypatch.setattr(variables, "ACCOUNT", None)


class TestCheckSender:
    def test_passes_account_as_sender(self, transaction, with_account):
        assert TransactionUtils.check(transaction, value=Wei(3)) is True

        params = transaction.call.call_args[0][0]
        assert params["from"] == ACCOUNT_ADDRESS
        assert params["value"] == Wei(3)

    def test_passes_sender_even_without_value(self, transaction, with_account):
        assert TransactionUtils.check(transaction) is True

        params = transaction.call.call_args[0][0]
        assert params["from"] == ACCOUNT_ADDRESS
        assert "value" not in params

    def test_omits_sender_when_no_account(self, transaction, without_account):
        assert TransactionUtils.check(transaction, value=Wei(3)) is True

        params = transaction.call.call_args[0][0]
        assert "from" not in params
        assert params["value"] == Wei(3)

    def test_reports_failure_when_the_call_reverts(self, transaction, with_account):
        transaction.call.side_effect = ValueError("insufficient funds")

        assert TransactionUtils.check(transaction, value=Wei(3)) is False
