"""Unit tests for the fallback between Consensus Layer endpoints."""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
import requests
from eth_typing import HexStr
from structlog.testing import capture_logs

from src.utils.cl_client import CLClient

FIRST = "https://first.example.com/key-one"
SECOND = "https://second.example.com/key-two"
PUBKEY = HexStr("0xabc123")
VALIDATOR_PATH = "/eth/v1/beacon/states/head/validators/0xabc123"
VALIDATOR = {
    "index": "12345",
    "status": "active_ongoing",
    "validator": {"pubkey": "0xabc123"},
}
SESSION_GET = "src.utils.cl_client.requests.Session.get"


def make_response(
    status: int, body: Any = None, text: str | None = None
) -> requests.Response:
    response = requests.Response()
    response.status_code = status
    content = text if text is not None else json.dumps(body)
    response._content = content.encode()
    return response


def answer() -> requests.Response:
    return make_response(200, {"data": VALIDATOR})


NO_ANSWER = [
    pytest.param(requests.ConnectionError("refused"), id="connection-error"),
    pytest.param(requests.ConnectTimeout("connect"), id="connect-timeout"),
    pytest.param(requests.ReadTimeout("read"), id="read-timeout"),
    pytest.param(requests.exceptions.ChunkedEncodingError("cut"), id="cut-body"),
    pytest.param(requests.HTTPError("no response"), id="http-error-no-response"),
    pytest.param(make_response(500, {}), id="500"),
    pytest.param(make_response(502, text="bad gateway"), id="502"),
    pytest.param(make_response(503, {}), id="503"),
    pytest.param(make_response(429, {}), id="429"),
    pytest.param(make_response(408, {}), id="408"),
    pytest.param(make_response(401, {}), id="401"),
    pytest.param(make_response(403, {}), id="403"),
    pytest.param(make_response(200, text="<html>"), id="not-json"),
    pytest.param(make_response(200, {}), id="no-data"),
    pytest.param(make_response(200, {"data": None}), id="null-data"),
    pytest.param(make_response(200, []), id="not-an-object"),
    pytest.param(make_response(200, {"data": {}}), id="no-status"),
    pytest.param(make_response(200, {"data": {"status": ""}}), id="empty-status"),
    pytest.param(
        make_response(200, {"data": {"status": "syncing"}}), id="unknown-status"
    ),
    pytest.param(make_response(200, {"data": {"status": None}}), id="null-status"),
]

FINAL = [
    pytest.param(make_response(404, {"message": "not found"}), id="404"),
    pytest.param(make_response(400, {"message": "bad request"}), id="400"),
    pytest.param(make_response(200, {"error": "not found"}), id="error-body"),
]


class TestCLClientInitUrls:
    """Test the endpoint list and the session of the client."""

    def test_list_of_urls_is_kept_in_order(self):
        """Test that every URL is normalized and the order is the configured one."""
        client = CLClient([FIRST, SECOND + "/"])

        assert client.urls == [FIRST + "/", SECOND + "/"]

    def test_blank_items_are_dropped(self):
        """Test that a trailing comma in the variable does not add an endpoint."""
        client = CLClient([FIRST, "", "  "])

        assert client.urls == [FIRST + "/"]

    @pytest.mark.parametrize("urls", [[], [""], ""])
    def test_no_url_raises(self, urls):
        """Test that a client without endpoints cannot be created."""
        with pytest.raises(ValueError):
            CLClient(urls)

    def test_user_agent_is_set_on_the_session(self):
        """Test that every request of the client carries the given User-Agent."""
        client = CLClient(FIRST, user_agent="validator-exit-bot/9.9.9")

        assert client._session.headers["User-Agent"] == "validator-exit-bot/9.9.9"

    def test_default_user_agent_names_the_app(self):
        """Test that a client created without a User-Agent still names the app."""
        client = CLClient(FIRST)

        user_agent = str(client._session.headers["User-Agent"])

        assert user_agent.startswith("validator-exit-bot/")


