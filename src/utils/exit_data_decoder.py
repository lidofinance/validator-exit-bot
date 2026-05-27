"""
Exit data decoder utility.

This module provides local Python implementation of exit data unpacking,
replicating the Solidity contract logic without requiring contract calls.
"""

from typing import Any

# Constants from Solidity contract
PUBLIC_KEY_LENGTH = 48  # bytes

# DATA_FORMAT_LIST = 1: 64 bytes per entry
#   MSB <----------------------------------------------- LSB
#   |  3 bytes   |  5 bytes   |     8 bytes      |    48 bytes     |
#   |  moduleId  |  nodeOpId  |  validatorIndex  | validatorPubkey |
DATA_FORMAT_LIST = 1
PACKED_REQUEST_LENGTH_V1 = 64  # 3 + 5 + 8 + 48

# DATA_FORMAT_LIST_WITH_KEY_INDEX = 2: 72 bytes per entry
#   MSB <--------------------------------------------------------------- LSB
#   |  3 bytes   |  5 bytes   |     8 bytes      |   8 bytes  |    48 bytes     |
#   |  moduleId  |  nodeOpId  |  validatorIndex  |  keyIndex  | validatorPubkey |
DATA_FORMAT_LIST_WITH_KEY_INDEX = 2
PACKED_REQUEST_LENGTH_V2 = 72  # 3 + 5 + 8 + 8 + 48

METADATA_LENGTH = 16  # 3 + 5 + 8 bytes (moduleId + nodeOpId + validatorIndex)
KEY_INDEX_LENGTH = 8  # bytes, only in format 2


def _get_packed_request_length(data_format: int) -> int:
    """Return the byte size of a single packed exit request for the given data format."""
    if data_format == DATA_FORMAT_LIST_WITH_KEY_INDEX:
        return PACKED_REQUEST_LENGTH_V2
    return PACKED_REQUEST_LENGTH_V1


def _get_pubkey_offset_in_entry(data_format: int) -> int:
    """Return the byte offset of the pubkey within a single packed entry."""
    if data_format == DATA_FORMAT_LIST_WITH_KEY_INDEX:
        return METADATA_LENGTH + KEY_INDEX_LENGTH  # 24
    return METADATA_LENGTH  # 16


def unpack_exit_request(exit_data: bytes, index: int, data_format: int = DATA_FORMAT_LIST) -> dict[str, Any]:
    """
    Unpack a single exit request from packed data using local Python implementation.

    This replicates the Solidity _getValidatorData function.

    Format 1 (DATA_FORMAT_LIST) - 64 bytes per entry:
        MSB <----------------------------------------------- LSB
        |  3 bytes   |  5 bytes   |     8 bytes      |    48 bytes     |
        |  moduleId  |  nodeOpId  |  validatorIndex  | validatorPubkey |

    Format 2 (DATA_FORMAT_LIST_WITH_KEY_INDEX) - 72 bytes per entry:
        MSB <--------------------------------------------------------------- LSB
        |  3 bytes   |  5 bytes   |     8 bytes      |   8 bytes  |    48 bytes     |
        |  moduleId  |  nodeOpId  |  validatorIndex  |  keyIndex  | validatorPubkey |

    Args:
        exit_data: Packed exit requests data
        index: Index of the validator to unpack (0-based)
        data_format: Data format identifier (1 or 2)

    Returns:
        Dictionary with keys: pubkey (bytes), nodeOpId (int), moduleId (int),
        valIndex (int), index (int), and optionally keyIndex (int) for format 2

    Raises:
        ValueError: If index is out of range or data_format is unknown
    """
    packed_request_length = _get_packed_request_length(data_format)

    # Check if index is valid
    if index >= len(exit_data) // packed_request_length:
        raise ValueError(
            f"Index {index} out of range for {len(exit_data) // packed_request_length} validators"
        )

    # Calculate offset for this validator entry
    item_offset = packed_request_length * index

    # Read first 16 bytes which contain the metadata
    # Memory layout (big-endian bytes → MSB first):
    #   bytes 0-2:  moduleId  (24 bits, highest)
    #   bytes 3-7:  nodeOpId  (40 bits)
    #   bytes 8-15: valIndex  (64 bits, lowest)
    metadata_bytes = exit_data[item_offset : item_offset + METADATA_LENGTH]

    # Convert bytes to integer (big-endian)
    data_without_pubkey = int.from_bytes(metadata_bytes, byteorder="big")

    # Extract fields using bit shifting (same as Solidity, LSB-first order)
    val_index = data_without_pubkey & 0xFFFFFFFFFFFFFFFF       # lowest 64 bits
    node_op_id = (data_without_pubkey >> 64) & 0xFFFFFFFFFF    # next 40 bits
    module_id = (data_without_pubkey >> (64 + 40)) & 0xFFFFFF  # next 24 bits

    result: dict[str, Any] = {
        "moduleId": module_id,
        "nodeOpId": node_op_id,
        "valIndex": val_index,
        "index": index,
    }

    # Extract keyIndex for format 2
    if data_format == DATA_FORMAT_LIST_WITH_KEY_INDEX:
        key_index_offset = item_offset + METADATA_LENGTH
        key_index_bytes = exit_data[key_index_offset : key_index_offset + KEY_INDEX_LENGTH]
        result["keyIndex"] = int.from_bytes(key_index_bytes, byteorder="big")

    # Extract pubkey (48 bytes)
    pubkey_offset = item_offset + _get_pubkey_offset_in_entry(data_format)
    result["pubkey"] = exit_data[pubkey_offset : pubkey_offset + PUBLIC_KEY_LENGTH]

    return result


def decode_all_validators(exit_data: bytes, data_format: int = DATA_FORMAT_LIST) -> list[dict[str, Any]]:
    """
    Decode all validators from packed exit data using local Python implementation.

    This replaces the contract call to decode_all_validators, performing the
    unpacking locally without any blockchain interaction.

    Args:
        exit_data: Packed exit requests data
        data_format: Data format identifier (1 = DATA_FORMAT_LIST,
                     2 = DATA_FORMAT_LIST_WITH_KEY_INDEX)

    Returns:
        List of validator dictionaries, each containing:
        - pubkey: bytes (48 bytes)
        - moduleId: int
        - nodeOpId: int
        - valIndex: int
        - index: int (position in the list, 0-based)
        - keyIndex: int (only for data_format=2)

    Raises:
        ValueError: If unable to unpack a validator or if data is invalid
    """
    requests_count = calculate_requests_count(exit_data, data_format)
    validators = []

    for i in range(requests_count):
        try:
            validator = unpack_exit_request(exit_data, i, data_format)
            validators.append(validator)
        except Exception as e:
            raise ValueError(f"Failed to unpack validator at index {i}: {e}") from e

    return validators


def calculate_requests_count(exit_data: bytes, data_format: int = DATA_FORMAT_LIST) -> int:
    """
    Calculate the number of validators in packed exit data.

    Args:
        exit_data: Packed exit requests data
        data_format: Data format identifier (1 or 2)

    Returns:
        Number of validators that can be extracted from the data
    """
    return len(exit_data) // _get_packed_request_length(data_format)
