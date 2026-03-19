import os
import socket

FTS_HOST = os.getenv("FTS_HOST", "freetakserver")
FTS_PORT = int(os.getenv("FTS_PORT", "8087"))


def send_cot(xml: str) -> None:
    """Send raw CoT XML string to FreeTakServer over TCP."""
    with socket.create_connection((FTS_HOST, FTS_PORT), timeout=5) as s:
        s.sendall(xml.encode("utf-8"))
