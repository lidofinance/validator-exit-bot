"""Unit tests for reading a config value from a file or from the environment."""

import pytest

from src.utils.env import from_file_or_env, split_endpoints

NAME = "EXIT_BOT_TEST_SECRET"
FILE_NAME = f"{NAME}_FILE"


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    monkeypatch.delenv(NAME, raising=False)
    monkeypatch.delenv(FILE_NAME, raising=False)


class TestFromFileOrEnv:
    """Test the source and the form of the returned value."""

    def test_returns_env_value_when_file_variable_is_unset(self, monkeypatch):
        """Test that the start through env works as before."""
        monkeypatch.setenv(NAME, "from-env")

        assert from_file_or_env(NAME) == "from-env"

    def test_returns_none_when_nothing_is_set(self):
        """Test that an unset variable without a file gives None."""
        assert from_file_or_env(NAME) is None

    def test_file_wins_over_env(self, monkeypatch, tmp_path):
        """Test that the file is used when both sources are set."""
        path = tmp_path / "secret"
        path.write_text("from-file")
        monkeypatch.setenv(NAME, "from-env")
        monkeypatch.setenv(FILE_NAME, str(path))

        assert from_file_or_env(NAME) == "from-file"

    def test_empty_file_variable_falls_back_to_env(self, monkeypatch):
        """Test that an empty path is the same as no path."""
        monkeypatch.setenv(NAME, "from-env")
        monkeypatch.setenv(FILE_NAME, "")

        assert from_file_or_env(NAME) == "from-env"

    @pytest.mark.parametrize("tail", ["\n", "\r\n", "  \n\n", "\t"])
    def test_trailing_whitespace_is_dropped(self, monkeypatch, tmp_path, tail):
        """Test that the newline an editor or a template adds is not part of the value."""
        path = tmp_path / "secret"
        path.write_text(f"value{tail}")
        monkeypatch.setenv(FILE_NAME, str(path))

        assert from_file_or_env(NAME) == "value"

    def test_leading_whitespace_is_kept(self, monkeypatch, tmp_path):
        """Test that only the end of the content is trimmed."""
        path = tmp_path / "secret"
        path.write_text("  value\n")
        monkeypatch.setenv(FILE_NAME, str(path))

        assert from_file_or_env(NAME) == "  value"

    def test_empty_file_gives_empty_string_and_ignores_env(self, monkeypatch, tmp_path):
        """Test that an empty file means no value even when the env has one."""
        path = tmp_path / "secret"
        path.write_text("\n")
        monkeypatch.setenv(NAME, "from-env")
        monkeypatch.setenv(FILE_NAME, str(path))

        assert from_file_or_env(NAME) == ""

    def test_missing_file_raises_with_variable_name(self, monkeypatch, tmp_path):
        """Test that a wrong path stops the start and names the variable."""
        monkeypatch.setenv(FILE_NAME, str(tmp_path / "absent"))

        with pytest.raises(ValueError, match=FILE_NAME):
            from_file_or_env(NAME)

    def test_directory_raises_value_error(self, monkeypatch, tmp_path):
        """Test that a path to a directory stops the start."""
        monkeypatch.setenv(FILE_NAME, str(tmp_path))

        with pytest.raises(ValueError, match=FILE_NAME):
            from_file_or_env(NAME)

    def test_non_utf8_file_raises_without_content(self, monkeypatch, tmp_path):
        """Test that the error of an unreadable file carries no bytes of the secret."""
        path = tmp_path / "secret"
        path.write_bytes(b"topsecret\xff\xfe")
        monkeypatch.setenv(FILE_NAME, str(path))

        with pytest.raises(ValueError) as raised:
            from_file_or_env(NAME)

        assert "topsecret" not in str(raised.value)
        assert raised.value.__cause__ is None
        assert raised.value.__suppress_context__ is True


class TestSplitEndpoints:
    """Test the parsing of a list of endpoint URLs."""

    @pytest.mark.parametrize(
        "value",
        [
            "http://a:8545,http://b:8545",
            "http://a:8545, http://b:8545",
            "http://a:8545\nhttp://b:8545\n",
            "http://a:8545,\r\nhttp://b:8545,",
            " http://a:8545 ,http://b:8545 ",
        ],
    )
    def test_commas_and_whitespace_separate_the_urls(self, value):
        """Test that one URL per line is not read as one endpoint."""
        assert split_endpoints(value) == ["http://a:8545", "http://b:8545"]

    @pytest.mark.parametrize("value", [None, "", " ", ",", "\n"])
    def test_no_url_gives_an_empty_list(self, value):
        """Test that a value without a URL has no endpoints."""
        assert split_endpoints(value) == []
