"""Tests of the bot start: where the secrets come from and what reaches the log.

The config is read and logging is configured once, at import, so every case runs in its own process.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

PRIVATE_KEY = "0x" + "11" * 32
EL_URLS = "https://el-one.example.com/v3/el-key-123456,https://el-two.example.com/el-key-abcdef"
CL_URLS = "https://cl-one.example.com/eth/cl-key-654321,https://cl-two.example.com/cl-key-fedcba"
SECRET_PARTS = (
    "11" * 32,
    "el-key-123456",
    "el-key-abcdef",
    "cl-key-654321",
    "cl-key-fedcba",
)

PROBE = """
import json
import logging
import os

import structlog
from logmask import masked_config

from src import variables

logger = structlog.get_logger("probe")
logger.info({"msg": "config", "value": masked_config(variables.PUBLIC_ENV_VARS, variables.PRIVATE_ENV_VARS)})
logger.debug({"msg": "debug line"})
logger.error({"msg": "request failed", "error": "503 Server Error for url: " + variables.CONSENSUS_CLIENT_URL[0]})
logger.error({"msg": "second endpoint failed", "error": "timeout for " + variables.CONSENSUS_CLIENT_URL[-1]})
logger.error({"msg": "signing failed", "error": "bad key " + (variables.WALLET_PRIVATE_KEY or "")})
logging.getLogger("urllib3").warning("Retrying %s", variables.WEB3_RPC_ENDPOINTS[0])
try:
    raise RuntimeError("no answer from " + variables.WEB3_RPC_ENDPOINTS[-1])
except RuntimeError:
    logger.error({"msg": "cycle failed"}, exc_info=True)

