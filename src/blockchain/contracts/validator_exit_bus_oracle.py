import structlog
from typing import Any, Optional

from contracts.base_interface import ContractInterface
from eth_typing import ChecksumAddress, HexStr
from web3.types import BlockIdentifier, EventData, TxData, TxReceipt

logger = structlog.get_logger(__name__)

class ValidatorExitBusOracleContract(ContractInterface):
    abi_path = './interfaces/ValidatorExitBusOracle.json'

    def lido(self, block_identifier: BlockIdentifier = 'latest') -> ChecksumAddress:
        response = self.functions.lido().call(block_identifier=block_identifier)
        logger.info({'msg': 'Call `lido()`.', 'value': response, 'block_identifier': repr(block_identifier)})
        return response

    def deposit_security_module(self, block_identifier: BlockIdentifier = 'latest') -> ChecksumAddress:
        response = self.functions.depositSecurityModule().call(block_identifier=block_identifier)
        logger.info({'msg': 'Call `depositSecurityModule()`.', 'value': response, 'block_identifier': repr(block_identifier)})
        return response

    def staking_router(self, block_identifier: BlockIdentifier = 'latest') -> ChecksumAddress:
        response = self.functions.stakingRouter().call(block_identifier=block_identifier)
        logger.info({'msg': 'Call `stakingRouter()`.', 'value': response, 'block_identifier': repr(block_identifier)})
        return response

    def withdrawal_queue(self, block_identifier: BlockIdentifier = 'latest') -> ChecksumAddress:
        response = self.functions.withdrawalQueue().call(block_identifier=block_identifier)
        logger.info({'msg': 'Call `withdrawalQueue()`.', 'value': response, 'block_identifier': repr(block_identifier)})
        return response

    def get_processing_state(self, block_identifier: BlockIdentifier = 'latest') -> dict[str, Any]:
        """
        Get the current processing state from VEBO.
        
        Returns dict with keys:
        - currentFrameRefSlot
        - processingDeadlineTime
        - dataHash
        - dataSubmitted
        - dataFormat
        - requestsCount
        - requestsSubmitted
        """
        result = self.functions.getProcessingState().call(block_identifier=block_identifier)
        
        state = {
            'currentFrameRefSlot': result[0],
            'processingDeadlineTime': result[1],
            'dataHash': result[2],
            'dataSubmitted': result[3],
            'dataFormat': result[4],
            'requestsCount': result[5],
            'requestsSubmitted': result[6]
        }
        
        logger.info({
            'msg': 'Retrieved processing state',
            'requests_count': state['requestsCount'],
            'data_submitted': state['dataSubmitted'],
            'block_identifier': repr(block_identifier)
        })
        
        return state

    def get_exit_data_processing_events(
        self, 
        from_block: BlockIdentifier = 0, 
        to_block: BlockIdentifier = 'latest'
    ) -> list[EventData]:
        """Fetch all ExitDataProcessing events within the specified block range."""
        event_filter = self.events.ExitDataProcessing.create_filter(
            fromBlock=from_block,
            toBlock=to_block
        )
        events = event_filter.get_all_entries()
        logger.info({
            'msg': 'Fetched ExitDataProcessing events',
            'from_block': from_block,
            'to_block': to_block,
            'events_count': len(events)
        })
        return events

    def decode_submit_report_data(self, input_data: HexStr) -> Optional[dict[str, Any]]:
        """
        Decode transaction input data as submitReportData function call.
        
        Returns None if decoding fails.
        """
        try:
            # Get the function signature for submitReportData
            func = self.functions.submitReportData
            decoded = func.decode_function_input(input_data)
            logger.info({'msg': 'Successfully decoded as submitReportData'})
            return decoded[1]  # Return the function arguments dict
        except Exception as error:
            logger.debug({'msg': 'Failed to decode as submitReportData', 'error': str(error)})
            return None

    def decode_submit_exit_requests_data(self, input_data: HexStr) -> Optional[dict[str, Any]]:
        """
        Decode transaction input data as submitExitRequestsData function call.
        
        Returns None if decoding fails.
        """
        try:
            # Get the function signature for submitExitRequestsData
            func = self.functions.submitExitRequestsData
            decoded = func.decode_function_input(input_data)
            logger.info({'msg': 'Successfully decoded as submitExitRequestsData'})
            return decoded[1]  # Return the function arguments dict
        except Exception as error:
            logger.debug({'msg': 'Failed to decode as submitExitRequestsData', 'error': str(error)})
            return None

    def unpack_exit_request(
        self, 
        exit_requests: bytes, 
        data_format: int, 
        index: int
    ) -> tuple[bytes, int, int, int]:
        """
        Unpack a single exit request from packed data.
        
        Args:
            exit_requests: Packed exit requests data
            data_format: Data format identifier
            index: Index of the validator to unpack
            
        Returns:
            Tuple of (pubkey, nodeOpId, moduleId, valIndex)
        """
        result = self.functions.unpackExitRequest(
            exit_requests, 
            data_format, 
            index
        ).call()
        
        pubkey, node_op_id, module_id, val_index = result
        
        logger.debug({
            'msg': 'Unpacked exit request',
            'index': index,
            'module_id': module_id,
            'node_op_id': node_op_id,
            'val_index': val_index,
            'pubkey_length': len(pubkey)
        })
        
        return pubkey, node_op_id, module_id, val_index

    def decode_all_validators(
        self, 
        exit_requests_data: bytes, 
        data_format: int, 
        requests_count: int
    ) -> list[dict[str, Any]]:
        """
        Decode all validators from packed exit requests data.
        
        Args:
            exit_requests_data: Packed exit requests data
            data_format: Data format identifier
            requests_count: Number of requests in the data
            
        Returns:
            List of validator dictionaries with keys: pubkey, nodeOpId, moduleId, valIndex
        """
        validators = []
        
        logger.info({
            'msg': 'Starting to decode validators',
            'requests_count': requests_count,
            'data_format': data_format,
            'data_length': len(exit_requests_data)
        })
        
        for index in range(requests_count):
            try:
                pubkey, node_op_id, module_id, val_index = self.unpack_exit_request(
                    exit_requests_data,
                    data_format,
                    index
                )
                
                validators.append({
                    'pubkey': pubkey,
                    'nodeOpId': node_op_id,
                    'moduleId': module_id,
                    'valIndex': val_index,
                    'index': index
                })
                
            except Exception as error:
                logger.error({
                    'msg': 'Failed to unpack exit request',
                    'index': index,
                    'error': str(error)
                })
                # Continue with next validator even if one fails
                continue
        
        logger.info({
            'msg': 'Successfully decoded validators',
            'validators_count': len(validators)
        })
        
        return validators

    def trigger_exits(
        self,
        exits_data: bytes,
        data_format: int,
        exit_data_indexes: list[int],
        refund_recipient: ChecksumAddress,
        value: int = 0
    ):
        """
        Trigger exits for validators specified by exit data indexes.
        
        This method builds a transaction to trigger validator exits. The actual exit messages
        will be sent to the Consensus Layer for the specified validators.
        
        Args:
            exits_data: Packed exit requests data (bytes)
            data_format: Data format identifier (usually 1 for DATA_FORMAT_LIST)
            exit_data_indexes: List of validator indexes to exit from the packed data
            refund_recipient: Address to receive any refund
            value: Amount of ETH to send with the transaction (in wei)
            
        Returns:
            ContractFunction that can be executed or passed to transaction utilities
            
        Example:
            >>> vebo = w3.lido.validator_exit_bus_oracle
            >>> tx_function = vebo.trigger_exits(
            ...     exits_data=exit_requests_bytes,
            ...     data_format=1,
            ...     exit_data_indexes=[0, 1, 2],
            ...     refund_recipient=Web3.to_checksum_address("0x..."),
            ...     value=0
            ... )
            >>> # Execute transaction
            >>> w3.transaction.send(tx_function, timeout_in_blocks=10)
        """
        logger.info({
            'msg': 'Preparing triggerExits transaction',
            'data_format': data_format,
            'exit_data_indexes_count': len(exit_data_indexes),
            'exit_data_indexes': exit_data_indexes,
            'data_length': len(exits_data),
            'refund_recipient': refund_recipient,
            'value': value
        })
        
        # Build the exitsData struct according to the ABI
        exits_data_struct = {
            'data': exits_data,
            'dataFormat': data_format
        }
        
        # Build and return the contract function
        return self.functions.triggerExits(
            exits_data_struct,
            exit_data_indexes,
            refund_recipient
        )
