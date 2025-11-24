"""Unit tests for TriggerExitBot core logic."""
import pytest
from unittest.mock import Mock, MagicMock, patch, call
from typing import Any
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from trigger_exit_bot import TriggerExitBot


@pytest.fixture
def mock_w3():
    """Create a mock Web3 instance with Lido contracts."""
    w3 = Mock()
    w3.eth = Mock()
    w3.to_checksum_address = Mock(side_effect=lambda x: x)
    
    # Mock Lido contracts
    w3.lido = Mock()
    w3.lido.validator_exit_bus_oracle = Mock()
    w3.lido.withdrawal_vault = Mock()
    w3.lido.node_operator_registry_map = {}
    
    # Mock transaction utilities
    w3.transaction = Mock()
    w3.transaction.check = Mock(return_value=True)
    w3.transaction.send = Mock(return_value=True)
    
    return w3


@pytest.fixture
def mock_cl_client():
    """Create a mock CL client."""
    client = Mock()
    client.is_validator_exited = Mock(return_value=False)
    return client


@pytest.fixture
def bot(mock_w3, mock_cl_client):
    """Create a TriggerExitBot instance with mocks."""
    return TriggerExitBot(mock_w3, mock_cl_client)


@pytest.fixture
def sample_validator():
    """Create a sample validator dictionary."""
    return {
        'pubkey': b'\x01' * 48,
        'nodeOpId': 1,
        'moduleId': 1,
        'valIndex': 0,
        'index': 0
    }


@pytest.fixture
def sample_validators():
    """Create a list of sample validators."""
    return [
        {
            'pubkey': b'\x01' * 48,
            'nodeOpId': 1,
            'moduleId': 1,
            'valIndex': 0,
            'index': 0
        },
        {
            'pubkey': b'\x02' * 48,
            'nodeOpId': 1,
            'moduleId': 1,
            'valIndex': 1,
            'index': 1
        },
        {
            'pubkey': b'\x03' * 48,
            'nodeOpId': 2,
            'moduleId': 1,
            'valIndex': 0,
            'index': 2
        }
    ]


class TestTriggerExitBotInit:
    """Tests for TriggerExitBot initialization."""
    
    def test_init_creates_empty_state(self, mock_w3, mock_cl_client):
        """Test that bot initializes with empty state."""
        bot = TriggerExitBot(mock_w3, mock_cl_client)
        
        assert bot.w3 is mock_w3
        assert bot.cl_client is mock_cl_client
        assert bot.validators_map == {}
        assert bot.data_format_map == {}


class TestGetTransactionData:
    """Tests for _get_transaction_data method."""
    
    def test_get_transaction_data_success(self, bot, mock_w3):
        """Test successfully getting transaction data."""
        tx_hash = "0x123"
        mock_tx = {'input': '0xabc', 'from': '0x456'}
        mock_receipt = {'status': 1, 'blockNumber': 100}
        
        mock_w3.eth.get_transaction.return_value = mock_tx
        mock_w3.eth.get_transaction_receipt.return_value = mock_receipt
        
        tx, receipt = bot._get_transaction_data(tx_hash)
        
        assert tx == mock_tx
        assert receipt == mock_receipt
        mock_w3.eth.get_transaction.assert_called_once_with(tx_hash)
        mock_w3.eth.get_transaction_receipt.assert_called_once_with(tx_hash)
    
    def test_get_transaction_data_failure(self, bot, mock_w3):
        """Test handling of failure when getting transaction data."""
        tx_hash = "0x123"
        mock_w3.eth.get_transaction.side_effect = Exception("Network error")
        
        tx, receipt = bot._get_transaction_data(tx_hash)
        
        assert tx is None
        assert receipt is None


