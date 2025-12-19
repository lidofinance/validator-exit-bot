import structlog

from blockchain.contracts.base_interface import ContractInterface
from eth_typing import ChecksumAddress
from web3.types import BlockIdentifier

logger = structlog.get_logger(__name__)


class LidoLocatorContract(ContractInterface):
    abi_path = "./interfaces/LidoLocator.json"

    def validator_exit_bus_oracle(
        self, block_identifier: BlockIdentifier = "latest"
    ) -> ChecksumAddress:
        response = self.functions.validatorsExitBusOracle().call(
            block_identifier=block_identifier
        )
        logger.info(
            {
                "msg": "Call `validatorsExitBusOracle()`.",
                "value": response,
                "block_identifier": repr(block_identifier),
            }
        )
        return response

    def staking_router(
        self, block_identifier: BlockIdentifier = "latest"
    ) -> ChecksumAddress:
        response = self.functions.stakingRouter().call(
            block_identifier=block_identifier
        )
        logger.info(
            {
                "msg": "Call `stakingRouter()`.",
                "value": response,
                "block_identifier": repr(block_identifier),
            }
        )
        return response

    def withdrawal_vault(
        self, block_identifier: BlockIdentifier = "latest"
    ) -> ChecksumAddress:
        response = self.functions.withdrawalVault().call(
            block_identifier=block_identifier
        )
        logger.info(
            {
                "msg": "Call `withdrawalVault()`.",
                "value": response,
                "block_identifier": repr(block_identifier),
            }
        )
        return response
