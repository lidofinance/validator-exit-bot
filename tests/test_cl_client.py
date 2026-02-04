"""Unit tests for CLClient."""

from unittest.mock import Mock, patch

import pytest
import requests
from eth_typing import HexStr

from src.utils.cl_client import CLClient


class TestCLClientInit:
    """Test CLClient initialization and URL normalization."""

    def test_url_without_trailing_slash(self):
        """Test that URL without trailing slash gets one added."""
        client = CLClient("https://beacon.example.com")
        assert client.url == "https://beacon.example.com/"

    def test_url_with_trailing_slash(self):
        """Test that URL with trailing slash stays normalized."""
        client = CLClient("https://beacon.example.com/")
        assert client.url == "https://beacon.example.com/"

    def test_url_with_path_and_no_trailing_slash(self):
        """Test that URL with path component gets trailing slash added."""
        client = CLClient("https://lb.drpc.org/eth-beacon-chain/API_KEY")
        assert client.url == "https://lb.drpc.org/eth-beacon-chain/API_KEY/"

    def test_url_with_path_and_trailing_slash(self):
        """Test that URL with path and trailing slash stays normalized."""
        client = CLClient("https://lb.drpc.org/eth-beacon-chain/API_KEY/")
        assert client.url == "https://lb.drpc.org/eth-beacon-chain/API_KEY/"

    def test_url_with_multiple_trailing_slashes(self):
        """Test that multiple trailing slashes are normalized to one."""
        client = CLClient("https://beacon.example.com///")
        assert client.url == "https://beacon.example.com/"


class TestCLClientGetAllValidators:
    """Test get_all_validators method."""

    @patch("src.utils.cl_client.requests.get")
    def test_get_all_validators_success(self, mock_get):
        """Test successful retrieval of all validators."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {"index": "0", "validator": {"pubkey": "0xabc123"}},
                {"index": "1", "validator": {"pubkey": "0xdef456"}},
            ]
        }
        mock_get.return_value = mock_response

        client = CLClient("https://beacon.example.com")
        validators = client.get_all_validators()

        assert len(validators) == 2
        assert validators[0]["index"] == "0"
        mock_get.assert_called_once_with(
            "https://beacon.example.com/eth/v1/beacon/states/head/validators",
            timeout=60,
        )

    @patch("src.utils.cl_client.requests.get")
    def test_get_all_validators_with_api_key_in_url(self, mock_get):
        """Test that API key path is preserved in URL construction."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": []}
        mock_get.return_value = mock_response

        client = CLClient("https://lb.drpc.org/eth-beacon-chain/API_KEY")
        client.get_all_validators()

        # Verify the API key path is preserved
        mock_get.assert_called_once_with(
            "https://lb.drpc.org/eth-beacon-chain/API_KEY/eth/v1/beacon/states/head/validators",
            timeout=60,
        )

    @patch("src.utils.cl_client.requests.get")
    def test_get_all_validators_http_error(self, mock_get):
        """Test that HTTP errors are raised."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404")
        mock_get.return_value = mock_response

        client = CLClient("https://beacon.example.com")
        with pytest.raises(requests.HTTPError):
            client.get_all_validators()


class TestCLClientGetValidatorsByIndexes:
    """Test get_validators_by_indexes method."""

    @patch("src.utils.cl_client.requests.get")
    def test_get_validators_by_indexes_success(self, mock_get):
        """Test successful retrieval and mapping of validators by index."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {"index": "0", "validator": {"pubkey": "0xabc123"}},
                {"index": "1", "validator": {"pubkey": "0xdef456"}},
            ]
        }
        mock_get.return_value = mock_response

        client = CLClient("https://beacon.example.com")
        validators = client.get_validators_by_indexes()

        assert len(validators) == 2
        assert validators[0] == HexStr("0xabc123")
        assert validators[1] == HexStr("0xdef456")


class TestCLClientEnsure0xPrefix:
    """Test _ensure_0x_prefix static method."""

    def test_ensure_0x_prefix_with_prefix(self):
        """Test that pubkey with 0x prefix is unchanged."""
        pubkey = HexStr("0xabc123")
        result = CLClient._ensure_0x_prefix(pubkey)
        assert result == "0xabc123"

    def test_ensure_0x_prefix_without_prefix(self):
        """Test that pubkey without 0x prefix gets it added."""
        pubkey = HexStr("abc123")
        result = CLClient._ensure_0x_prefix(pubkey)
        assert result == "0xabc123"