class TestCLClientFallbackSwitches:
    """Test the cases where an endpoint gives no answer and the next one is asked."""

    @pytest.mark.parametrize("failure", NO_ANSWER)
    def test_second_endpoint_answers(self, failure):
        """Test that the answer of the second endpoint is returned."""
        client = CLClient([FIRST, SECOND])

        with patch(SESSION_GET, side_effect=[failure, answer()]) as mock_get:
            validator = client.get_validator_by_pubkey(PUBKEY)

        assert validator == VALIDATOR
        assert [call.args[0] for call in mock_get.call_args_list] == [
            FIRST + VALIDATOR_PATH,
            SECOND + VALIDATOR_PATH,
        ]

    def test_all_validators_from_second_endpoint(self):
        """Test that the list request falls back as well and keeps its timeout."""
        client = CLClient([FIRST, SECOND])
        validators = [{"index": "0", "validator": {"pubkey": "0xabc123"}}]
        responses = [make_response(503, {}), make_response(200, {"data": validators})]

        with patch(SESSION_GET, side_effect=responses) as mock_get:
            assert client.get_all_validators() == validators

        assert [call.kwargs["timeout"] for call in mock_get.call_args_list] == [60, 60]

    @pytest.mark.parametrize("data", [{}, None, "validators"])
    def test_list_request_skips_data_that_is_not_a_list(self, data):
        """Test that a malformed list answer is not returned to the caller."""
        client = CLClient([FIRST, SECOND])
        validators = [{"index": "0", "validator": {"pubkey": "0xabc123"}}]
        responses = [
            make_response(200, {"data": data}),
            make_response(200, {"data": validators}),
        ]

        with patch(SESSION_GET, side_effect=responses):
            assert client.get_all_validators() == validators

    @pytest.mark.parametrize("data", [[], {}, {"index": None}, {"index": "abc"}])
    def test_index_request_skips_data_without_a_numeric_index(self, data):
        """Test that a malformed validator answer is not used for the index."""
        client = CLClient([FIRST, SECOND])
        responses = [make_response(200, {"data": data}), answer()]

        with patch(SESSION_GET, side_effect=responses):
            assert client.get_validator_index_by_pubkey(PUBKEY) == 12345


class TestCLClientFallbackFinal:
    """Test the answers that must not be asked again from another endpoint."""

    @pytest.mark.parametrize("final", FINAL)
    def test_validator_request_stops_at_the_first_endpoint(self, final):
        """Test that the result is "no validator data" and the second endpoint is not called."""
        client = CLClient([FIRST, SECOND])

        with patch(SESSION_GET, side_effect=[final, answer()]) as mock_get:
            validator = client.get_validator_by_pubkey(PUBKEY)

        assert validator is None
        assert mock_get.call_count == 1

    def test_index_request_raises_http_error_on_404(self):
        """Test that a raising method keeps the HTTP error of the first endpoint."""
        client = CLClient([FIRST, SECOND])
        responses = [make_response(404, {"message": "not found"}), answer()]

        with patch(SESSION_GET, side_effect=responses) as mock_get:
            with pytest.raises(requests.HTTPError):
                client.get_validator_index_by_pubkey(PUBKEY)

        assert mock_get.call_count == 1

    def test_list_request_raises_on_an_error_body(self):
        """Test that an error body never becomes an empty list of validators."""
        client = CLClient([FIRST, SECOND])
        responses = [
            make_response(200, {"error": "state not found"}),
            make_response(200, {"data": []}),
        ]

        with patch(SESSION_GET, side_effect=responses) as mock_get:
            with pytest.raises(ValueError):
                client.get_all_validators()

        assert mock_get.call_count == 1

    def test_list_request_raises_http_error_on_404(self):
        """Test that the list request does not ask another endpoint after a 404."""
        client = CLClient([FIRST, SECOND])
        responses = [
            make_response(404, {"message": "not found"}),
            make_response(200, {"data": []}),
        ]

        with patch(SESSION_GET, side_effect=responses) as mock_get:
            with pytest.raises(requests.HTTPError):
                client.get_all_validators()

        assert mock_get.call_count == 1


