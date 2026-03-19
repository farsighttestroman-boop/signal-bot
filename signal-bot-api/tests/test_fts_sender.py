from unittest.mock import MagicMock, patch

from fts_sender import send_cot


def test_send_cot_sends_xml_over_tcp() -> None:
    mock_socket = MagicMock()
    mock_ctx = MagicMock()
    mock_ctx.__enter__ = MagicMock(return_value=mock_socket)
    mock_ctx.__exit__ = MagicMock(return_value=False)

    with patch("fts_sender.socket.create_connection", return_value=mock_ctx):
        send_cot("<event/>")

    mock_socket.sendall.assert_called_once_with(b"<event/>")


def test_send_cot_encodes_utf8() -> None:
    mock_socket = MagicMock()
    mock_ctx = MagicMock()
    mock_ctx.__enter__ = MagicMock(return_value=mock_socket)
    mock_ctx.__exit__ = MagicMock(return_value=False)

    with patch("fts_sender.socket.create_connection", return_value=mock_ctx):
        send_cot("<event>тест</event>")

    sent = mock_socket.sendall.call_args[0][0]
    assert isinstance(sent, bytes)
    assert "тест".encode() in sent
