from eth_abi import decode, encode
from eth_typing import HexStr
from hexbytes import HexBytes
from web3 import Web3

from src.utils.types import Key


class ValidatorExitData:
    # Constants matching the original ejector format
    MODULE_ID_LENGTH = 3  # 3 bytes
    NODE_OPERATOR_ID_LENGTH = 5  # 5 bytes
    VALIDATOR_INDEX_LENGTH = 8  # 8 bytes
    VALIDATOR_PUB_KEY_LENGTH = 48  # 48 bytes

    exit_requests: list[Key]

    def __init__(self, exit_requests: list[Key]):
        # Sort all requests by module ID, node operator ID, and validator index (VEB requirements)
        self.exit_requests = sorted(exit_requests, key=lambda x: (x.module_id, x.no_id, x.validator_index))

    @classmethod
    def from_et_calldata(cls, calldata: HexStr) -> "ValidatorExitData":
        raise NotImplementedError('Not yet implemented')
        result = decode(['(uint256,uint256,uint64,bytes,uint256)[]'], Web3.to_bytes(hexstr=calldata))
        return result

    @classmethod
    def from_veb_calldata(cls) -> "ValidatorExitData":
        raise NotImplementedError('Not yet implemented')

    def to_veb_calldata(self) -> HexStr:
        """
        ABI encode exit requests as ExitRequestsData struct for Solidity contract

        This creates raw encoded bytes matching the original ejector format (WITHOUT valPubKeyIndex)

        Format:
        MSB <------------------------------------------------------- LSB
        |  3 bytes   |  5 bytes   |     8 bytes      |    48 bytes     |
        |  moduleId  |  nodeOpId  |  validatorIndex  | validatorPubkey |

        Args:
            exit_requests: List of exit request inputs

        Returns:
            ABI-encoded ExitRequestsData struct

        struct ExitRequestsData {
            bytes data;
            uint256 dataFormat;
        }
        """
        veb_calldata = b''

        for request in self.exit_requests:
            # Module ID (3 bytes) - matching original format
            veb_calldata += request.module_id.to_bytes(self.MODULE_ID_LENGTH, byteorder='big')

            # Node Operator ID (5 bytes) - matching original format
            veb_calldata += request.no_id.to_bytes(self.NODE_OPERATOR_ID_LENGTH, byteorder='big')

            # Validator Index (8 bytes)
            veb_calldata += request.validator_index.to_bytes(self.VALIDATOR_INDEX_LENGTH, byteorder='big')

            veb_calldata += HexBytes(request.validator_pub_key)

        return HexStr(veb_calldata.hex())

    def to_et_calldata(self) -> HexStr:
        """
        ABI encode exit requests as array of structs for Solidity contract

        This creates the _evmScriptCallData that can be passed to:
        function createEVMScript(address _creator, bytes memory _evmScriptCallData)

        The contract expects: SubmitExitRequestHashesUtils.ExitRequestInput[] memory

        Args:
            exit_requests: List of exit request inputs

        Returns:
            ABI-encoded bytes data ready for Solidity contract
        """
        return HexStr(encode(
            ['(uint256,uint256,uint64,bytes,uint256)[]'],
            [[(
                req.module_id,
                req.no_id,
                req.validator_index,
                HexBytes(req.validator_pub_key),
                req.pub_key_index,
            ) for req in self.exit_requests]]
        ).hex())
