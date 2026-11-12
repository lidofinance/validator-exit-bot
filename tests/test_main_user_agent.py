"""Unit tests for the clients the bot creates at start."""

from unittest.mock import patch

import pytest
from structlog.testing import capture_logs
from web3_multi_provider import FallbackProvider

from src import main
from src.variables import BUILD_INFO, CONSENSUS_CLIENT_URL, WEB3_RPC_ENDPOINTS

USER_AGENT = f"validator-exit-bot/{BUILD_INFO['version']}"


class TestCreateWeb3:
    """Test the EL provider options."""

    @patch("src.main.Web3")
    @patch("src.main.FallbackProvider")
    def test_el_requests_carry_user_agent_and_content_type(self, mock_provider, _):
        """Test that the headers replace the web3 defaults completely and correctly."""
        endpoints = ["http://el-one.example.com", "http://el-two.example.com"]

        main.create_web3(endpoints)

        mock_provider.assert_called_once_with(
            endpoints,
            cache_allowed_requests=True,
            request_kwargs={
                "headers": {
                    "Content-Type": "application/json",
                    "User-Agent": USER_AGENT,
                }
            },
        )

    def test_every_el_provider_sends_the_headers(self):
        """Test that the provider library hands the headers to each endpoint."""
        headers = {"Content-Type": "application/json", "User-Agent": USER_AGENT}

        provider = FallbackProvider(
            ["http://el-one.example.com", "http://el-two.example.com"],
            cache_allowed_requests=True,
            request_kwargs={"headers": headers},
        )

        sent = [dict(item.get_request_kwargs()) for item in provider.get_providers()]
        assert [kwargs["headers"] for kwargs in sent] == [headers, headers]


class TestStartupLog:
    """Test what the bot logs before its first cycle."""

    def test_start_logs_the_build_and_the_masked_config(self):
        """Test that the dump of main() hides the private values."""
        with (
            patch("src.main.start_health_server"),
            patch("src.main.start_http_server"),
            patch("src.main.web3_multi_provider.init_metrics"),
            patch("src.main.create_web3", side_effect=RuntimeError("stop here")),
            capture_logs() as logs,
            pytest.raises(RuntimeError, match="stop here"),
        ):
            main.main()

        events = {log["event"]["msg"]: log["event"] for log in logs}
        assert events["Start validator exit bot."]["build"] == BUILD_INFO
        dump = events["Bot env variables"]["value"]
        assert dump["WEB3_RPC_ENDPOINTS"] == ["***"] * len(WEB3_RPC_ENDPOINTS)
        assert dump["CONSENSUS_CLIENT_URL"] == ["***"] * len(CONSENSUS_CLIENT_URL)
        assert dump["WALLET_PRIVATE_KEY"] in ("", "***")
        assert "LIDO_LOCATOR" in dump


class TestCreateClClient:
    """Test the CL client options."""

    def test_cl_client_gets_the_whole_list(self):
        """Test that no configured CL endpoint is dropped."""
        client = main.create_cl_client(
            ["http://cl-one.example.com", "http://cl-two.example.com"]
        )

        assert client.urls == [
            "http://cl-one.example.com/",
            "http://cl-two.example.com/",
        ]

    def test_cl_requests_carry_user_agent(self):
        """Test that the CL session names the app and its version."""
        client = main.create_cl_client(["http://cl-one.example.com"])

        assert client._session.headers["User-Agent"] == USER_AGENT
