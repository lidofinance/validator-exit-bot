"""Tests of the bot start: where the secrets come from and what reaches the log.

The config is read and logging is configured once, at import, so every case reloads both modules
with its own environment.
"""

import importlib
import io
import json
import logging
import sys
from pathlib import Path
from types import ModuleType

import pytest
import structlog
from logmask import masked_config

from src import logging_setup, variables

PRIVATE_KEY = "0x" + "11" * 32
EL_URLS = [
    "https://el-one.example.com/v3/el-key-123456",
    "https://el-two.example.com/el-key-abcdef",
]
CL_URLS = [
    "https://cl-one.example.com/eth/cl-key-654321",
    "https://cl-two.example.com/cl-key-fedcba",
]
SECRET_PARTS = (
    "11" * 32,
    "el-key-123456",
    "el-key-abcdef",
    "cl-key-654321",
    "cl-key-fedcba",
)
CONFIG_NAMES = (
    "WEB3_RPC_ENDPOINTS",
    "WEB3_RPC_ENDPOINTS_FILE",
    "CONSENSUS_CLIENT_URL",
    "CONSENSUS_CLIENT_URL_FILE",
    "WALLET_PRIVATE_KEY",
    "WALLET_PRIVATE_KEY_FILE",
    "LOG_LEVEL",
)


@pytest.fixture
def stdout() -> io.StringIO:
    return io.StringIO()


@pytest.fixture
def start_bot(monkeypatch, stdout):
    """Read the config and configure logging again; the original state is back after the test."""

    def start(env: dict[str, str]) -> ModuleType:
        # Here and not in a fixture: pytest puts its own capture back into sys.stdout before the test body.
        monkeypatch.setattr(sys, "stdout", stdout)
        for name in CONFIG_NAMES:
            monkeypatch.delenv(name, raising=False)
        for name, value in env.items():
            monkeypatch.setenv(name, value)
        importlib.reload(logging_setup)
        return importlib.reload(variables)

    yield start
    monkeypatch.undo()
    importlib.reload(logging_setup)
    importlib.reload(variables)


@pytest.fixture
def env_config() -> dict[str, str]:
    return {
        "WEB3_RPC_ENDPOINTS": ",".join(EL_URLS),
        "CONSENSUS_CLIENT_URL": ",".join(CL_URLS),
        "WALLET_PRIVATE_KEY": PRIVATE_KEY,
    }


@pytest.fixture
def file_config(tmp_path) -> dict[str, str]:
    return {
        "WEB3_RPC_ENDPOINTS_FILE": write_secret(
            tmp_path, "el", ",".join(EL_URLS) + "\n"
        ),
        "CONSENSUS_CLIENT_URL_FILE": write_secret(
            tmp_path, "cl", ",".join(CL_URLS) + "\n"
        ),
        "WALLET_PRIVATE_KEY_FILE": write_secret(tmp_path, "key", PRIVATE_KEY + "\n"),
    }


def write_secret(tmp_path: Path, name: str, content: str) -> str:
    path = tmp_path / name
    path.write_text(content)
    return str(path)


def write_log_lines(config: ModuleType):
    """Log every secret of the config in the ways the bot can meet it."""
    logger = structlog.get_logger("test")
    dump = masked_config(config.PUBLIC_ENV_VARS, config.PRIVATE_ENV_VARS)
    logger.info({"msg": "config", "value": dump})
    logger.debug({"msg": "debug line"})
    logger.error({"msg": "request failed", "error": config.CONSENSUS_CLIENT_URL[0]})
    logger.error({"msg": "second failed", "error": config.CONSENSUS_CLIENT_URL[-1]})
    logger.error({"msg": "signing failed", "error": config.WALLET_PRIVATE_KEY or ""})
    logging.getLogger("urllib3").warning("Retrying %s", config.WEB3_RPC_ENDPOINTS[0])
    try:
        raise RuntimeError("no answer from " + config.WEB3_RPC_ENDPOINTS[-1])
    except RuntimeError:
        logger.error({"msg": "cycle failed"}, exc_info=True)


def crash(error: BaseException):
    """Call the hook the interpreter calls for an exception nobody caught."""
    sys.excepthook(type(error), error, error.__traceback__)


