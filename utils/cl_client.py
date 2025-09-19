from urllib.parse import urljoin

import requests
from eth_pydantic_types.hex.str import HexStr


class CLClient:
    def __init__(self, url: str):
        self.url = url

    def get_all_validators(self) -> dict[int, HexStr]:
        response = requests.get(urljoin(self.url, '/eth/v1/beacon/states/head/validators'), timeout=60)
        response.raise_for_status()
        return {int(val['index']): val['validator']['pubkey'] for val in response.json()['data']}

    def get_validator_index_by_pubkey(self, pub_key: HexStr) -> int:
        response = requests.get(urljoin(self.url, f'/eth/v1/beacon/states/head/validators/{pub_key}'), timeout=10)
        response.raise_for_status()

        data = response.json()

        if data.get('error'):
            raise ValueError(f"Validator not found in CL for public key: {pub_key}")

        return int(data['data']['index'])
