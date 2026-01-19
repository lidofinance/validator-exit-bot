"""Simple unit tests for scripts/exit_request.py"""

from unittest.mock import Mock

import pytest
from eth_typing.encoding import HexStr

from scripts.exit_request import build_exit_request
from scripts.kapi_client import KapiKey


class TestBuildExitRequest:
    """Tests for build_exit_request function."""

    def test_build_exit_request_success(self):
        """Test successful exit request building."""
        # Mock CL client
        mock_cl_client = Mock()
        mock_cl_client.get_validators_by_indexes.return_value = {
            123: "0xaabbccdd",
            456: "0x11223344",
        }

        # Mock KAPI client
        mock_kapi_client = Mock()
        mock_kapi_client.get_keys.return_value = [
            KapiKey(
                module_id=1,
                no_id=10,
                validator_pub_key=HexStr("0xaabbccdd"),
                pub_key_index=5,
            ),
            KapiKey(
                module_id=2,
                no_id=20,
                validator_pub_key=HexStr("0x11223344"),
                pub_key_index=15,
            ),
        ]

        validator_indexes = [123, 456]
        result = build_exit_request(mock_kapi_client, mock_cl_client, validator_indexes)

        assert len(result) == 2
        assert result[0].module_id == 1
        assert result[0].no_id == 10
        assert result[0].validator_index == 123
        assert result[0].validator_pub_key == "0xaabbccdd"
        assert result[0].pub_key_index == 5

        assert result[1].module_id == 2
        assert result[1].no_id == 20
        assert result[1].validator_index == 456
        assert result[1].validator_pub_key == "0x11223344"
        assert result[1].pub_key_index == 15

    def test_build_exit_request_validator_not_found_in_cl(self):
        """Test error when validator index is not found in CL."""
        mock_cl_client = Mock()
        mock_cl_client.get_validators_by_indexes.return_value = {123: "0xaabbccdd"}

        mock_kapi_client = Mock()
        mock_kapi_client.get_keys.return_value = []

        validator_indexes = [999]  # Not in CL

        with pytest.raises(ValueError, match="Validator index 999 not found in CL"):
            build_exit_request(mock_kapi_client, mock_cl_client, validator_indexes)

    def test_build_exit_request_pubkey_not_found_in_kapi(self):
        """Test error when validator pubkey is not found in KAPI."""
        mock_cl_client = Mock()
        mock_cl_client.get_validators_by_indexes.return_value = {123: "0xaabbccdd"}

        mock_kapi_client = Mock()
        mock_kapi_client.get_keys.return_value = [
            KapiKey(
                module_id=1,
                no_id=10,
                validator_pub_key=HexStr("0x99999999"),
                pub_key_index=5,
            ),
        ]

        validator_indexes = [123]

        with pytest.raises(
            ValueError, match="Validator pubkey 0xaabbccdd not found in KAPI"
        ):
            build_exit_request(mock_kapi_client, mock_cl_client, validator_indexes)

    def test_build_exit_request_empty_list(self):
        """Test with empty validator list."""
        mock_cl_client = Mock()
        mock_cl_client.get_validators_by_indexes.return_value = {}

        mock_kapi_client = Mock()
        mock_kapi_client.get_keys.return_value = []

        validator_indexes = []
        result = build_exit_request(mock_kapi_client, mock_cl_client, validator_indexes)

        assert len(result) == 0
