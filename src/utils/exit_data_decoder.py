"""
Exit data decoder utility.

This module provides local Python implementation of exit data unpacking,
replicating the Solidity contract logic without requiring contract calls.
"""
from typing import Dict, Any, List


# Constants from Solidity contract
PUBLIC_KEY_LENGTH = 48  # bytes
PACKED_REQUEST_LENGTH = 64  # 16 bytes metadata + 48 bytes pubkey + 5 bytes padding


def unpack_exit_request(exit_data: bytes, index: int) -> Dict[str, Any]:
    """
    Unpack a single exit request from packed data using local Python implementation.
    
    This replicates the Solidity _getValidatorData function.
    
    The packed format (69 bytes per validator):
    - Bytes 0-15:  Metadata (16 bytes)
                   - Bits 0-63:    valIndex (uint64 / 8 bytes)
                   - Bits 64-103:  nodeOpId (uint40 / 5 bytes)
                   - Bits 104-127: moduleId (uint24 / 3 bytes)
    - Bytes 16-63: pubkey (48 bytes)
    - Bytes 64-68: padding (5 bytes)
    
    Args:
        exit_data: Packed exit requests data
        index: Index of the validator to unpack (0-based)
        
    Returns:
        Dictionary with keys: pubkey (bytes), nodeOpId (int), moduleId (int), valIndex (int), index (int)
        
    Raises:
        ValueError: If index is out of range
    """
    # Check if index is valid
    if index >= len(exit_data) // PACKED_REQUEST_LENGTH:
        raise ValueError(
            f"Index {index} out of range for {len(exit_data) // PACKED_REQUEST_LENGTH} validators"
        )
    
    # Calculate offset for this validator
    item_offset = PACKED_REQUEST_LENGTH * index
    
    # Read first 16 bytes which contain the metadata
    # Format: | padding/zeros | 24 bits moduleId | 40 bits nodeOpId | 64 bits valIndex |
    metadata_bytes = exit_data[item_offset:item_offset + 16]
    
    # Convert bytes to integer (big-endian)
    data_without_pubkey = int.from_bytes(metadata_bytes, byteorder='big')
    
    # Extract fields using bit shifting (same as Solidity)
    # LSB first: valIndex occupies the lowest 64 bits
    val_index = data_without_pubkey & 0xFFFFFFFFFFFFFFFF  # uint64 mask (64 bits)
    
    # Next 40 bits: nodeOpId
    node_op_id = (data_without_pubkey >> 64) & 0xFFFFFFFFFF  # uint40 mask (40 bits)
    
    # Next 24 bits: moduleId
    module_id = (data_without_pubkey >> (64 + 40)) & 0xFFFFFF  # uint24 mask (24 bits)
    
    # Extract pubkey (48 bytes starting at offset 16)
    pubkey_offset = item_offset + 16
    pubkey = exit_data[pubkey_offset:pubkey_offset + PUBLIC_KEY_LENGTH]
    
    return {
        'pubkey': pubkey,
        'nodeOpId': node_op_id,
        'moduleId': module_id,
        'valIndex': val_index,
        'index': index
    }


def decode_all_validators(exit_data: bytes) -> List[Dict[str, Any]]:
    """
    Decode all validators from packed exit data using local Python implementation.
    
    This replaces the contract call to decode_all_validators, performing the
    unpacking locally without any blockchain interaction.
    
    Args:
        exit_data: Packed exit requests data
        
    Returns:
        List of validator dictionaries, each containing:
        - pubkey: bytes (48 bytes)
        - nodeOpId: int
        - moduleId: int
        - valIndex: int
        - index: int (position in the list, 0-based)
        
    Raises:
        ValueError: If unable to unpack a validator or if data is invalid
    """
    requests_count = calculate_requests_count(exit_data)
    validators = []
    
    for i in range(requests_count):
        try:
            validator = unpack_exit_request(exit_data, i)
            validators.append(validator)
        except Exception as e:
            raise ValueError(f"Failed to unpack validator at index {i}: {e}")
    
    return validators


def calculate_requests_count(exit_data: bytes) -> int:
    """
    Calculate the number of validators in packed exit data.
    
    Args:
        exit_data: Packed exit requests data
        
    Returns:
        Number of validators that can be extracted from the data
    """
    return len(exit_data) // PACKED_REQUEST_LENGTH