class TestDecodeTransactionInput:
    """Tests for _decode_transaction_input method."""
    
    def test_decode_as_submit_report_data(self, bot, mock_w3):
        """Test decoding transaction as submitReportData."""
        input_data = "0xabc123"
        decoded_data = {'data': {'requestsCount': 5}}
        
        mock_w3.lido.validator_exit_bus_oracle.decode_submit_report_data.return_value = decoded_data
        
        func_name, data = bot._decode_transaction_input(input_data)
        
        assert func_name == 'submitReportData'
        assert data == decoded_data
        mock_w3.lido.validator_exit_bus_oracle.decode_submit_report_data.assert_called_once_with(input_data)
    
    def test_decode_as_submit_exit_requests_data(self, bot, mock_w3):
        """Test decoding transaction as submitExitRequestsData."""
        input_data = "0xabc123"
        decoded_data = {'request': {'dataFormat': 1}}
        
        mock_w3.lido.validator_exit_bus_oracle.decode_submit_report_data.return_value = None
        mock_w3.lido.validator_exit_bus_oracle.decode_submit_exit_requests_data.return_value = decoded_data
        
        func_name, data = bot._decode_transaction_input(input_data)
        
        assert func_name == 'submitExitRequestsData'
        assert data == decoded_data
    
    def test_decode_fails_both_attempts(self, bot, mock_w3):
        """Test when both decode attempts fail."""
        input_data = "0xabc123"
        
        mock_w3.lido.validator_exit_bus_oracle.decode_submit_report_data.return_value = None
        mock_w3.lido.validator_exit_bus_oracle.decode_submit_exit_requests_data.return_value = None
        
        func_name, data = bot._decode_transaction_input(input_data)
        
        assert func_name is None
        assert data is None


class TestProcessSubmitReportData:
    """Tests for _process_submit_report_data method."""
    
    def test_process_submit_report_data_success(self, bot, mock_w3, sample_validators):
        """Test successfully processing submitReportData."""
        exit_requests_data = b'\x01\x02\x03'
        decoded_data = {
            'data': {
                'data': exit_requests_data,
                'dataFormat': 1,
                'requestsCount': 3,
                'consensusVersion': 1,
                'refSlot': 1000
            }
        }
        
        mock_w3.lido.validator_exit_bus_oracle.decode_all_validators.return_value = sample_validators
        
        bot._process_submit_report_data(decoded_data)
        
        # Check that validators were stored
        data_key = exit_requests_data.hex()
        assert data_key in bot.validators_map
        assert bot.validators_map[data_key] == sample_validators
        assert bot.data_format_map[data_key] == 1
        
        mock_w3.lido.validator_exit_bus_oracle.decode_all_validators.assert_called_once_with(
            exit_requests_data, 1, 3
        )
    
    def test_process_submit_report_data_zero_requests(self, bot, mock_w3):
        """Test processing submitReportData with zero requests."""
        decoded_data = {
            'data': {
                'data': b'',
                'dataFormat': 1,
                'requestsCount': 0
            }
        }
        
        bot._process_submit_report_data(decoded_data)
        
        # Should not decode validators when requestsCount is 0
        mock_w3.lido.validator_exit_bus_oracle.decode_all_validators.assert_not_called()
        assert len(bot.validators_map) == 0


class TestProcessSubmitExitRequestsData:
    """Tests for _process_submit_exit_requests_data method."""
    
    def test_process_submit_exit_requests_data_success(self, bot, mock_w3, sample_validators):
        """Test successfully processing submitExitRequestsData."""
        exit_requests_data = b'\x04\x05\x06'
        decoded_data = {
            'request': {
                'data': exit_requests_data,
                'dataFormat': 1
            }
        }
        
        processing_state = {
            'requestsCount': 3,
            'dataSubmitted': True
        }
        
        mock_w3.lido.validator_exit_bus_oracle.get_processing_state.return_value = processing_state
        mock_w3.lido.validator_exit_bus_oracle.decode_all_validators.return_value = sample_validators
        
        bot._process_submit_exit_requests_data(decoded_data)
        
        # Check that validators were stored
        data_key = exit_requests_data.hex()
        assert data_key in bot.validators_map
        assert bot.validators_map[data_key] == sample_validators
        assert bot.data_format_map[data_key] == 1
        
        mock_w3.lido.validator_exit_bus_oracle.get_processing_state.assert_called_once()
        mock_w3.lido.validator_exit_bus_oracle.decode_all_validators.assert_called_once_with(
            exit_requests_data, 1, 3
        )
    
    def test_process_submit_exit_requests_data_zero_requests(self, bot, mock_w3):
        """Test processing submitExitRequestsData with zero requests."""
        decoded_data = {
            'request': {
                'data': b'',
                'dataFormat': 1
            }
        }
        
        processing_state = {'requestsCount': 0}
        mock_w3.lido.validator_exit_bus_oracle.get_processing_state.return_value = processing_state
        
        bot._process_submit_exit_requests_data(decoded_data)
        
        # Should not decode validators when requestsCount is 0
        mock_w3.lido.validator_exit_bus_oracle.decode_all_validators.assert_not_called()
        assert len(bot.validators_map) == 0


