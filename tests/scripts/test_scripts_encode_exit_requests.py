"""Simple unit tests for scripts/encode_exit_requests.py"""

from eth_typing.encoding import HexStr
import pytest
import sys
from pathlib import Path

# Add scripts to path
scripts_path = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_path))

from scripts.encode_exit_requests import ValidatorExitData
from scripts.kapi_client import Key


class TestValidatorExitData:
    """Tests for ValidatorExitData class."""

    def test_initialization_and_sorting(self):
        """Test that exit requests are sorted correctly on initialization."""
        keys = [
            Key(
                module_id=2,
                no_id=20,
                validator_index=200,
                validator_pub_key=HexStr("0xbb"),
                pub_key_index=2,
            ),
            Key(
                module_id=1,
                no_id=10,
                validator_index=100,
                validator_pub_key=HexStr("0xaa"),
                pub_key_index=1,
            ),
            Key(
                module_id=1,
                no_id=10,
                validator_index=101,
                validator_pub_key=HexStr("0xcc"),
                pub_key_index=3,
            ),
        ]

        ved = ValidatorExitData(keys)

        # Should be sorted by (module_id, no_id, validator_index)
        assert ved.exit_requests[0].validator_index == 100
        assert ved.exit_requests[1].validator_index == 101
        assert ved.exit_requests[2].validator_index == 200

    def test_constants(self):
        """Test that constants are defined correctly."""
        assert ValidatorExitData.MODULE_ID_LENGTH == 3
        assert ValidatorExitData.NODE_OPERATOR_ID_LENGTH == 5
        assert ValidatorExitData.VALIDATOR_INDEX_LENGTH == 8
        assert ValidatorExitData.VALIDATOR_PUB_KEY_LENGTH == 48

    def test_to_veb_calldata_format(self):
        """Test that VEB calldata has correct format and length."""
        # Create a test key with known values
        keys = [
            Key(
                module_id=1,
                no_id=10,
                validator_index=12345,
                validator_pub_key=HexStr("0x" + "ab" * 48),  # 48 bytes
                pub_key_index=5,
            ),
        ]

        ved = ValidatorExitData(keys)
        calldata = ved.to_veb_calldata()

        # VEB format: 3 (module_id) + 5 (no_id) + 8 (validator_index) + 48 (pubkey) = 64 bytes per validator
        # Hex string is 2 chars per byte
        expected_length = 64 * 2
        assert len(calldata) == expected_length
        assert isinstance(calldata, str)
        # Should not have 0x prefix
        assert not calldata.startswith("0x")

    def test_to_veb_calldata_multiple_validators(self):
        """Test VEB calldata with multiple validators."""
        keys = [
            Key(
                module_id=1,
                no_id=10,
                validator_index=100,
                validator_pub_key=HexStr("0x" + "aa" * 48),
                pub_key_index=1,
            ),
            Key(
                module_id=2,
                no_id=20,
                validator_index=200,
                validator_pub_key=HexStr("0x" + "bb" * 48),
                pub_key_index=2,
            ),
        ]

        ved = ValidatorExitData(keys)
        calldata = ved.to_veb_calldata()

        # 2 validators * 64 bytes * 2 hex chars
        expected_length = 2 * 64 * 2
        assert len(calldata) == expected_length

    def test_to_et_calldata_format(self):
        """Test that ET calldata returns hex string."""
        keys = [
            Key(
                module_id=1,
                no_id=10,
                validator_index=12345,
                validator_pub_key=HexStr("0x" + "ab" * 48),
                pub_key_index=5,
            ),
        ]

        ved = ValidatorExitData(keys)
        calldata = ved.to_et_calldata()

        # Should return a hex string (ABI encoded)
        assert isinstance(calldata, str)
        # Should not have 0x prefix
        assert not calldata.startswith("0x")
        # ABI encoding should produce a non-empty string
        assert len(calldata) > 0

    def test_to_et_calldata_multiple_validators(self):
        """Test ET calldata with multiple validators."""
        keys = [
            Key(
                module_id=1,
                no_id=10,
                validator_index=100,
                validator_pub_key=HexStr("0x" + "aa" * 48),
                pub_key_index=1,
            ),
            Key(
                module_id=2,
                no_id=20,
                validator_index=200,
                validator_pub_key=HexStr("0x" + "bb" * 48),
                pub_key_index=2,
            ),
        ]

        ved = ValidatorExitData(keys)
        calldata = ved.to_et_calldata()

        # Should return a non-empty hex string
        assert len(calldata) > 0
        assert isinstance(calldata, str)

    def test_empty_exit_requests(self):
        """Test with empty list of exit requests."""
        ved = ValidatorExitData([])

        veb_calldata = ved.to_veb_calldata()
        et_calldata = ved.to_et_calldata()

        # VEB should be empty
        assert len(veb_calldata) == 0
        # ET should have minimal ABI encoding
        assert len(et_calldata) > 0  # ABI encoding of empty array is not empty

    def test_from_et_calldata_not_implemented(self):
        """Test that from_et_calldata raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            ValidatorExitData.from_et_calldata(HexStr("0x1234"))

    def test_from_veb_calldata_not_implemented(self):
        """Test that from_veb_calldata raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            ValidatorExitData.from_veb_calldata()
