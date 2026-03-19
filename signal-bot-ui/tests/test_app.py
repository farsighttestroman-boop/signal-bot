import json
from unittest.mock import MagicMock, patch

import app as ui_app
import pytest


@pytest.fixture()
def client():
    ui_app.app.config["TESTING"] = True
    with ui_app.app.test_client() as c:
        yield c


# ── /health ──────────────────────────────────────────────────────────────────


def test_health(client) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.data == b"ok"


# ── / (index) ────────────────────────────────────────────────────────────────


def test_index_no_accounts(client) -> None:
    with patch("app._get_accounts", return_value=[]):
        resp = client.get("/")
    assert resp.status_code == 200
    assert b"No accounts linked" in resp.data


def test_index_with_accounts(client) -> None:
    with patch("app._get_accounts", return_value=["+380991234567"]):
        resp = client.get("/")
    assert resp.status_code == 200
    assert b"+380991234567" in resp.data


def test_index_shows_linked_flash(client) -> None:
    with patch("app._get_accounts", return_value=["+380991234567"]):
        resp = client.get("/?linked=%2B380991234567")
    assert resp.status_code == 200
    assert b"Successfully linked" in resp.data


# ── /api/accounts ─────────────────────────────────────────────────────────────


def test_api_accounts_returns_list(client) -> None:
    with patch("app._get_accounts", return_value=["+380991234567"]):
        resp = client.get("/api/accounts")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data == ["+380991234567"]


def test_api_accounts_empty(client) -> None:
    with patch("app._get_accounts", return_value=[]):
        resp = client.get("/api/accounts")
    assert resp.status_code == 200
    assert json.loads(resp.data) == []


# ── /docs ────────────────────────────────────────────────────────────────────


def test_docs_renders(client) -> None:
    resp = client.get("/docs")
    assert resp.status_code == 200
    assert b"Signal Bot" in resp.data


# ── /api/recent ──────────────────────────────────────────────────────────────


def test_api_recent_proxies_bot_api(client) -> None:
    fake_events = [{"ts": 1000, "description": "tank"}]
    mock_resp = MagicMock()
    mock_resp.content = json.dumps(fake_events).encode()
    with patch("app.requests.get", return_value=mock_resp):
        resp = client.get("/api/recent")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data[0]["description"] == "tank"


def test_api_recent_returns_empty_on_error(client) -> None:
    with patch("app.requests.get", side_effect=Exception("conn refused")):
        resp = client.get("/api/recent")
    assert resp.status_code == 200
    assert json.loads(resp.data) == []


# ── /link ────────────────────────────────────────────────────────────────────


def test_link_page_renders(client) -> None:
    with patch("app._get_accounts", return_value=[]):
        with patch("app._fetch_fresh_qr", return_value=b"fakepng"):
            resp = client.get("/link")
    assert resp.status_code == 200
    assert b"Link" in resp.data
