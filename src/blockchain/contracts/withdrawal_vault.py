import structlog

from blockchain.contracts.base_interface import ContractInterface
from web3.types import BlockIdentifier

logger = structlog.get_logger(__name__)

class WithdrawalVaultContract(ContractInterface):
    abi_path = './interfaces/WithdrawalVault.json'

    def get_withdrawal_request_fee(self, block_identifier: BlockIdentifier = 'latest') -> int:
        response = self.functions.getWithdrawalRequestFee().call(block_identifier=block_identifier)
        logger.info({'msg': 'Call `getWithdrawalRequestFee()`.', 'value': response, 'block_identifier': repr(block_identifier)})
        return response

