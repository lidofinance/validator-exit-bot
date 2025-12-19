import structlog
from typing import Any

from blockchain.contracts.base_interface import ContractInterface
from eth_typing import HexStr
from web3.types import BlockIdentifier

logger = structlog.get_logger(__name__)


class NodeOperatorRegistryContract(ContractInterface):
    abi_path = "./interfaces/NodeOperatorRegistry.json"

    def is_validator_exiting_key_reported(
        self, pubkey: HexStr, block_identifier: BlockIdentifier = "latest"
    ) -> bool:
        # Convert hex string to bytes - remove '0x' prefix if present
        pubkey_bytes = bytes.fromhex(pubkey.removeprefix("0x"))
        response = self.functions.isValidatorExitingKeyReported(pubkey_bytes).call(
            block_identifier=block_identifier
        )
        logger.info(
            {
                "msg": "Call `isValidatorExitingKeyReported()`.",
                "value": response,
                "block_identifier": repr(block_identifier),
            }
        )
        return response

    def get_node_operator(
        self,
        node_operator_id: int,
        full_info: bool = False,
        block_identifier: BlockIdentifier = "latest",
    ) -> dict[str, Any]:
        """
        Get node operator information.

        Args:
            node_operator_id: ID of the node operator
            full_info: If True, returns full information. If False, returns partial info.
            block_identifier: Block at which to query (default: 'latest')

        Returns:
            Dictionary with keys:
            - active: Whether the node operator is active
            - name: Name of the node operator
            - rewardAddress: Address that receives rewards
            - totalVettedValidators: Total number of vetted validators
            - totalExitedValidators: Total number of exited validators
            - totalAddedValidators: Total number of added validators
            - totalDepositedValidators: Total number of deposited validators
        """
        result = self.functions.getNodeOperator(node_operator_id, full_info).call(
            block_identifier=block_identifier
        )

        # Unpack the tuple returned by the contract
        (
            active,
            name,
            reward_address,
            total_vetted_validators,
            total_exited_validators,
            total_added_validators,
            total_deposited_validators,
        ) = result

        node_operator_info = {
            "active": active,
            "name": name,
            "rewardAddress": reward_address,
            "totalVettedValidators": total_vetted_validators,
            "totalExitedValidators": total_exited_validators,
            "totalAddedValidators": total_added_validators,
            "totalDepositedValidators": total_deposited_validators,
        }

        logger.info(
            {
                "msg": "Call `getNodeOperator()`.",
                "node_operator_id": node_operator_id,
                "full_info": full_info,
                "active": active,
                "name": name,
                "block_identifier": repr(block_identifier),
            }
        )

        return node_operator_info
