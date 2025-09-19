from functools import lru_cache
from urllib.parse import urljoin

import requests
from eth_typing import ChecksumAddress, HexStr

from utils.types import Key, KapiKey


class KeysAPIClient:
    def __init__(self, url: str):
        self.url = url

    @lru_cache(maxsize=1)
    def get_modules(self) -> dict[ChecksumAddress, int]:
        response = requests.get(urljoin(self.url, 'v1/modules'), timeout=10)
        response.raise_for_status()
        return {module['stakingModuleAddress']: module['id'] for module in response.json()['data']}

    def get_keys(self) -> list[KapiKey]:
        modules_map = self.get_modules()

        response = requests.get(urljoin(self.url, 'v1/keys'), timeout=10)
        response.raise_for_status()
        return [
            KapiKey(
                module_id=modules_map[key['moduleAddress']],
                no_id=key['operatorIndex'],
                validator_pub_key=key['key'],
                pub_key_index=key['index'],
            ) for key in response.json()['data']
        ]