class TestCLClientGetValidatorIndexByPubkey:
    """Test get_validator_index_by_pubkey method."""

    @patch("src.utils.cl_client.requests.get")
    def test_get_validator_index_by_pubkey_success(self, mock_get):
        """Test successful retrieval of validator index."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {"index": "12345", "validator": {"pubkey": "0xabc123"}}
        }
        mock_get.return_value = mock_response

        client = CLClient("https://beacon.example.com")
        pubkey = HexStr("0xabc123")
        index = client.get_validator_index_by_pubkey(pubkey)

        assert index == 12345
        mock_get.assert_called_once_with(
            "https://beacon.example.com/eth/v1/beacon/states/head/validators/0xabc123",
            timeout=10,
        )

    @patch("src.utils.cl_client.requests.get")
    def test_get_validator_index_by_pubkey_without_0x_prefix(self, mock_get):
        """Test that pubkey without 0x prefix is handled correctly."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {"index": "12345", "validator": {"pubkey": "0xabc123"}}
        }
        mock_get.return_value = mock_response

        client = CLClient("https://beacon.example.com")
        pubkey = HexStr("abc123")  # No 0x prefix
        index = client.get_validator_index_by_pubkey(pubkey)

        assert index == 12345
        # Verify 0x was added to the URL
        mock_get.assert_called_once_with(
            "https://beacon.example.com/eth/v1/beacon/states/head/validators/0xabc123",
            timeout=10,
        )

    @patch("src.utils.cl_client.requests.get")
    def test_get_validator_index_by_pubkey_with_api_key(self, mock_get):
        """Test that pubkey endpoint preserves API key in URL."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": {"index": "12345"}}
        mock_get.return_value = mock_response

        client = CLClient("https://lb.drpc.org/eth-beacon-chain/API_KEY")
        pubkey = HexStr("0xabc123")
        client.get_validator_index_by_pubkey(pubkey)

        mock_get.assert_called_once_with(
            "https://lb.drpc.org/eth-beacon-chain/API_KEY/eth/v1/beacon/states/head/validators/0xabc123",
            timeout=10,
        )

    @patch("src.utils.cl_client.requests.get")
    def test_get_validator_index_by_pubkey_not_found(self, mock_get):
        """Test error handling when validator not found."""
        mock_response = Mock()
        mock_response.json.return_value = {"error": "Validator not found"}
        mock_get.return_value = mock_response

        client = CLClient("https://beacon.example.com")
        pubkey = HexStr("0xabc123")

        with pytest.raises(ValueError, match="Validator not found in CL"):
            client.get_validator_index_by_pubkey(pubkey)


class TestCLClientGetValidatorByPubkey:
    """Test get_validator_by_pubkey method."""

    @patch("src.utils.cl_client.requests.get")
    def test_get_validator_by_pubkey_success(self, mock_get):
        """Test successful retrieval of validator data."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "index": "12345",
                "status": "active_ongoing",
                "validator": {"pubkey": "0xabc123"},
            }
        }
        mock_get.return_value = mock_response

        client = CLClient("https://beacon.example.com")
        pubkey = HexStr("0xabc123")
        validator = client.get_validator_by_pubkey(pubkey)

        assert validator is not None
        assert validator["index"] == "12345"
        assert validator["status"] == "active_ongoing"

    @patch("src.utils.cl_client.requests.get")
    def test_get_validator_by_pubkey_api_error(self, mock_get):
        """Test handling of API error response."""
        mock_response = Mock()
        mock_response.json.return_value = {"error": "Validator not found"}
        mock_get.return_value = mock_response

        client = CLClient("https://beacon.example.com")
        pubkey = HexStr("0xabc123")
        validator = client.get_validator_by_pubkey(pubkey)

        assert validator is None

    @patch("src.utils.cl_client.requests.get")
    def test_get_validator_by_pubkey_http_error(self, mock_get):
        """Test handling of HTTP errors (404, 500, etc)."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        client = CLClient("https://beacon.example.com")
        pubkey = HexStr("0xabc123")
        validator = client.get_validator_by_pubkey(pubkey)

        assert validator is None

    @patch("src.utils.cl_client.requests.get")
    def test_get_validator_by_pubkey_timeout(self, mock_get):
        """Test handling of request timeout."""
        mock_get.side_effect = requests.Timeout("Request timed out")

        client = CLClient("https://beacon.example.com")
        pubkey = HexStr("0xabc123")
        validator = client.get_validator_by_pubkey(pubkey)

        assert validator is None

    @patch("src.utils.cl_client.requests.get")
    def test_get_validator_by_pubkey_without_0x_prefix(self, mock_get):
        """Test that pubkey without 0x prefix is handled correctly."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "index": "12345",
                "status": "active_ongoing",
                "validator": {"pubkey": "0xabc123"},
            }
        }
        mock_get.return_value = mock_response

        client = CLClient("https://beacon.example.com")
        pubkey = HexStr("abc123")  # No 0x prefix
        validator = client.get_validator_by_pubkey(pubkey)

        assert validator is not None
        # Verify 0x was added to the URL
        mock_get.assert_called_once_with(
            "https://beacon.example.com/eth/v1/beacon/states/head/validators/0xabc123",
            timeout=10,
        )