class TestGetValidatorsForData:
    """Tests for get_validators_for_data method."""
    
    def test_get_validators_for_data_with_bytes(self, bot, sample_validators):
        """Test getting validators using bytes key."""
        exit_requests_data = b'\x01\x02\x03'
        data_key = exit_requests_data.hex()
        bot.validators_map[data_key] = sample_validators
        
        result = bot.get_validators_for_data(exit_requests_data)
        
        assert result == sample_validators
    
    def test_get_validators_for_data_with_hex_string(self, bot, sample_validators):
        """Test getting validators using hex string key."""
        data_key = "010203"
        bot.validators_map[data_key] = sample_validators
        
        result = bot.get_validators_for_data(data_key)
        
        assert result == sample_validators
    
    def test_get_validators_for_data_not_found(self, bot):
        """Test getting validators when key doesn't exist."""
        result = bot.get_validators_for_data(b'\x99\x99\x99')
        
        assert result is None


class TestCheckAndTriggerExits:
    """Tests for _check_and_trigger_exits method."""
    
    @patch('trigger_exit_bot.variables')
    def test_check_and_trigger_exits_all_reported(self, mock_variables, bot, mock_w3, mock_cl_client, sample_validators):
        """Test checking and triggering exits for reported validators."""
        mock_variables.MODULES_WHITELIST = [1]
        
        data_key = "010203"
        bot.validators_map[data_key] = sample_validators.copy()
        bot.data_format_map[data_key] = 1
        
        # Mock node operator registry
        mock_registry = Mock()
        mock_registry.is_validator_exiting_key_reported.return_value = True
        mock_w3.lido.node_operator_registry_map[1] = mock_registry
        
        # Mock CL client - all validators not exited
        mock_cl_client.is_validator_exited.return_value = False
        
        # Mock trigger exits transaction
        with patch.object(bot, '_trigger_exits_transaction') as mock_trigger:
            bot._check_and_trigger_exits(data_key)
            
            # Should trigger exits for all 3 validators
            mock_trigger.assert_called_once()
            _, _, validators_to_trigger = mock_trigger.call_args[0]
            assert len(validators_to_trigger) == 3
    
    @patch('trigger_exit_bot.variables')
    def test_check_and_trigger_exits_removes_exited(self, mock_variables, bot, mock_w3, mock_cl_client, sample_validators):
        """Test that exited validators are removed from state."""
        mock_variables.MODULES_WHITELIST = [1]
        
        data_key = "010203"
        bot.validators_map[data_key] = sample_validators.copy()
        bot.data_format_map[data_key] = 1
        
        # Mock node operator registry
        mock_registry = Mock()
        mock_registry.is_validator_exiting_key_reported.return_value = True
        mock_w3.lido.node_operator_registry_map[1] = mock_registry
        
        # First validator is exited, others are not
        mock_cl_client.is_validator_exited.side_effect = [True, False, False]
        
        with patch.object(bot, '_trigger_exits_transaction') as mock_trigger:
            bot._check_and_trigger_exits(data_key)
            
            # Should only trigger for 2 validators (not the exited one)
            mock_trigger.assert_called_once()
            _, _, validators_to_trigger = mock_trigger.call_args[0]
            assert len(validators_to_trigger) == 2
            
            # First validator should be removed from state
            assert len(bot.validators_map[data_key]) == 2
    
    @patch('trigger_exit_bot.variables')
    def test_check_and_trigger_exits_not_reported(self, mock_variables, bot, mock_w3, mock_cl_client, sample_validators):
        """Test that non-reported validators are not triggered."""
        mock_variables.MODULES_WHITELIST = [1]
        
        data_key = "010203"
        bot.validators_map[data_key] = sample_validators.copy()
        bot.data_format_map[data_key] = 1
        
        # Mock node operator registry - validators not reported
        mock_registry = Mock()
        mock_registry.is_validator_exiting_key_reported.return_value = False
        mock_w3.lido.node_operator_registry_map[1] = mock_registry
        
        mock_cl_client.is_validator_exited.return_value = False
        
        with patch.object(bot, '_trigger_exits_transaction') as mock_trigger:
            bot._check_and_trigger_exits(data_key)
            
            # Should not trigger any exits
            mock_trigger.assert_not_called()
    
    @patch('trigger_exit_bot.variables')
    def test_check_and_trigger_exits_module_not_whitelisted(self, mock_variables, bot, mock_w3, mock_cl_client, sample_validators):
        """Test that validators from non-whitelisted modules are skipped."""
        mock_variables.MODULES_WHITELIST = [99]  # Different module ID
        
        data_key = "010203"
        bot.validators_map[data_key] = sample_validators.copy()
        bot.data_format_map[data_key] = 1
        
        mock_cl_client.is_validator_exited.return_value = False
        
        with patch.object(bot, '_trigger_exits_transaction') as mock_trigger:
            bot._check_and_trigger_exits(data_key)
            
            # Should not trigger any exits (module not whitelisted)
            mock_trigger.assert_not_called()
    
    def test_check_and_trigger_exits_no_data(self, bot):
        """Test handling of missing data_key."""
        with patch.object(bot, '_trigger_exits_transaction') as mock_trigger:
            bot._check_and_trigger_exits("nonexistent")
            
            # Should not trigger anything
            mock_trigger.assert_not_called()


