from unittest.mock import MagicMock, patch

from signal_client import SignalClient


def _mock_response(json_data=None, status_code: int = 200) -> MagicMock:
    r = MagicMock()
    r.status_code = status_code
    r.ok = status_code < 400
    r.json.return_value = json_data
    r.raise_for_status.return_value = None
    return r


def test_get_accounts_returns_list() -> None:
    with patch("signal_client.requests.get", return_value=_mock_response(["+380991234567"])):
        result = SignalClient.get_accounts("http://localhost:8080")
    assert result == ["+380991234567"]


def test_get_accounts_returns_empty_on_error() -> None:
    with patch("signal_client.requests.get", side_effect=Exception("conn")):
        result = SignalClient.get_accounts("http://localhost:8080")
    assert result == []


def test_get_accounts_handles_non_list_response() -> None:
    with patch("signal_client.requests.get", return_value=_mock_response({"error": "x"})):
        result = SignalClient.get_accounts("http://localhost:8080")
    assert result == []


def test_send_message_posts_payload() -> None:
    mock_post = MagicMock(return_value=_mock_response())
    client = SignalClient("http://localhost:8080", "+380001234567")
    with patch("signal_client.requests.post", mock_post):
        client.send_message("+380991234567", "hello")
    mock_post.assert_called_once()
    _, kwargs = mock_post.call_args
    assert kwargs["json"]["message"] == "hello"
    assert kwargs["json"]["number"] == "+380001234567"
    assert "+380991234567" in kwargs["json"]["recipients"]


def test_send_message_swallows_error() -> None:
    client = SignalClient("http://localhost:8080", "+380001234567")
    with patch("signal_client.requests.post", side_effect=Exception("timeout")):
        client.send_message("+380991234567", "hi")  # must not raise