class TestCLClientAllEndpointsFail:
    """Test that a failure of every endpoint stays an error and never becomes a status."""

    def test_validator_request_returns_none(self):
        """Test that the caller gets no validator data."""
        client = CLClient([FIRST, SECOND])
        failures = [requests.ConnectionError("refused"), make_response(503, {})]

        with patch(SESSION_GET, side_effect=failures) as mock_get:
            assert client.get_validator_by_pubkey(PUBKEY) is None

        assert mock_get.call_count == 2

    def test_is_validator_exited_reports_cl_error(self):
        """Test that the bot skips the validator instead of treating it as not exited."""
        client = CLClient([FIRST, SECOND])
        failures = [requests.ReadTimeout("read"), requests.ConnectionError("refused")]

        with patch(SESSION_GET, side_effect=failures):
            assert client.is_validator_exited(PUBKEY) == (False, True)

    @pytest.mark.parametrize("response", [*NO_ANSWER, *FINAL])
    def test_no_answer_of_a_single_endpoint_is_a_cl_error(self, response):
        """Test that no failure of the only endpoint is read as "not exited"."""
        client = CLClient(FIRST)

        with patch(SESSION_GET, side_effect=[response]):
            assert client.is_validator_exited(PUBKEY) == (False, True)

    def test_answer_without_a_known_status_is_a_cl_error(self):
        """Test that validator data without a Beacon API status is not read as "not exited"."""
        client = CLClient([FIRST, SECOND])
        responses = [
            make_response(200, {"data": {"index": "12345"}}),
            make_response(200, {"data": {"index": "12345", "status": "syncing"}}),
        ]

        with patch(SESSION_GET, side_effect=responses):
            assert client.is_validator_exited(PUBKEY) == (False, True)

    def test_list_request_raises_the_last_error(self):
        """Test that a raising method raises when no endpoint answered."""
        client = CLClient([FIRST, SECOND])
        failures = [make_response(500, {}), requests.ConnectionError("refused")]

        with patch(SESSION_GET, side_effect=failures):
            with pytest.raises(requests.ConnectionError):
                client.get_all_validators()

    def test_final_answer_of_the_last_endpoint_is_kept(self):
        """Test that a 404 of the second endpoint ends the request as "no validator data"."""
        client = CLClient([FIRST, SECOND])
        responses = [make_response(503, {}), make_response(404, {"message": "none"})]

        with patch(SESSION_GET, side_effect=responses):
            assert client.get_validator_by_pubkey(PUBKEY) is None


class TestCLClientFallbackOrder:
    """Test the order in which the endpoints are asked."""

    def test_healthy_first_endpoint_is_the_only_one_called(self):
        """Test that the second endpoint is not touched while the first one answers."""
        client = CLClient([FIRST, SECOND])

        with patch(SESSION_GET, side_effect=[answer()]) as mock_get:
            assert client.get_validator_by_pubkey(PUBKEY) == VALIDATOR

        mock_get.assert_called_once_with(FIRST + VALIDATOR_PATH, timeout=10)

    def test_every_request_starts_at_the_first_endpoint(self):
        """Test that a failure of the first endpoint is not remembered."""
        client = CLClient([FIRST, SECOND])
        responses = [make_response(503, {}), answer(), answer()]

        with patch(SESSION_GET, side_effect=responses) as mock_get:
            client.get_validator_by_pubkey(PUBKEY)
            client.get_validator_by_pubkey(PUBKEY)

        assert [call.args[0] for call in mock_get.call_args_list] == [
            FIRST + VALIDATOR_PATH,
            SECOND + VALIDATOR_PATH,
            FIRST + VALIDATOR_PATH,
        ]


class TestCLClientFallbackLog:
    """Test that the fallback is visible in the log and the log has no endpoint URL."""

    def test_log_names_the_endpoint_by_its_position(self):
        """Test the log lines of a request that no endpoint answered."""
        client = CLClient([FIRST, SECOND])
        error = requests.ConnectionError(f"Max retries exceeded with url: {FIRST}")
        failures = [error, make_response(503, {})]

        with capture_logs() as logs:
            with patch(SESSION_GET, side_effect=failures):
                client.get_validator_by_pubkey(PUBKEY)

        endpoint_events = [log["event"] for log in logs if "endpoint" in log["event"]]
        assert [event["endpoint"] for event in endpoint_events] == [0, 1]
        assert endpoint_events[0]["error_type"] == "ConnectionError"
        assert endpoint_events[1]["status_code"] == 503
        assert "example.com" not in repr(logs)
        assert "key-one" not in repr(logs)
        assert "key-two" not in repr(logs)

    def test_log_has_the_status_of_a_final_answer(self):
        """Test that a rejected request can be told apart from an outage in the log."""
        client = CLClient([FIRST, SECOND])
        responses = [make_response(404, {"message": "not found"}), answer()]

        with capture_logs() as logs:
            with patch(SESSION_GET, side_effect=responses):
                client.get_validator_by_pubkey(PUBKEY)

        assert {
            "msg": "CL endpoint rejected the request",
            "endpoint": 0,
            "status_code": 404,
        } in [log["event"] for log in logs]


class TestCLClientImport:
    """Test that the client stays usable outside the bot process."""

    def test_import_does_not_need_the_bot_config(self):
        """Test that the scripts can import the client without the bot variables."""
        env = {
            name: value
            for name, value in os.environ.items()
            if name not in ("WEB3_RPC_ENDPOINTS", "CONSENSUS_CLIENT_URL")
        }

        result = subprocess.run(
            [sys.executable, "-c", "import src.utils.cl_client"],
            cwd=Path(__file__).resolve().parents[1],
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )

        assert result.returncode == 0, result.stderr
