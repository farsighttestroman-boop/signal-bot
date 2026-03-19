import re
from dataclasses import dataclass

_HOSTILE = {"tank", "artillery", "enemy", "hostile", "target"}
_FRIENDLY = {"friendly", "ally", "blue", "friend"}

_PATTERN = re.compile(r"^(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s+(.+)$")


@dataclass
class ParsedTarget:
    lat: float
    lon: float
    description: str
    cot_type: str


def parse_message(text: str) -> ParsedTarget | None:
    """
    Parse 'lat lon description' messages.
    Returns None if format does not match.

    Examples:
      "48.567123 39.87897 tank"    → hostile (Red)
      "50.1 30.5 friendly patrol"  → friendly (Cyan)
      "51.0 32.0 checkpoint"       → unknown (Yellow)
    """
    m = _PATTERN.match(text.strip())
    if not m:
        return None

    lat = float(m.group(1))
    lon = float(m.group(2))
    desc = m.group(3).strip()

    words = set(desc.lower().split())
    if words & _FRIENDLY:
        cot_type = "a-f-G-U-C"
    elif words & _HOSTILE:
        cot_type = "a-h-G-U-C"
    else:
        cot_type = "a-u-G"

    return ParsedTarget(lat=lat, lon=lon, description=desc, cot_type=cot_type)
