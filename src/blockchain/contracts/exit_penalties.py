import structlog
from eth_typing import HexStr
from web3.types import BlockIdentifier

from src.blockchain.contracts.base_interface import ContractInterface

logger = structlog.get_logger(__name__)


class ExitPenaltiesContract(ContractInterface):
    abi_path = "./interfaces/ExitPenalties.json"

    def is_exit_delay_applicable(
        self, node_op_id: int, pubkey: HexStr, block_identifier: BlockIdentifier = "latest"
    ) -> bool:
        pubkey_bytes = bytes.fromhex(pubkey.removeprefix("0x"))
        response = self.functions.getExitPenaltyInfo(node_op_id, pubkey_bytes).call(
            block_identifier=block_identifier
        )
        # response is ExitPenaltyInfo: (delayFee, strikesPenalty, elWithdrawalRequestFee)
        # each field is MarkedUint248: (value, isValue)
        delay_fee_is_value = bool(response[0][1])
        logger.info(
            {
                "msg": "Call `getExitPenaltyInfo()`.",
                "node_op_id": node_op_id,
                "delay_fee_is_value": delay_fee_is_value,
                "block_identifier": repr(block_identifier),
            }
        )
        return delay_fee_is_value
