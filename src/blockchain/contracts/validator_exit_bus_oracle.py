import structlog
from typing import Any, Optional

from blockchain.contracts.base_interface import ContractInterface
from eth_typing import ChecksumAddress, HexStr
from web3.types import BlockIdentifier, EventData

logger = structlog.get_logger(__name__)

class ValidatorExitBusOracleContract(ContractInterface):
    abi_path = './interfaces/ValidatorExitBusOracle.json'

    def get_exit_data_processing_events(
        self, 
        from_block: BlockIdentifier = 0, 
        to_block: BlockIdentifier = 'latest'
    ) -> list[EventData]:
        """Fetch all ExitDataProcessing events within the specified block range."""
        events = self.events.ExitDataProcessing.get_logs(
            from_block=from_block,
            to_block=to_block
        )
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
            func, params = self.decode_function_input(input_data)
            if func.fn_name == 'submitReportData':
                logger.info({'msg': 'Successfully decoded as submitReportData'})
                return params
            return None
        except Exception as e:
            logger.warning({
                'msg': 'Failed to decode as submitReportData',
                'error': str(e),
                'error_type': type(e).__name__
            })
            return None

    def decode_submit_exit_requests_data(self, input_data: HexStr) -> Optional[dict[str, Any]]:
        """
        Decode transaction input data as submitExitRequestsData function call.
        
        Returns None if decoding fails.
        """
        try:
            func, params = self.decode_function_input(input_data)
            if func.fn_name == 'submitExitRequestsData':
                logger.info({'msg': 'Successfully decoded as submitExitRequestsData'})
                return params
            return None
        except Exception as e:
            logger.warning({
                'msg': 'Failed to decode as submitExitRequestsData',
                'error': str(e),
                'error_type': type(e).__name__
            })
            return None

    def trigger_exits(
        self,
        exits_data: bytes,
        data_format: int,
        exit_data_indexes: list[int],
        refund_recipient: ChecksumAddress
    ):
        """
        Trigger exits for validators specified by exit data indexes.
        
        This method builds a transaction to trigger validator exits. The actual exit messages
        will be sent to the Consensus Layer for the specified validators.
        
        Note: This function is payable and requires sending ETH for withdrawal request fees.
        The value must be passed separately to the transaction.send() method.
        
        Args:
            exits_data: Packed exit requests data (bytes)
            data_format: Data format identifier (usually 1 for DATA_FORMAT_LIST)
            exit_data_indexes: List of validator indexes to exit from the packed data
            refund_recipient: Address to receive any refund
            
        Returns:
            ContractFunction that can be executed or passed to transaction utilities
            
        Example:
            >>> vebo = w3.lido.validator_exit_bus_oracle
            >>> withdrawal_vault = w3.lido.withdrawal_vault
            >>> fee = withdrawal_vault.get_withdrawal_request_fee()
            >>> total_fee = fee * len(exit_data_indexes)
            >>> tx_function = vebo.trigger_exits(
            ...     exits_data=exit_requests_bytes,
            ...     data_format=1,
            ...     exit_data_indexes=[0, 1, 2],
            ...     refund_recipient=Web3.to_checksum_address("0x...")
            ... )
            >>> # Execute transaction with value
            >>> w3.transaction.send(tx_function, timeout_in_blocks=10, value=total_fee)
        """
        logger.info({
            'msg': 'Preparing triggerExits transaction',
            'data_format': data_format,
            'exit_data_indexes_count': len(exit_data_indexes),
            'exit_data_indexes': exit_data_indexes,
            'data_length': len(exits_data),
            'refund_recipient': refund_recipient
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
