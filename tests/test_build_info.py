"""Unit tests for the build info loader."""

import json

import pytest
from structlog.testing import capture_logs

from src.utils.build_info import (
    BUILD_INFO_KEYS,
    BUILD_INFO_PATH,
    UNKNOWN,
    load_build_info,
    user_agent,
)


class TestLoadBuildInfo:
    """Test reading version, branch and commit of the build."""

    def test_load_build_info_reads_all_keys(self, tmp_path):
        """Test that the three values of a filled file are returned."""
        path = tmp_path / "build-info.json"
        path.write_text('{"version": "1.2.3", "branch": "main", "commit": "abc123"}')

        assert load_build_info(path) == {
            "version": "1.2.3",
            "branch": "main",
            "commit": "abc123",
        }

    def test_load_build_info_missing_file(self, tmp_path):
        """Test that a missing file gives unknown values without a warning."""
        with capture_logs() as logs:
            info = load_build_info(tmp_path / "absent.json")

        assert info == dict.fromkeys(BUILD_INFO_KEYS, UNKNOWN)
        assert logs == []

    def test_load_build_info_broken_json(self, tmp_path):
        """Test that a broken file gives unknown values and one warning."""
        path = tmp_path / "build-info.json"
        path.write_text("{not json")

        with capture_logs() as logs:
            info = load_build_info(path)

        assert info == dict.fromkeys(BUILD_INFO_KEYS, UNKNOWN)
        assert len(logs) == 1
        assert logs[0]["log_level"] == "warning"

    def test_load_build_info_not_an_object(self, tmp_path):
        """Test that a JSON value that is not an object gives unknown values."""
        path = tmp_path / "build-info.json"
        path.write_text('["1.2.3"]')

        assert load_build_info(path) == dict.fromkeys(BUILD_INFO_KEYS, UNKNOWN)

    def test_load_build_info_partial_and_extra_keys(self, tmp_path):
        """Test that missing or empty keys stay unknown and extra keys are dropped."""
        path = tmp_path / "build-info.json"
        path.write_text('{"version": "1.2.3", "branch": "", "builder": "ci"}')

        assert load_build_info(path) == {
            "version": "1.2.3",
            "branch": UNKNOWN,
            "commit": UNKNOWN,
        }

    def test_tracked_file_has_placeholders_for_all_keys(self):
        """Test that the file in the repo has every key the Docker build fills."""
        data = json.loads(BUILD_INFO_PATH.read_text())

        assert set(data) == set(BUILD_INFO_KEYS)


class TestUserAgent:
    """Test the User-Agent value for outgoing requests."""

    def test_user_agent_with_version(self):
        """Test that the version of the build is part of the value."""
        info = {"version": "1.2.3", "branch": "main", "commit": "abc123"}

        assert user_agent(info) == "validator-exit-bot/1.2.3"

    @pytest.mark.parametrize(
        "version", ["1.2.3-\u0440\u0435\u043b\u0438\u0437", "1.2.3\n"]
    )
    def test_user_agent_drops_a_version_that_is_not_a_header_value(self, version):
        """Test that a version an HTTP client would refuse to send is not used."""
        info = {"version": version, "branch": "main", "commit": "abc123"}

        assert user_agent(info) == f"validator-exit-bot/{UNKNOWN}"

    def test_user_agent_without_build_info_file(self, tmp_path, monkeypatch):
        """Test that a local run without build info still names the app."""
        monkeypatch.setattr(
            "src.utils.build_info.BUILD_INFO_PATH", tmp_path / "absent.json"
        )

        assert user_agent() == f"validator-exit-bot/{UNKNOWN}"