def json_lines(stdout: io.StringIO) -> list[dict]:
    """Parse the output; a line that is not a JSON object fails the test."""
    lines = [json.loads(line) for line in stdout.getvalue().splitlines() if line]
    assert all(isinstance(line, dict) for line in lines)
    return lines


def events(stdout: io.StringIO) -> dict[str, dict]:
    """The lines the bot wrote through structlog, by their message."""
    return {
        line["event"]["msg"]: line
        for line in json_lines(stdout)
        if isinstance(line.get("event"), dict)
    }


def assert_no_secret(text: str):
    for part in SECRET_PARTS:
        assert part not in text


class TestSecretsSources:
    """Test the values the bot starts with for each source of the secrets."""

    def test_start_through_env(self, start_bot, env_config):
        """Test that the start with plain variables works as before."""
        config = start_bot(env_config)

        assert config.WEB3_RPC_ENDPOINTS == EL_URLS
        assert config.CONSENSUS_CLIENT_URL == CL_URLS
        assert config.WALLET_PRIVATE_KEY == PRIVATE_KEY
        assert config.ACCOUNT is not None

    def test_start_without_key_is_dry_mode(self, start_bot, env_config, stdout):
        """Test the minimal config: two endpoints and no key."""
        del env_config["WALLET_PRIVATE_KEY"]

        config = start_bot(env_config)

        assert config.WEB3_RPC_ENDPOINTS == EL_URLS
        assert config.CONSENSUS_CLIENT_URL == CL_URLS
        assert config.ACCOUNT is None
        assert "Account not provided. Run in dry mode." in events(stdout)

    def test_secrets_from_files(self, start_bot, file_config):
        """Test that the content of the files, without the final newline, is the config."""
        config = start_bot(file_config)

        assert config.WEB3_RPC_ENDPOINTS == EL_URLS
        assert config.CONSENSUS_CLIENT_URL == CL_URLS
        assert config.WALLET_PRIVATE_KEY == PRIVATE_KEY
        assert config.ACCOUNT is not None

    def test_file_wins_over_env(self, start_bot, file_config):
        """Test that a variable is ignored when its file variable is set."""
        env = {
            **file_config,
            "WEB3_RPC_ENDPOINTS": "http://ignored.example.com",
            "CONSENSUS_CLIENT_URL": "http://ignored.example.com",
            "WALLET_PRIVATE_KEY": "0x" + "22" * 32,
        }

        config = start_bot(env)

        assert config.WEB3_RPC_ENDPOINTS == EL_URLS
        assert config.CONSENSUS_CLIENT_URL == CL_URLS
        assert config.WALLET_PRIVATE_KEY == PRIVATE_KEY

    def test_empty_key_file_is_dry_mode(self, start_bot, file_config, tmp_path):
        """Test that an empty key file is the same as no key."""
        file_config["WALLET_PRIVATE_KEY_FILE"] = write_secret(tmp_path, "empty", "\n")

        config = start_bot(file_config)

        assert config.ACCOUNT is None

    def test_empty_endpoints_file_stops_the_start(
        self, start_bot, file_config, tmp_path, stdout
    ):
        """Test that an empty CL file is the same error as an unset variable."""
        file_config["CONSENSUS_CLIENT_URL_FILE"] = write_secret(tmp_path, "empty", "")

        with pytest.raises(
            ValueError, match="CONSENSUS_CLIENT_URL environment variable is required"
        ) as error:
            start_bot(file_config)

        assert_no_secret(stdout.getvalue() + str(error.value))

    def test_missing_file_stops_the_start(
        self, start_bot, file_config, tmp_path, stdout
    ):
        """Test that a wrong path is reported with the name of the variable."""
        file_config["WALLET_PRIVATE_KEY_FILE"] = str(tmp_path / "absent")

        with pytest.raises(ValueError, match="WALLET_PRIVATE_KEY_FILE") as error:
            start_bot(file_config)

        assert_no_secret(stdout.getvalue() + str(error.value))

    def test_endpoints_file_with_one_url_per_line(
        self, start_bot, file_config, tmp_path
    ):
        """Test that a file written one URL per line gives separate endpoints."""
        file_config["CONSENSUS_CLIENT_URL_FILE"] = write_secret(
            tmp_path, "cl-lines", "\n".join(CL_URLS) + "\n"
        )

        config = start_bot(file_config)

        assert config.CONSENSUS_CLIENT_URL == CL_URLS

    def test_invalid_key_stops_the_start(
        self, start_bot, file_config, tmp_path, stdout
    ):
        """Test that a key the account library rejects is one masked error line."""
        bad_key = "not-a-hex-key-but-still-a-secret-0123456789"
        file_config["WALLET_PRIVATE_KEY_FILE"] = write_secret(tmp_path, "bad", bad_key)

        with pytest.raises(ValueError) as error:
            start_bot(file_config)
        crash(error.value)

        assert [line["levelname"] for line in json_lines(stdout)] == ["CRITICAL"]
        assert bad_key not in stdout.getvalue()


