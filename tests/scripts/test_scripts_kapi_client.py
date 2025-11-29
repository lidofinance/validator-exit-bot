"""Simple unit tests for scripts/kapi_client.py"""
import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add scripts to path
scripts_path = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_path))

from scripts.kapi_client import KeysAPIClient, Key, KapiKey


class TestKey:
    """Tests for Key dataclass."""
    
    def test_key_creation(self):
        """Test Key dataclass creation."""
        key = Key(
            module_id=1,
            no_id=10,
            validator_index=123,
            validator_pub_key="0xaabbccdd",
            pub_key_index=5
        )
        
        assert key.module_id == 1
        assert key.no_id == 10
        assert key.validator_index == 123
        assert key.validator_pub_key == "0xaabbccdd"
        assert key.pub_key_index == 5


class TestKapiKey:
    """Tests for KapiKey dataclass."""
    
    def test_kapi_key_creation(self):
        """Test KapiKey dataclass creation."""
        key = KapiKey(
            module_id=1,
            no_id=10,
            validator_pub_key="0xaabbccdd",
            pub_key_index=5
        )
        
        assert key.module_id == 1
        assert key.no_id == 10
        assert key.validator_pub_key == "0xaabbccdd"
        assert key.pub_key_index == 5


class TestKeysAPIClient:
    """Tests for KeysAPIClient class."""
    
    def test_client_initialization(self):
        """Test KeysAPIClient initialization."""
        client = KeysAPIClient("http://test-api.com")
        assert client.url == "http://test-api.com"
    
    @patch('requests.get')
    def test_get_modules_success(self, mock_get):
        """Test get_modules returns correct mapping."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'data': [
                {'stakingModuleAddress': '0xAddress1', 'id': 1},
                {'stakingModuleAddress': '0xAddress2', 'id': 2},
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        client = KeysAPIClient("http://test-api.com")
        modules = client.get_modules()
        
        assert modules == {'0xAddress1': 1, '0xAddress2': 2}
        mock_get.assert_called_once()
    
    @patch('requests.get')
    def test_get_modules_caching(self, mock_get):
        """Test that get_modules uses caching."""
        mock_response = Mock()
        mock_response.json.return_value = {'data': []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        client = KeysAPIClient("http://test-api.com")
        
        # Call twice
        client.get_modules()
        client.get_modules()
        
        # Should only call API once due to caching
        assert mock_get.call_count == 1
    
    @patch('requests.get')
    def test_get_keys_success(self, mock_get):
        """Test get_keys returns correct list of KapiKey objects."""
        def mock_get_impl(url, timeout=None):
            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            
            if 'modules' in url:
                mock_response.json.return_value = {
                    'data': [
                        {'stakingModuleAddress': '0xAddress1', 'id': 1},
                    ]
                }
            elif 'keys' in url:
                mock_response.json.return_value = {
                    'data': [
                        {
                            'moduleAddress': '0xAddress1',
                            'operatorIndex': 10,
                            'key': '0xpubkey1',
                            'index': 5
                        },
                    ]
                }
            return mock_response
        
        mock_get.side_effect = mock_get_impl
        
        client = KeysAPIClient("http://test-api.com")
        keys = client.get_keys()
        
        assert len(keys) == 1
        assert isinstance(keys[0], KapiKey)
        assert keys[0].module_id == 1
        assert keys[0].no_id == 10
        assert keys[0].validator_pub_key == '0xpubkey1'
        assert keys[0].pub_key_index == 5
    
    @patch('requests.get')
    def test_get_keys_http_error(self, mock_get):
        """Test that get_keys handles HTTP errors."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP Error")
        mock_get.return_value = mock_response
        
        client = KeysAPIClient("http://test-api.com")
        
        with pytest.raises(Exception, match="HTTP Error"):
            client.get_keys()

