import structlog

from contracts.base_interface import ContractInterface
from eth_typing import ChecksumAddress
from web3.types import BlockIdentifier

logger = structlog.get_logger(__name__)

class StakingRouterContract(ContractInterface):
    abi_path = './interfaces/StakingRouter.json'

    def get_staking_module(self, id: int, block_identifier: BlockIdentifier = 'latest') -> ChecksumAddress:
        response = self.functions.getStakingModule(id).call(block_identifier=block_identifier)
        logger.info({'msg': f'Call `getStakingModule({id})`.', 'value': response, 'block_identifier': repr(block_identifier)})
        (_, address, _, _, _, _, _, _, _, _, _, _) = response
        return address
