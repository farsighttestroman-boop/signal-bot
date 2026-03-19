import logging

import requests

log = logging.getLogger(__name__)


class SignalClient:
    def __init__(self, base_url: str, number: str):
        self.base_url = base_url.rstrip("/")
        self.number = number

    @classmethod
    def get_accounts(cls, base_url: str) -> list[str]:
        """GET /v1/accounts — returns list of registered phone numbers."""
        try:
            r = requests.get(f"{base_url.rstrip('/')}/v1/accounts", timeout=5)
            r.raise_for_status()
            data = r.json()
            return data if isinstance(data, list) else []
        except Exception as e:
            log.debug("get_accounts failed: %s", e)
            return []

    def send_message(self, recipient: str, message: str) -> None:
        """POST /v2/send — reply to a Signal user."""
        url = f"{self.base_url}/v2/send"
        payload = {
            "message": message,
            "number": self.number,
            "recipients": [recipient],
        }
        try:
            r = requests.post(url, json=payload, timeout=10)
            r.raise_for_status()
        except Exception as e:
            log.warning("send_message to %s failed: %s", recipient, e)