class TestLogOutput:
    """Test that every line of the start is JSON and carries no secret."""

    @pytest.mark.parametrize("config_name", ["env_config", "file_config"])
    def test_no_secret_in_the_output(self, config_name, request, start_bot, stdout):
        """Test the config dump, an error text, a library logger line and a traceback."""
        write_log_lines(start_bot(request.getfixturevalue(config_name)))

        assert_no_secret(stdout.getvalue())
        assert {
            "config",
            "request failed",
            "second failed",
            "signing failed",
            "cycle failed",
        } <= set(events(stdout))

    def test_config_dump_masks_private_values(self, start_bot, file_config, stdout):
        """Test that the dump shows the sources of the secrets and hides their values."""
        write_log_lines(start_bot(file_config))

        dump = events(stdout)["config"]["event"]["value"]
        assert dump["WALLET_PRIVATE_KEY"] == "***"
        assert dump["WEB3_RPC_ENDPOINTS"] == ["***", "***"]
        assert dump["CONSENSUS_CLIENT_URL"] == ["***", "***"]
        assert dump["WALLET_PRIVATE_KEY_FILE"] == file_config["WALLET_PRIVATE_KEY_FILE"]

    def test_unset_key_is_shown_as_empty(self, start_bot, env_config, stdout):
        """Test that the dump tells an unset key from a masked one."""
        del env_config["WALLET_PRIVATE_KEY"]

        write_log_lines(start_bot(env_config))

        assert events(stdout)["config"]["event"]["value"]["WALLET_PRIVATE_KEY"] == ""

    def test_library_logger_line_is_json(self, start_bot, env_config, stdout):
        """Test that a standard-library logger writes a masked JSON line to stdout."""
        write_log_lines(start_bot(env_config))

        library_lines = [
            line for line in json_lines(stdout) if line.get("name") == "urllib3"
        ]
        assert len(library_lines) == 1
        assert "***" in json.dumps(library_lines[0])

    def test_traceback_is_in_the_line(self, start_bot, env_config, stdout):
        """Test that an error logged with exc_info carries its traceback."""
        write_log_lines(start_bot(env_config))

        assert "RuntimeError" in events(stdout)["cycle failed"]["exception"]


class TestUnhandledError:
    """Test the last line of a bot that stops on an error."""

    def test_unhandled_error_is_one_masked_json_line(
        self, start_bot, env_config, stdout
    ):
        """Test that the text of a crash does not carry an endpoint URL."""
        config = start_bot(env_config)

        crash(RuntimeError("down: " + config.CONSENSUS_CLIENT_URL[0]))

        lines = [
            line for line in json_lines(stdout) if line.get("levelname") == "CRITICAL"
        ]
        assert len(lines) == 1
        assert "RuntimeError" in json.dumps(lines[0])
        assert_no_secret(stdout.getvalue())


class TestLogLevel:
    """Test the LOG_LEVEL variable."""

    def test_default_level_hides_debug(self, start_bot, env_config, stdout):
        """Test that debug lines are not written by default."""
        write_log_lines(start_bot(env_config))

        assert "debug line" not in events(stdout)

    def test_debug_level_in_lower_case(self, start_bot, env_config, stdout):
        """Test that the level name is not case sensitive."""
        write_log_lines(start_bot({**env_config, "LOG_LEVEL": "debug"}))

        assert "debug line" in events(stdout)

    def test_unknown_level_stops_the_start(self, start_bot, env_config):
        """Test that a wrong level name is reported by the name of the variable."""
        with pytest.raises(ValueError, match="LOG_LEVEL"):
            start_bot({**env_config, "LOG_LEVEL": "LOUD"})
