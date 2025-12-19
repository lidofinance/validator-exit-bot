# pyright: reportTypedDictNotRequiredAccess=false

import structlog

import variables
from blockchain.constants import SLOT_TIME
from eth_account.datastructures import SignedTransaction
from eth_typing import ChecksumAddress
from metrics.metrics import TX_SEND
from web3 import Web3
from web3.contract.contract import ContractFunction
from web3.exceptions import ContractLogicError, TimeExhausted
from web3.module import Module
from web3.types import TxParams, Wei

logger = structlog.get_logger(__name__)


class TransactionUtils(Module):
    w3: Web3

    @staticmethod
    def check(transaction: ContractFunction, value: Wei = Wei(0)) -> bool:
        try:
            call_params = TxParams({})
            if value > 0:
                call_params["value"] = value
            transaction.call(call_params)
        except (ValueError, ContractLogicError) as error:
            logger.error({"msg": "Local transaction reverted.", "error": str(error)})
            return False

        logger.info({"msg": "Tx local call succeed."})
        return True

    def send(
        self,
        transaction: ContractFunction,
        timeout_in_blocks: int,
        value: Wei = Wei(0),
    ) -> bool:
        if not variables.ACCOUNT:
            logger.info(
                {"msg": "Account was not provided. Sending transaction skipped."}
            )
            return True

        if variables.DRY_RUN:
            logger.info({"msg": "Dry mode activated. Sending transaction skipped."})
            return True

        pending = self.w3.eth.get_block("pending")

        priority = self._get_priority_fee(
            variables.GAS_PRIORITY_FEE_PERCENTILE,
            variables.MIN_PRIORITY_FEE,
            variables.MAX_PRIORITY_FEE,
        )

        gas_limit = self._estimate_gas(transaction, variables.ACCOUNT.address, value)

        tx_params = TxParams(
            {
                "from": variables.ACCOUNT.address,
                "gas": gas_limit,
                "maxFeePerGas": Wei(pending["baseFeePerGas"] * 2 + priority),
                "maxPriorityFeePerGas": priority,
                "nonce": self.w3.eth.get_transaction_count(variables.ACCOUNT.address),
            }
        )

        if value > 0:
            tx_params["value"] = Wei(value)

        transaction_dict = transaction.build_transaction(tx_params)

        signed = self.w3.eth.account.sign_transaction(
            transaction_dict, variables.ACCOUNT.key
        )
        status = self.send_and_wait(signed, timeout_in_blocks)

        if status:
            TX_SEND.labels("success").inc()
            logger.info({"msg": "Transaction found in blockchain."})
        else:
            TX_SEND.labels("failure").inc()
            logger.warning({"msg": "Transaction not found in blockchain."})

        return status

    @staticmethod
    def _estimate_gas(
        transaction: ContractFunction,
        account_address: ChecksumAddress,
        value: Wei = Wei(0),
    ) -> int:
        try:
            tx_params = TxParams({"from": account_address})
            if value > 0:
                tx_params["value"] = value
            gas = transaction.estimate_gas(tx_params)
        except ContractLogicError as error:
            logger.warning(
                {
                    "msg": "Can not estimate gas. Contract logic error.",
                    "error": str(error),
                }
            )
            return variables.CONTRACT_GAS_LIMIT
        except ValueError as error:
            logger.warning(
                {
                    "msg": "Can not estimate gas. Execution reverted.",
                    "error": str(error),
                }
            )
            return variables.CONTRACT_GAS_LIMIT

        return min(
            variables.CONTRACT_GAS_LIMIT,
            int(gas * 1.3),
        )

    def send_and_wait(
        self, signed_tx: SignedTransaction, timeout_in_blocks: int
    ) -> bool:
        try:
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        except Exception as error:
            logger.error({"msg": "Transaction reverted.", "value": str(error)})
            return False

        logger.info({"msg": "Transaction sent.", "value": tx_hash.hex()})
        try:
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(
                tx_hash, (timeout_in_blocks + 1) * SLOT_TIME
            )
        except TimeExhausted:
            return False

        logger.info(
            {
                "msg": "Sent transaction included in blockchain.",
                "value": tx_receipt["transactionHash"].hex(),
            }
        )
        return True

    def _get_priority_fee(
        self, percentile: int, min_priority_fee: Wei, max_priority_fee: Wei
    ) -> Wei:
        return min(
            max(
                self.w3.eth.fee_history(1, "latest", reward_percentiles=[percentile])[
                    "reward"
                ][0][0],
                min_priority_fee,
            ),
            max_priority_fee,
        )
