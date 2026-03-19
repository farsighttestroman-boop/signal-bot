import uuid
from datetime import UTC, datetime, timedelta

# Maps CoT type → ATAK group colour
_GROUP_COLOUR = {
    "a-h-G-U-C": "Red",  # Hostile
    "a-f-G-U-C": "Cyan",  # Friendly
    "a-u-G": "Yellow",  # Unknown
}


def build_cot(lat: float, lon: float, callsign: str, cot_type: str, uid: str | None = None) -> str:
    now = datetime.now(UTC)
    stale = now + timedelta(hours=1)
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    uid = uid or str(uuid.uuid4())
    colour = _GROUP_COLOUR.get(cot_type, "Yellow")

    return (
        f'<event version="2.0" uid="{uid}" type="{cot_type}" '
        f'time="{now.strftime(fmt)}" start="{now.strftime(fmt)}" '
        f'stale="{stale.strftime(fmt)}" how="m-g">'
        f'<point lat="{lat}" lon="{lon}" hae="0" ce="9999999" le="9999999"/>'
        f"<detail>"
        f'<contact callsign="{callsign}"/>'
        f'<__group name="{colour}" role="Team Member"/>'
        f"</detail>"
        f"</event>\n"
    )