expected = os.environ
print(json.dumps({"probe": {
    "el": variables.WEB3_RPC_ENDPOINTS == expected.get("EXPECTED_EL", "").split(","),
    "cl": variables.CONSENSUS_CLIENT_URL == expected.get("EXPECTED_CL", "").split(","),
    "key": (variables.WALLET_PRIVATE_KEY or "") == expected.get("EXPECTED_KEY", ""),
    "account": variables.ACCOUNT is not None,
}}))
"""


def run_bot(env: dict[str, str], code: str = PROBE) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=REPO_ROOT,
        env={"PATH": os.environ["PATH"], **env},
        capture_output=True,
        text=True,
        timeout=120,
    )


def json_lines(result: subprocess.CompletedProcess) -> list[dict]:
    """Parse stdout; a line that is not a JSON object fails the test."""
    lines = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
    assert all(isinstance(line, dict) for line in lines)
    return lines


def probe(result: subprocess.CompletedProcess) -> dict:
    return next(line["probe"] for line in json_lines(result) if "probe" in line)


def event_lines(result: subprocess.CompletedProcess) -> list[dict]:
    return [line for line in json_lines(result) if isinstance(line.get("event"), dict)]


def messages(result: subprocess.CompletedProcess) -> list[str]:
    return [line["event"]["msg"] for line in event_lines(result)]


def find_event(result: subprocess.CompletedProcess, msg: str) -> dict:
    return next(line for line in event_lines(result) if line["event"]["msg"] == msg)


def assert_no_secret(result: subprocess.CompletedProcess):
    output = result.stdout + result.stderr
    for part in SECRET_PARTS:
        assert part not in output


def write_secret(tmp_path: Path, name: str, content: str) -> str:
    path = tmp_path / name
    path.write_text(content)
    return str(path)


@pytest.fixture
def env_config() -> dict[str, str]:
    return {
        "WEB3_RPC_ENDPOINTS": EL_URLS,
        "CONSENSUS_CLIENT_URL": CL_URLS,
        "WALLET_PRIVATE_KEY": PRIVATE_KEY,
        "EXPECTED_EL": EL_URLS,
        "EXPECTED_CL": CL_URLS,
        "EXPECTED_KEY": PRIVATE_KEY,
    }


@pytest.fixture
def file_config(tmp_path) -> dict[str, str]:
    return {
        "WEB3_RPC_ENDPOINTS_FILE": write_secret(tmp_path, "el", EL_URLS + "\n"),
        "CONSENSUS_CLIENT_URL_FILE": write_secret(tmp_path, "cl", CL_URLS + "\n"),
        "WALLET_PRIVATE_KEY_FILE": write_secret(tmp_path, "key", PRIVATE_KEY + "\n"),
        "EXPECTED_EL": EL_URLS,
        "EXPECTED_CL": CL_URLS,
        "EXPECTED_KEY": PRIVATE_KEY,
    }


class TestSecretsSources:
    """Test the values the bot starts with for each source of the secrets."""

    def test_start_through_env(self, env_config):
        """Test that the start with plain variables works as before."""
        result = run_bot(env_config)

        assert result.returncode == 0, result.stdout + result.stderr
        assert probe(result) == {"el": True, "cl": True, "key": True, "account": True}

    def test_start_without_key_is_dry_mode(self):
        """Test the minimal config: two endpoints and no key."""
        env = {
            "WEB3_RPC_ENDPOINTS": EL_URLS,
            "CONSENSUS_CLIENT_URL": CL_URLS,
            "EXPECTED_EL": EL_URLS,
            "EXPECTED_CL": CL_URLS,
        }

        result = run_bot(env)

        assert result.returncode == 0, result.stdout + result.stderr
        assert probe(result) == {"el": True, "cl": True, "key": True, "account": False}
        assert "Account not provided. Run in dry mode." in messages(result)

    def test_secrets_from_files(self, file_config):
        """Test that the content of the files, without the final newline, is the config."""
        result = run_bot(file_config)

        assert result.returncode == 0, result.stdout + result.stderr
        assert probe(result) == {"el": True, "cl": True, "key": True, "account": True}

    def test_file_wins_over_env(self, file_config):
        """Test that a variable is ignored when its file variable is set."""
        env = {
            **file_config,
            "WEB3_RPC_ENDPOINTS": "http://ignored.example.com",
            "CONSENSUS_CLIENT_URL": "http://ignored.example.com",
            "WALLET_PRIVATE_KEY": "0x" + "22" * 32,
        }

        result = run_bot(env)

        assert result.returncode == 0, result.stdout + result.stderr
        assert probe(result) == {"el": True, "cl": True, "key": True, "account": True}

    def test_empty_key_file_is_dry_mode(self, file_config, tmp_path):
        """Test that an empty key file is the same as no key."""
        env = {
            **file_config,
            "WALLET_PRIVATE_KEY_FILE": write_secret(tmp_path, "empty-key", "\n"),
            "EXPECTED_KEY": "",
        }

        result = run_bot(env)

        assert result.returncode == 0, result.stdout + result.stderr
        assert probe(result)["account"] is False

    def test_empty_endpoints_file_stops_the_start(self, file_config, tmp_path):
        """Test that an empty CL file is the same error as an unset variable."""
        env = {
            **file_config,
            "CONSENSUS_CLIENT_URL_FILE": write_secret(tmp_path, "empty-cl", ""),
        }

        result = run_bot(env)

        assert result.returncode != 0
        assert "CONSENSUS_CLIENT_URL environment variable is required" in (
            result.stdout + result.stderr
        )
        assert_no_secret(result)

    def test_missing_file_stops_the_start(self, file_config, tmp_path):
        """Test that a wrong path is reported with the name of the variable."""
        env = {**file_config, "WALLET_PRIVATE_KEY_FILE": str(tmp_path / "absent")}

        result = run_bot(env)

        assert result.returncode != 0
        assert "WALLET_PRIVATE_KEY_FILE" in result.stdout + result.stderr
        assert_no_secret(result)

    def test_endpoints_file_with_one_url_per_line(self, file_config, tmp_path):
        """Test that a file written one URL per line gives separate endpoints."""
        env = {
            **file_config,
            "CONSENSUS_CLIENT_URL_FILE": write_secret(
                tmp_path, "cl-lines", CL_URLS.replace(",", "\n") + "\n"
            ),
        }

        result = run_bot(env)

        assert result.returncode == 0, result.stdout + result.stderr
        assert probe(result)["cl"] is True

    def test_invalid_key_stops_the_start(self, file_config, tmp_path):
        """Test that a key the account library rejects is one masked error line."""
        bad_key = "not-a-hex-key-but-still-a-secret-0123456789"
        env = {
            **file_config,
            "WALLET_PRIVATE_KEY_FILE": write_secret(tmp_path, "bad-key", bad_key),
        }

        result = run_bot(env)

        assert result.returncode != 0
        assert [line["levelname"] for line in json_lines(result)] == ["CRITICAL"]
        assert bad_key not in result.stdout + result.stderr


class TestLogOutput:
    """Test that every line of the start is JSON and carries no secret."""

    @pytest.mark.parametrize("config", ["env_config", "file_config"])
    def test_no_secret_in_the_output(self, config, request):
        """Test the config dump, an error text, a library logger line and a traceback."""
        result = run_bot(request.getfixturevalue(config))

        assert result.returncode == 0, result.stdout + result.stderr
        assert_no_secret(result)
        assert {
            "config",
            "request failed",
            "second endpoint failed",
            "signing failed",
            "cycle failed",
        } <= set(messages(result))

    def test_config_dump_masks_private_values(self, file_config):
        """Test that the dump shows the sources of the secrets and hides their values."""
        result = run_bot(file_config)

        dump = find_event(result, "config")["event"]["value"]
        assert dump["WALLET_PRIVATE_KEY"] == "***"
        assert dump["WEB3_RPC_ENDPOINTS"] == ["***", "***"]
        assert dump["CONSENSUS_CLIENT_URL"] == ["***", "***"]
        assert dump["WALLET_PRIVATE_KEY_FILE"] == file_config["WALLET_PRIVATE_KEY_FILE"]

    def test_unset_key_is_shown_as_empty(self):
        """Test that the dump tells an unset key from a masked one."""
        env = {"WEB3_RPC_ENDPOINTS": EL_URLS, "CONSENSUS_CLIENT_URL": CL_URLS}

        result = run_bot(env)

        dump = find_event(result, "config")["event"]["value"]
        assert dump["WALLET_PRIVATE_KEY"] == ""

    def test_library_logger_line_is_json(self, env_config):
        """Test that a standard-library logger writes a masked JSON line to stdout."""
        result = run_bot(env_config)

        library_lines = [
            line for line in json_lines(result) if line.get("name") == "urllib3"
        ]
        assert len(library_lines) == 1
        assert "***" in json.dumps(library_lines[0])

    def test_traceback_is_in_the_line(self, env_config):
        """Test that an error logged with exc_info carries its traceback."""
        result = run_bot(env_config)

        assert "RuntimeError" in find_event(result, "cycle failed")["exception"]


class TestUnhandledError:
    """Test the last line of a bot that stops on an error."""

    def test_unhandled_error_is_one_masked_json_line(self, env_config):
        """Test that the text of a crash does not carry an endpoint URL."""
        code = (
            "from src import variables\n"
            "raise RuntimeError('down: ' + variables.CONSENSUS_CLIENT_URL[0])\n"
        )

        result = run_bot(env_config, code)

        assert result.returncode == 1
        crash = [
            line for line in json_lines(result) if line.get("levelname") == "CRITICAL"
        ]
        assert len(crash) == 1
        assert "RuntimeError" in json.dumps(crash[0])
        assert_no_secret(result)


class TestLogLevel:
    """Test the LOG_LEVEL variable."""

    def test_default_level_hides_debug(self, env_config):
        """Test that debug lines are not written by default."""
        assert "debug line" not in messages(run_bot(env_config))

    def test_debug_level_in_lower_case(self, env_config):
        """Test that the level name is not case sensitive."""
        result = run_bot({**env_config, "LOG_LEVEL": "debug"})

        assert "debug line" in messages(result)

    def test_unknown_level_stops_the_start(self, env_config):
        """Test that a wrong level name is reported by the name of the variable."""
        result = run_bot({**env_config, "LOG_LEVEL": "LOUD"})

        assert result.returncode != 0
        assert "LOG_LEVEL" in result.stdout + result.stderr
