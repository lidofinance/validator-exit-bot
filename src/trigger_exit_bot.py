from blockchain.contracts.validator_exit_bus_oracle import ValidatorExitBusOracleContract
from blockchain.web3_extentions.transaction import TransactionUtils
import structlog
from typing import Optional, Any, cast
from hashlib import sha256
from blockchain.typings import Web3
from web3.types import BlockIdentifier, TxReceipt, TxData
from utils.cl_client import CLClient
from utils.exit_data_decoder import decode_all_validators
import variables

logger = structlog.get_logger(__name__)


class TriggerExitBot:
    def __init__(self, w3: Web3, cl_client: CLClient):
        self.w3 = w3
        self.cl_client = cl_client
        # Store mapping of exit_requests_data hash -> list of validators
        # Key is SHA256 hash of the data, value is list of validator dicts
        self.validators_map: dict[str, list[dict[str, Any]]] = {}
        # Store mapping of exit_requests_data hash -> data_format
        self.data_format_map: dict[str, int] = {}
        # Store mapping of hash -> original bytes data (for transaction building)
        self.data_bytes_map: dict[str, bytes] = {}
        self.vebo = cast(ValidatorExitBusOracleContract, self.w3.lido.validator_exit_bus_oracle)
        self.transaction_utils = cast(TransactionUtils, self.w3.transaction)
    
    def _get_data_key(self, data: bytes | str) -> str:
        """
        Generate a consistent hash key for exit requests data.
        
        Args:
            data: Either bytes or hex string of the data
            
        Returns:
            SHA256 hash as hex string (64 characters instead of potentially thousands)
        """
        if isinstance(data, str):
            # If it's already a hex string, convert to bytes first
            data = bytes.fromhex(data)
        return sha256(data).hexdigest()

    def _get_transaction_data(self, tx_hash: str) -> tuple[Optional[TxData], Optional[TxReceipt]]:
        """
        Get transaction data and receipt for a given transaction hash.
        
        Returns:
            Tuple of (transaction_data, transaction_receipt) or (None, None) if failed
        """
        tx = self.w3.eth.get_transaction(tx_hash)
        tx_receipt = self.w3.eth.get_transaction_receipt(tx_hash)
        return tx, tx_receipt

    def _decode_transaction_input(self, input_data: str) -> tuple[Optional[str], Optional[dict[str, Any]]]:
        """
        Attempt to decode transaction input data.
        
        Tries to decode as submitReportData first, then as submitExitRequestsData.
        
        Returns:
            Tuple of (function_name, decoded_data) or (None, None) if both fail
        """
        # Try to decode as submitReportData first
        decoded = self.vebo.decode_submit_report_data(input_data)
        if decoded is not None:
            return 'submitReportData', decoded
        
        # If that fails, try to decode as submitExitRequestsData
        decoded = self.vebo.decode_submit_exit_requests_data(input_data)
        if decoded is not None:
            return 'submitExitRequestsData', decoded
        
        logger.warning({
            'msg': 'Failed to decode transaction input as either submitReportData or submitExitRequestsData'
        })
        return None, None

    def trigger_exits(
        self,
        from_block: BlockIdentifier = 0,
        to_block: BlockIdentifier = 'latest'
    ):
        """
        Fetch and process ExitDataProcessing events from VEBO.
        
        Args:
            from_block: Starting block number (default: 0)
            to_block: Ending block number (default: 'latest')
        """
        logger.info({
            'msg': 'Starting to fetch ExitDataProcessing events',
            'from_block': from_block,
            'to_block': to_block
        })
        
        # Fetch ExitDataProcessing events from VEBO
        events = self.vebo.get_exit_data_processing_events(
            from_block=from_block,
            to_block=to_block
        )
        
        logger.info({
            'msg': 'Successfully fetched ExitDataProcessing events',
            'events_count': len(events)
        })
        
        # Process each event
        for event in events:
            exit_requests_hash = event['args']['exitRequestsHash']
            block_number = event['blockNumber']
            transaction_hash = event['transactionHash'].hex()
            
            logger.info({
                'msg': 'Processing ExitDataProcessing event',
                'exit_requests_hash': exit_requests_hash.hex(),
                'block_number': block_number,
                'transaction_hash': transaction_hash
            })
            
            tx_data, tx_receipt = self._get_transaction_data(transaction_hash)
            
            if tx_data is None or tx_receipt is None:
                raise ValueError('Could not get transaction data')
            
            # Check if transaction was successful
            if tx_receipt['status'] != 1:
                logger.warning({
                    'msg': 'Transaction was not successful, skipping',
                    'transaction_hash': transaction_hash,
                    'status': tx_receipt['status']
                })
                continue
            
            logger.info({
                'msg': 'Transaction was successful',
                'transaction_hash': transaction_hash,
            })
            
            # Decode transaction input data
            function_name, decoded_data = self._decode_transaction_input(tx_data['input'])
            
            if function_name is None:
                raise ValueError('Could not decode transaction input')
            
            if function_name == 'submitReportData':
                self._process_submit_report_data(decoded_data)
            elif function_name == 'submitExitRequestsData':
                self._process_submit_exit_requests_data(decoded_data)
        
        # After processing all events, check and trigger exits for ALL validators in state
        logger.info({
            'msg': 'Processing complete, checking all validators in state',
            'state_entries': len(self.validators_map)
        })
        
        for data_key in list(self.validators_map.keys()):
            self._check_and_trigger_exits(data_key)
        
        return events

    def _process_submit_report_data(self, decoded_data: dict[str, Any]) -> None:
        """Process decoded submitReportData transaction."""
        data_obj = decoded_data.get('data', {})
        exit_requests_data = data_obj.get('data', b'')
        data_format = data_obj.get('dataFormat', 0)
        requests_count = data_obj.get('requestsCount', 0)
        
        logger.info({
            'msg': 'Processing submitReportData',
            'consensus_version': data_obj.get('consensusVersion'),
            'ref_slot': data_obj.get('refSlot'),
            'requests_count': requests_count,
            'data_length': len(exit_requests_data),
            'data_format': data_format,
        })
        validators = decode_all_validators(exit_requests_data)
        
        # Generate hash key for efficient storage
        data_key = self._get_data_key(exit_requests_data)
        self.validators_map[data_key] = validators
        self.data_format_map[data_key] = data_format
        self.data_bytes_map[data_key] = exit_requests_data if isinstance(exit_requests_data, bytes) else bytes.fromhex(exit_requests_data)
        
        logger.info({
            'msg': 'Stored validators mapping for submitReportData',
            'data_hash': data_key,
            'validators_count': len(validators)
        })
        
        # Log sample validators
        if validators:
            for i, validator in enumerate(validators[:3]):  # Log first 3 validators
                logger.info({
                    'msg': f'Validator {i}',
                    'pubkey': validator['pubkey'].hex() if isinstance(validator['pubkey'], bytes) else validator['pubkey'],
                    'moduleId': validator['moduleId'],
                    'nodeOpId': validator['nodeOpId'],
                    'valIndex': validator['valIndex']
                })

    def _process_submit_exit_requests_data(self, decoded_data: dict[str, Any]):
        """Process decoded submitExitRequestsData transaction."""
        request_obj = decoded_data.get('request', {})
        exit_requests_data = request_obj.get('data', b'')
        data_format = request_obj.get('dataFormat', 0)
        
        logger.info({
            'msg': 'Processing submitExitRequestsData',
            'data_format': data_format,
            'data_length': len(exit_requests_data)
        })
        
        # Decode all validators from the packed data
        validators = decode_all_validators(exit_requests_data)
        
        # Generate hash key for efficient storage
        data_key = self._get_data_key(exit_requests_data)
        self.validators_map[data_key] = validators
        self.data_format_map[data_key] = data_format
        self.data_bytes_map[data_key] = exit_requests_data if isinstance(exit_requests_data, bytes) else bytes.fromhex(exit_requests_data)
        
        logger.info({
            'msg': 'Stored validators mapping for submitExitRequestsData',
            'data_hash': data_key,
            'validators_count': len(validators)
        })
        
        # Log sample validators
        if validators:
            for i, validator in enumerate(validators[:3]):  # Log first 3 validators
                logger.info({
                    'msg': f'Validator {i}',
                    'pubkey': validator['pubkey'].hex() if isinstance(validator['pubkey'], bytes) else validator['pubkey'],
                    'moduleId': validator['moduleId'],
                    'nodeOpId': validator['nodeOpId'],
                    'valIndex': validator['valIndex']
                })
    
    def get_validators_for_data(self, exit_requests_data: bytes | str) -> Optional[list[dict[str, Any]]]:
        """
        Get decoded validators for given exit requests data.
        
        Args:
            exit_requests_data: Either bytes or hex string of the exit requests data
            
        Returns:
            List of validator dictionaries or None if not found
        """
        data_key = self._get_data_key(exit_requests_data)
        return self.validators_map.get(data_key)

    def _check_and_trigger_exits(self, data_key: str):
        """
        Check validators and trigger exits for those that are reported but not exited.
        
        This method:
        1. Checks if each validator is already exited using CL client
        2. If exited, removes it from the state
        3. If not exited, checks if it was reported using the node operator registry
        4. If reported and not exited, adds it to the list to trigger
        5. Calls trigger_exits transaction with the list
        
        Args:
            data_key: SHA256 hash of the exit requests data
        """
        validators = self.validators_map.get(data_key)
        data_format = self.data_format_map.get(data_key)
        
        if not validators or data_format is None:
            logger.warning({
                'msg': 'No validators or data_format found for data_key',
                'data_hash': data_key
            })
            return
        
        logger.info({
            'msg': 'Starting to check and trigger exits',
            'validators_count': len(validators),
            'data_format': data_format
        })
        
        validators_to_trigger = []
        validators_to_remove = []
        
        for validator in validators:
            pubkey = validator['pubkey']
            pubkey_hex = pubkey.hex() if isinstance(pubkey, bytes) else pubkey
            module_id = validator['moduleId']
            node_op_id = validator['nodeOpId']
            val_index = validator['valIndex']
            validator_index = validator['index']
            
            logger.info({
                'msg': 'Checking validator',
                'pubkey': pubkey_hex[:20] + '...',  # Log first part of pubkey for brevity
                'module_id': module_id,
                'node_op_id': node_op_id,
                'val_index': val_index,
                'validator_index': validator_index
            })
            
            # Check if validator is already exited
            is_exited = self.cl_client.is_validator_exited(pubkey_hex)
            
            if is_exited:
                logger.info({
                    'msg': 'Validator is already exited, removing from state',
                    'pubkey': pubkey_hex[:20] + '...',
                    'validator_index': validator_index
                })
                validators_to_remove.append(validator)
                continue
            
            # Check if module_id is in the whitelist
            if module_id not in variables.MODULES_WHITELIST:
                logger.info({
                    'msg': 'Module not in whitelist, skipping',
                    'module_id': module_id,
                    'validator_index': validator_index
                })
                continue
            
            # Get the node operator registry for this module
            node_operator_registry = self.w3.lido.node_operator_registry_map.get(module_id)
            
            if node_operator_registry is None:
                logger.warning({
                    'msg': 'Node operator registry not found for module',
                    'module_id': module_id,
                    'validator_index': validator_index
                })
                continue
            
            is_reported = node_operator_registry.is_validator_exiting_key_reported(pubkey_hex)
            
            if is_reported:
                logger.info({
                    'msg': 'Validator is reported but not exited, adding to trigger list',
                    'pubkey': pubkey_hex[:20] + '...',
                    'validator_index': validator_index
                })
                validators_to_trigger.append(validator)
            else:
                logger.info({
                    'msg': 'Validator exiting key not reported yet',
                    'pubkey': pubkey_hex[:20] + '...',
                    'validator_index': validator_index
                })
        
        # Remove exited validators from state
        if validators_to_remove:
            self.validators_map[data_key] = [
                v for v in validators if v not in validators_to_remove
            ]
            logger.info({
                'msg': 'Removed exited validators from state',
                'removed_count': len(validators_to_remove),
                'remaining_count': len(self.validators_map[data_key])
            })
        
        # Trigger exits for reported validators
        if validators_to_trigger:
            self._trigger_exits_transaction(data_key, data_format, validators_to_trigger)
        else:
            logger.info({'msg': 'No validators to trigger exits for'})

    def _trigger_exits_transaction(
        self, 
        data_key: str, 
        data_format: int, 
        validators_to_trigger: list[dict[str, Any]]
    ):
        """
        Build and send trigger_exits transaction.
        
        Uses the bot's account address as the refund recipient.
        
        Args:
            data_key: SHA256 hash of the exit requests data
            data_format: Data format identifier
            validators_to_trigger: List of validator dicts to trigger exits for
        """
        # Get original bytes data from the hash key
        exits_data = self.data_bytes_map.get(data_key)
        
        if exits_data is None:
            raise ValueError(f'Original exit data not found for hash key {data_key}')
        
        # Get exit data indexes from validators
        exit_data_indexes = [v['index'] for v in validators_to_trigger]
        
        # Use bot's account address as refund recipient
        # If account is not configured, use zero address as placeholder
        refund_recipient = (
            variables.ACCOUNT.address 
            if variables.ACCOUNT 
            else self.w3.to_checksum_address('0x0000000000000000000000000000000000000000')
        )
        
        # Get withdrawal request fee from withdrawal vault
        fee_per_request = self.w3.lido.withdrawal_vault.get_withdrawal_request_fee()
        total_fee = fee_per_request * len(validators_to_trigger)
        
        logger.info({
            'msg': 'Building trigger_exits transaction',
            'validators_count': len(validators_to_trigger),
            'exit_data_indexes': exit_data_indexes,
            'data_format': data_format,
            'refund_recipient': refund_recipient,
            'fee_per_request': fee_per_request,
            'total_fee': total_fee
        })
        
        # Build the transaction
        tx_function = self.vebo.trigger_exits(
            exits_data=exits_data,
            data_format=data_format,
            exit_data_indexes=exit_data_indexes,
            refund_recipient=refund_recipient
        )
            
        # Check transaction locally first
        if not self.transaction_utils.check(tx_function, value=total_fee):
            logger.error({
                'msg': 'Transaction check failed, not sending',
                'validators_count': len(validators_to_trigger)
            })
            return
            
        # Send transaction
        success = self.transaction_utils.send(
            tx_function, 
            timeout_in_blocks=10,
            value=total_fee
        )
            
        if success:
            logger.info({
                'msg': 'Successfully triggered exits',
                'validators_count': len(validators_to_trigger)
            })
        else:
            logger.warning({
                'msg': 'Failed to trigger exits',
                'validators_count': len(validators_to_trigger)
            })
                