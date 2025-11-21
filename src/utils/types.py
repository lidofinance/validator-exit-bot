from dataclasses import dataclass

from eth_typing import HexStr


@dataclass
class Key:
    """Exit request input structure"""
    module_id: int
    no_id: int
    validator_index: int
    validator_pub_key: HexStr
    pub_key_index: int


@dataclass
class KapiKey:
    module_id: int
    no_id: int
    validator_pub_key: HexStr
    pub_key_index: int