class TestTriggerExitsTransaction:
    """Tests for _trigger_exits_transaction method."""
    
    @patch('trigger_exit_bot.variables')
    def test_trigger_exits_transaction_success(self, mock_variables, bot, mock_w3, sample_validators):
        """Test successfully building and sending trigger exits transaction."""
        # Mock account
        mock_account = Mock()
        mock_account.address = "0xBotAddress"
        mock_variables.ACCOUNT = mock_account
        
        data_key = "010203"
        data_format = 1
        
        # Mock withdrawal vault fee
        mock_w3.lido.withdrawal_vault.get_withdrawal_request_fee.return_value = 1000
        
        # Mock trigger_exits function
        mock_tx_function = Mock()
        mock_w3.lido.validator_exit_bus_oracle.trigger_exits.return_value = mock_tx_function
        
        bot._trigger_exits_transaction(data_key, data_format, sample_validators)
        
        # Verify withdrawal fee was fetched
        mock_w3.lido.withdrawal_vault.get_withdrawal_request_fee.assert_called_once()
        
        # Verify trigger_exits was called correctly
        mock_w3.lido.validator_exit_bus_oracle.trigger_exits.assert_called_once()
        call_args = mock_w3.lido.validator_exit_bus_oracle.trigger_exits.call_args
        assert call_args[1]['exits_data'] == bytes.fromhex(data_key)
        assert call_args[1]['data_format'] == data_format
        assert call_args[1]['exit_data_indexes'] == [0, 1, 2]
        assert call_args[1]['refund_recipient'] == "0xBotAddress"
        
        # Verify transaction was checked and sent
        mock_w3.transaction.check.assert_called_once_with(mock_tx_function, value=3000)
        mock_w3.transaction.send.assert_called_once_with(mock_tx_function, timeout_in_blocks=10, value=3000)
    
    @patch('trigger_exit_bot.variables')
    def test_trigger_exits_transaction_no_account(self, mock_variables, bot, mock_w3, sample_validators):
        """Test transaction with no account configured (dry run)."""
        mock_variables.ACCOUNT = None
        
        data_key = "010203"
        data_format = 1
        
        # Mock withdrawal vault fee
        mock_w3.lido.withdrawal_vault.get_withdrawal_request_fee.return_value = 1000
        
        # Mock trigger_exits function
        mock_tx_function = Mock()
        mock_w3.lido.validator_exit_bus_oracle.trigger_exits.return_value = mock_tx_function
        
        bot._trigger_exits_transaction(data_key, data_format, sample_validators)
        
        # Should use zero address as refund recipient
        call_args = mock_w3.lido.validator_exit_bus_oracle.trigger_exits.call_args
        assert call_args[1]['refund_recipient'] == '0x0000000000000000000000000000000000000000'
        
        # Transaction should still be checked and sent
        mock_w3.transaction.check.assert_called_once()
        mock_w3.transaction.send.assert_called_once()
    
    @patch('trigger_exit_bot.variables')
    def test_trigger_exits_transaction_fee_fetch_fails(self, mock_variables, bot, mock_w3, sample_validators):
        """Test handling of failure to fetch withdrawal fee."""
        mock_account = Mock()
        mock_account.address = "0xBotAddress"
        mock_variables.ACCOUNT = mock_account
        
        # Mock withdrawal vault to raise exception
        mock_w3.lido.withdrawal_vault.get_withdrawal_request_fee.side_effect = Exception("RPC error")
        
        data_key = "010203"
        data_format = 1
        
        bot._trigger_exits_transaction(data_key, data_format, sample_validators)
        
        # Should not proceed to trigger exits
        mock_w3.lido.validator_exit_bus_oracle.trigger_exits.assert_not_called()
        mock_w3.transaction.send.assert_not_called()
    
    @patch('trigger_exit_bot.variables')
    def test_trigger_exits_transaction_check_fails(self, mock_variables, bot, mock_w3, sample_validators):
        """Test handling of failed transaction check."""
        mock_account = Mock()
        mock_account.address = "0xBotAddress"
        mock_variables.ACCOUNT = mock_account
        
        data_key = "010203"
        data_format = 1
        
        # Mock withdrawal vault fee
        mock_w3.lido.withdrawal_vault.get_withdrawal_request_fee.return_value = 1000
        
        # Mock trigger_exits function
        mock_tx_function = Mock()
        mock_w3.lido.validator_exit_bus_oracle.trigger_exits.return_value = mock_tx_function
        
        # Mock transaction check to fail
        mock_w3.transaction.check.return_value = False
        
        bot._trigger_exits_transaction(data_key, data_format, sample_validators)
        
        # Should not send transaction
        mock_w3.transaction.send.assert_not_called()


