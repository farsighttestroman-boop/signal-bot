import collections
import json
import logging
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import websocket
from cot_builder import build_cot
from fts_sender import send_cot
from message_parser import parse_message
from signal_client import SignalClient

SIGNAL_API_URL = os.getenv("SIGNAL_API_URL", "http://signal-cli-rest-api:8080")
LOG_LEVEL = os.getenv("LOG_LEVEL", "info").upper()
EVENTS_PORT = int(os.getenv("EVENTS_PORT", "8088"))

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)

# In-memory ring buffer of the last 50 processed CoT events
_events: collections.deque = collections.deque(maxlen=50)
_events_lock = threading.Lock()


def _add_event(source: str, lat: float, lon: float, description: str, cot_type: str) -> None:
    with _events_lock:
        _events.append(
            {
                "ts": time.time(),
                "source": source,
                "lat": lat,
                "lon": lon,
                "description": description,
                "cot_type": cot_type,
            }
        )


class _EventsHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path != "/api/recent":
            self.send_response(404)
            self.end_headers()
            return
        with _events_lock:
            data = json.dumps(list(_events)).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args: object) -> None:
        pass  # silence access log


def _start_events_server() -> None:
    server = HTTPServer(("0.0.0.0", EVENTS_PORT), _EventsHandler)  # noqa: S104
    log.info("Events HTTP server listening on :%d", EVENTS_PORT)
    server.serve_forever()


USAGE_HINT = (
    "Usage: <lat> <lon> <description>\n"
    "Examples:\n"
    "  48.567 39.878 tank\n"
    "  50.1 30.5 friendly patrol\n"
    "  51.0 32.0 checkpoint"
)


def extract_text_and_source(envelope: dict) -> tuple[str | None, str | None]:
    """
    Pull (source_number, message_text) from an envelope.
    Handles:
      - dataMessage:            regular messages from other accounts
      - syncMessage.sentMessage: self-messages forwarded to linked devices
    Returns (None, None) for receipts, typing indicators, etc.
    """
    inner = envelope.get("envelope", {})
    source = inner.get("sourceNumber") or inner.get("source")

    # Regular message from another account
    data = inner.get("dataMessage", {})
    text = data.get("message")
    if text:
        return source, text

    # Self-message synced to linked device
    sent = inner.get("syncMessage", {}).get("sentMessage", {})
    text = sent.get("message")
    if text:
        return source, text

    return None, None


def handle_envelope(raw: str, client: SignalClient) -> None:
    try:
        envelope = json.loads(raw)
    except Exception:
        return

    source, text = extract_text_and_source(envelope)
    if source is None or text is None:
        return  # receipt / typing indicator — skip silently

    log.info("Message from %s: %s", source, text)
    parsed = parse_message(text)

    if parsed is None:
        client.send_message(source, USAGE_HINT)
        return

    xml = build_cot(parsed.lat, parsed.lon, parsed.description, parsed.cot_type)
    log.debug("CoT XML: %s", xml.strip())

    try:
        send_cot(xml)
        _add_event(source, parsed.lat, parsed.lon, parsed.description, parsed.cot_type)
        reply = (
            f"Sent to ATAK:\n"
            f"  {parsed.description}\n"
            f"  lat={parsed.lat}  lon={parsed.lon}\n"
            f"  type={parsed.cot_type}\n\n"
            f"View on map: http://localhost:5000/webmap\n"
            f"(login: admin / password if prompted)"
        )
        client.send_message(source, reply)
        log.info("CoT sent: %s @ (%.4f, %.4f)", parsed.description, parsed.lat, parsed.lon)
    except OSError as exc:
        log.error("Failed to send CoT: %s", exc)
        client.send_message(source, f"Error sending to ATAK: {exc}")


def wait_for_account() -> str:
    """Block until signal-cli-rest-api has at least one registered account."""
    log.info("Waiting for a Signal account to be registered via the UI at :5001 ...")
    while True:
        accounts = SignalClient.get_accounts(SIGNAL_API_URL)
        if accounts:
            number = accounts[0]
            log.info("Found registered account: %s", number)
            return number
        time.sleep(5)


def main() -> None:
    threading.Thread(target=_start_events_server, daemon=True).start()
    number = wait_for_account()
    client = SignalClient(SIGNAL_API_URL, number)

    ws_url = (
        SIGNAL_API_URL.replace("http://", "ws://").replace("https://", "wss://")
        + f"/v1/receive/{number}"
    )
    log.info("Signal bot started. Listening on %s", ws_url)

    def on_message(ws: object, raw: str) -> None:
        handle_envelope(raw, client)

    def on_error(ws: object, error: object) -> None:
        log.error("WebSocket error: %s", error)

    def on_close(ws: object, *args: object) -> None:
        log.warning("WebSocket closed — will reconnect")

    def on_open(ws: object) -> None:
        log.info("WebSocket connected to signal-cli-rest-api")

    while True:
        try:
            ws = websocket.WebSocketApp(
                ws_url,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
            )
            ws.run_forever(ping_interval=30, ping_timeout=10, reconnect=5)
        except Exception as e:
            log.error("WebSocket crashed: %s — retrying in 5s", e)
            time.sleep(5)


if __name__ == "__main__":
    main()
