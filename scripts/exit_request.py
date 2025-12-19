from scripts.kapi_client import Key, KeysAPIClient
from src.utils.cl_client import CLClient


def build_exit_request(
    kapi_client: KeysAPIClient, cl_client: CLClient, validator_indexes: list[int]
) -> list[Key]:
    all_validators = cl_client.get_validators_by_indexes()
    keys = kapi_client.get_keys()

    result = []

    for validator_index in validator_indexes:
        if validator_index not in all_validators:
            raise ValueError(f"Validator index {validator_index} not found in CL")

        pub_key = all_validators[validator_index]

        for key in keys:
            if pub_key == key.validator_pub_key:
                result.append(
                    Key(
                        module_id=key.module_id,
                        no_id=key.no_id,
                        validator_index=validator_index,
                        validator_pub_key=key.validator_pub_key,
                        pub_key_index=key.pub_key_index,
                    )
                )
                break
        else:
            raise ValueError(f"Validator pubkey {pub_key} not found in KAPI")

    return result
