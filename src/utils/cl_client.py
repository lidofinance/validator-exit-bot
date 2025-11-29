from urllib.parse import urljoin
from typing import Optional

import requests
from eth_typing import HexStr


class CLClient:
    def __init__(self, url: str):
        self.url = url

    def get_validators_by_indexes(self) -> dict[int, HexStr]:
        validators = self.get_all_validators()
        return {int(val['index']): val['validator']['pubkey'] for val in validators}

    def get_all_validators(self) -> dict[int, HexStr]:
        response = requests.get(urljoin(self.url, '/eth/v1/beacon/states/head/validators'), timeout=60)
        response.raise_for_status()
        return response.json()['data']

    def get_validator_index_by_pubkey(self, pub_key: HexStr) -> int:
        response = requests.get(urljoin(self.url, f'/eth/v1/beacon/states/head/validators/{pub_key}'), timeout=10)
        response.raise_for_status()

        data = response.json()

        if data.get('error'):
            raise ValueError(f"Validator not found in CL for public key: {pub_key}")

        return int(data['data']['index'])

    def get_validator_by_pubkey(self, pub_key: HexStr) -> Optional[dict]:
        """
        Get validator information by public key.
        
        Returns None if validator not found, otherwise returns validator data dict.
        """
        try:
            response = requests.get(urljoin(self.url, f'/eth/v1/beacon/states/head/validators/{pub_key}'), timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('error'):
                return None
                
            return data.get('data')
        except Exception:
            return None

    def is_validator_exited(self, pub_key: HexStr) -> bool:
        """
        Check if a validator has exited (fully withdrawn or in withdrawal process).
        
        Returns True if validator is in one of the exited states:
        - withdrawal_done
        - withdrawal_possible
        - exited_slashed
        - exited_unslashed
        """
        validator_data = self.get_validator_by_pubkey(pub_key)
        
        if validator_data is None:
            # Validator not found, consider as not exited
            return False
        
        status = validator_data.get('status', '').lower()
        
        # Check for various exit states
        exited_states = [
            'withdrawal_done',
            'withdrawal_possible', 
            'exited_slashed',
            'exited_unslashed'
        ]
        
        return status in exited_states