class TestCLClientIsValidatorExited:
    """Test is_validator_exited method."""

    @patch("src.utils.cl_client.requests.get")
    def test_is_validator_exited_active_ongoing(self, mock_get):
        """Test validator that is still active."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {"status": "active_ongoing", "validator": {"pubkey": "0xabc123"}}
        }
        mock_get.return_value = mock_response

        client = CLClient("https://beacon.example.com")
        pubkey = HexStr("0xabc123")
        is_exited, is_error = client.is_validator_exited(pubkey)

        assert is_exited is False
        assert is_error is False

    @patch("src.utils.cl_client.requests.get")
    def test_is_validator_exited_active_exiting(self, mock_get):
        """Test validator that is in the process of exiting."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {"status": "active_exiting", "validator": {"pubkey": "0xabc123"}}
        }
        mock_get.return_value = mock_response

        client = CLClient("https://beacon.example.com")
        pubkey = HexStr("0xabc123")
        is_exited, is_error = client.is_validator_exited(pubkey)

        assert is_exited is True
        assert is_error is False

    @patch("src.utils.cl_client.requests.get")
    def test_is_validator_exited_exited_unslashed(self, mock_get):
        """Test validator that has exited."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {"status": "exited_unslashed", "validator": {"pubkey": "0xabc123"}}
        }
        mock_get.return_value = mock_response

        client = CLClient("https://beacon.example.com")
        pubkey = HexStr("0xabc123")
        is_exited, is_error = client.is_validator_exited(pubkey)

        assert is_exited is True
        assert is_error is False

    @patch("src.utils.cl_client.requests.get")
    def test_is_validator_exited_withdrawal_done(self, mock_get):
        """Test validator that has fully withdrawn."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {"status": "withdrawal_done", "validator": {"pubkey": "0xabc123"}}
        }
        mock_get.return_value = mock_response

        client = CLClient("https://beacon.example.com")
        pubkey = HexStr("0xabc123")
        is_exited, is_error = client.is_validator_exited(pubkey)

        assert is_exited is True
        assert is_error is False

    @patch("src.utils.cl_client.requests.get")
    def test_is_validator_exited_cl_error(self, mock_get):
        """Test handling of CL API errors."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        client = CLClient("https://beacon.example.com")
        pubkey = HexStr("0xabc123")
        is_exited, is_error = client.is_validator_exited(pubkey)

        assert is_exited is False
        assert is_error is True

    @patch("src.utils.cl_client.requests.get")
    def test_is_validator_exited_api_returns_error(self, mock_get):
        """Test when API returns error in response."""
        mock_response = Mock()
        mock_response.json.return_value = {"error": "Validator not found"}
        mock_get.return_value = mock_response

        client = CLClient("https://beacon.example.com")
        pubkey = HexStr("0xabc123")
        is_exited, is_error = client.is_validator_exited(pubkey)

        assert is_exited is False
        assert is_error is True

    @patch("src.utils.cl_client.requests.get")
    def test_is_validator_exited_case_insensitive(self, mock_get):
        """Test that status comparison is case insensitive."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {"status": "ACTIVE_EXITING", "validator": {"pubkey": "0xabc123"}}
        }
        mock_get.return_value = mock_response

        client = CLClient("https://beacon.example.com")
        pubkey = HexStr("0xabc123")
        is_exited, is_error = client.is_validator_exited(pubkey)

        assert is_exited is True
        assert is_error is False