class TestTriggerExitsMainMethod:
    """Tests for main trigger_exits method."""
    
    def test_trigger_exits_processes_events(self, bot, mock_w3):
        """Test that trigger_exits processes events correctly."""
        # Create mock events
        mock_event1 = {
            'args': {'exitRequestsHash': Mock(hex=Mock(return_value='0xhash1'))},
            'blockNumber': 100,
            'transactionHash': Mock(hex=Mock(return_value='0xtx1'))
        }
        mock_event2 = {
            'args': {'exitRequestsHash': Mock(hex=Mock(return_value='0xhash2'))},
            'blockNumber': 101,
            'transactionHash': Mock(hex=Mock(return_value='0xtx2'))
        }
        
        mock_w3.lido.validator_exit_bus_oracle.get_exit_data_processing_events.return_value = [
            mock_event1, mock_event2
        ]
        
        # Mock transaction data
        mock_tx = {'input': '0xabc'}
        mock_receipt = {'status': 1}
        
        with patch.object(bot, '_get_transaction_data', return_value=(mock_tx, mock_receipt)):
            with patch.object(bot, '_decode_transaction_input', return_value=(None, None)):
                with patch.object(bot, '_check_and_trigger_exits'):
                    events = bot.trigger_exits(from_block=0, to_block=200)
        
        # Verify events were fetched
        mock_w3.lido.validator_exit_bus_oracle.get_exit_data_processing_events.assert_called_once_with(
            from_block=0, to_block=200
        )
        
        # Should return the events
        assert len(events) == 2
    
    def test_trigger_exits_skips_failed_transactions(self, bot, mock_w3):
        """Test that failed transactions are skipped."""
        mock_event = {
            'args': {'exitRequestsHash': Mock(hex=Mock(return_value='0xhash'))},
            'blockNumber': 100,
            'transactionHash': Mock(hex=Mock(return_value='0xtx'))
        }
        
        mock_w3.lido.validator_exit_bus_oracle.get_exit_data_processing_events.return_value = [mock_event]
        
        # Mock transaction data with failed status
        mock_tx = {'input': '0xabc'}
        mock_receipt = {'status': 0}  # Failed
        
        with patch.object(bot, '_get_transaction_data', return_value=(mock_tx, mock_receipt)):
            with patch.object(bot, '_decode_transaction_input') as mock_decode:
                bot.trigger_exits(from_block=0, to_block=200)
                
                # Should not attempt to decode failed transaction
                mock_decode.assert_not_called()
    
    def test_trigger_exits_calls_check_for_all_state_entries(self, bot, mock_w3):
        """Test that _check_and_trigger_exits is called for all state entries."""
        # No events
        mock_w3.lido.validator_exit_bus_oracle.get_exit_data_processing_events.return_value = []
        
        # Add some validators to state
        bot.validators_map['key1'] = []
        bot.validators_map['key2'] = []
        bot.data_format_map['key1'] = 1
        bot.data_format_map['key2'] = 1
        
        with patch.object(bot, '_check_and_trigger_exits') as mock_check:
            bot.trigger_exits()
            
            # Should check all state entries
            assert mock_check.call_count == 2
            mock_check.assert_any_call('key1')
            mock_check.assert_any_call('key2')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

