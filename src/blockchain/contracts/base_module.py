import structlog
from eth_typing import ChecksumAddress
from web3.types import BlockIdentifier

from src.blockchain.contracts.base_interface import ContractInterface

logger = structlog.get_logger(__name__)


class BaseModuleContract(ContractInterface):
    abi_path = "./interfaces/BaseModule.json"

    def exit_penalties(
        self, block_identifier: BlockIdentifier = "latest"
    ) -> ChecksumAddress:
        response = self.functions.EXIT_PENALTIES().call(
            block_identifier=block_identifier
        )
        logger.info(
            {
                "msg": "Call `EXIT_PENALTIES()`.",
                "value": response,
                "block_identifier": repr(block_identifier),
            }
        )
        return response
