import os
import threading
import time

import requests
from flask import Flask, Response, jsonify, render_template, request

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "changeme")

SIGNAL_API_URL = os.getenv("SIGNAL_API_URL", "http://signal-cli-rest-api:8080")
SIGNAL_BOT_API_URL = os.getenv("SIGNAL_BOT_API_URL", "http://signal-bot-api:8088")
QR_TTL = 25  # seconds before QR expires in signal-cli

# QR cache: one active link session at a time
_qr_lock = threading.Lock()
_qr_cache: bytes | None = None
_qr_ts: float = 0.0


def _get_accounts() -> list[str]:
    try:
        r = requests.get(f"{SIGNAL_API_URL}/v1/accounts", timeout=5)
        data = r.json() if r.ok else []
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _fetch_fresh_qr() -> bytes:
    """Fetch a new QR from signal-cli and update the cache."""
    global _qr_cache, _qr_ts
    r = requests.get(f"{SIGNAL_API_URL}/v1/qrcodelink?device_name=signalbot", timeout=30)
    r.raise_for_status()
    with _qr_lock:
        _qr_cache = r.content
        _qr_ts = time.time()
    return r.content


@app.route("/")
def index() -> str:
    accounts = _get_accounts()
    linked = request.args.get("linked")
    return render_template("index.html", accounts=accounts, linked=linked)


@app.route("/link")
def link() -> str:
    # Snapshot of accounts before linking; also pre-warm the QR cache
    before = _get_accounts()
    # Kick off QR fetch in background so the page loads instantly
    threading.Thread(target=_fetch_fresh_qr, daemon=True).start()
    return render_template("link.html", before=before, qr_ttl=QR_TTL)


@app.route("/qrcode.png")
def qrcode() -> Response:
    """Serve cached QR or fetch a fresh one. ?refresh=1 forces regeneration."""
    force = request.args.get("refresh") == "1"
    with _qr_lock:
        age = time.time() - _qr_ts
        cached = _qr_cache if (not force and age < QR_TTL and _qr_cache) else None

    if cached:
        return Response(cached, mimetype="image/png")

    try:
        data: bytes = _fetch_fresh_qr()
    except Exception:
        # If we have a stale cache, return it rather than a broken image
        with _qr_lock:
            stale = _qr_cache
        if not stale:
            return Response(status=503)
        data = stale
    return Response(data, mimetype="image/png")


@app.route("/api/accounts")
def api_accounts() -> Response:
    return jsonify(_get_accounts())


@app.route("/api/recent")
def api_recent() -> Response:
    """Proxy recent CoT events from signal-bot-api."""
    try:
        r = requests.get(f"{SIGNAL_BOT_API_URL}/api/recent", timeout=3)
        return Response(r.content, mimetype="application/json")
    except Exception:
        return jsonify([])


@app.route("/docs")
def docs() -> str:
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    try:
        with open(readme_path, encoding="utf-8") as f:  # noqa: PTH123
            content = f.read()
    except FileNotFoundError:
        content = "_README.md not found._"
    return render_template("docs.html", content=content)


@app.route("/health")
def health() -> tuple[str, int]:
    return "ok", 200


if __name__ == "__main__":
    port = int(os.getenv("UI_PORT", "5001"))
    app.run(host="0.0.0.0", port=port, threaded=True)  # noqa: S104
