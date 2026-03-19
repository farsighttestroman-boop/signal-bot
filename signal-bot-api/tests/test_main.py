import json
import threading
import urllib.request
from unittest.mock import MagicMock, patch

import main as bot
import pytest

# ── extract_text_and_source ─────────────────────────────────────────────────


def _wrap(inner: dict) -> str:
    return json.dumps({"envelope": inner})


def test_extract_data_message() -> None:
    raw = _wrap(
        {
            "sourceNumber": "+380991234567",
            "dataMessage": {"message": "48.5 39.8 tank"},
        }
    )
    source, text = bot.extract_text_and_source(json.loads(raw))
    assert source == "+380991234567"
    assert text == "48.5 39.8 tank"


def test_extract_sync_message() -> None:
    raw = _wrap(
        {
            "sourceNumber": "+380991234567",
            "syncMessage": {"sentMessage": {"message": "51.0 32.0 checkpoint"}},
        }
    )
    source, text = bot.extract_text_and_source(json.loads(raw))
    assert source == "+380991234567"
    assert text == "51.0 32.0 checkpoint"


def test_extract_receipt_returns_none() -> None:
    raw = _wrap({"sourceNumber": "+380991234567", "receiptMessage": {}})
    source, text = bot.extract_text_and_source(json.loads(raw))
    assert source is None
    assert text is None


# ── _add_event ───────────────────────────────────────────────────────────────


def test_add_event_stores_data() -> None:
    bot._events.clear()
    bot._add_event("+1234", 48.5, 39.8, "tank", "a-h-G-U-C")
    assert len(bot._events) == 1
    ev = bot._events[0]
    assert ev["lat"] == pytest.approx(48.5)
    assert ev["lon"] == pytest.approx(39.8)
    assert ev["description"] == "tank"
    assert ev["cot_type"] == "a-h-G-U-C"
    assert "ts" in ev


def test_add_event_respects_maxlen() -> None:
    bot._events.clear()
    for i in range(60):
        bot._add_event("+1", float(i), 0.0, "x", "a-u-G")
    assert len(bot._events) == 50  # deque maxlen


# ── events HTTP server ────────────────────────────────────────────────────────


def test_events_server_returns_json() -> None:
    bot._events.clear()
    bot._add_event("+1", 10.0, 20.0, "ping", "a-u-G")

    # Start server on a random free port
    from http.server import HTTPServer

    server = HTTPServer(("127.0.0.1", 0), bot._EventsHandler)
    port = server.server_address[1]
    t = threading.Thread(target=server.handle_request)
    t.start()

    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/recent", timeout=3) as resp:  # noqa: S310
            data = json.loads(resp.read())
    finally:
        server.server_close()
        t.join(timeout=2)

    assert isinstance(data, list)
    assert data[0]["description"] == "ping"


# ── handle_envelope ───────────────────────────────────────────────────────────


def test_handle_envelope_valid_target_sends_cot() -> None:
    bot._events.clear()
    raw = json.dumps(
        {
            "envelope": {
                "sourceNumber": "+380001234567",
                "dataMessage": {"message": "48.5 39.8 tank"},
            }
        }
    )
    mock_client = MagicMock()
    with patch("main.send_cot") as mock_send:
        bot.handle_envelope(raw, mock_client)
    mock_send.assert_called_once()
    mock_client.send_message.assert_called_once()
    assert len(bot._events) == 1


def test_handle_envelope_invalid_text_sends_usage_hint() -> None:
    raw = json.dumps(
        {
            "envelope": {
                "sourceNumber": "+380001234567",
                "dataMessage": {"message": "not a target"},
            }
        }
    )
    mock_client = MagicMock()
    with patch("main.send_cot") as mock_send:
        bot.handle_envelope(raw, mock_client)
    mock_send.assert_not_called()
    mock_client.send_message.assert_called_once()
    assert "Usage" in mock_client.send_message.call_args[0][1]


def test_handle_envelope_malformed_json_is_silently_ignored() -> None:
    mock_client = MagicMock()
    bot.handle_envelope("not json at all", mock_client)
    mock_client.send_message.assert_not_called()


def test_handle_envelope_receipt_is_silently_ignored() -> None:
    raw = json.dumps({"envelope": {"sourceNumber": "+380001234567", "receiptMessage": {}}})
    mock_client = MagicMock()
    bot.handle_envelope(raw, mock_client)
    mock_client.send_message.assert_not_called()
