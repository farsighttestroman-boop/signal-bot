import uuid
import xml.etree.ElementTree as ET

import pytest
from cot_builder import build_cot


def test_build_cot_hostile() -> None:
    xml = build_cot(48.567, 39.878, "tank", "a-h-G-U-C")
    assert 'type="a-h-G-U-C"' in xml
    assert 'lat="48.567"' in xml
    assert 'lon="39.878"' in xml
    assert 'name="Red"' in xml
    assert 'callsign="tank"' in xml


def test_build_cot_friendly() -> None:
    xml = build_cot(50.1, 30.5, "patrol", "a-f-G-U-C")
    assert 'type="a-f-G-U-C"' in xml
    assert 'name="Cyan"' in xml


def test_build_cot_unknown() -> None:
    xml = build_cot(51.0, 32.0, "checkpoint", "a-u-G")
    assert 'type="a-u-G"' in xml
    assert 'name="Yellow"' in xml


def test_build_cot_custom_uid() -> None:
    custom = str(uuid.uuid4())
    xml = build_cot(0.0, 0.0, "test", "a-u-G", uid=custom)
    assert f'uid="{custom}"' in xml


def test_build_cot_auto_uid() -> None:
    xml = build_cot(0.0, 0.0, "test", "a-u-G")
    # extract uid= value and verify it parses as a UUID
    import re

    match = re.search(r'uid="([^"]+)"', xml)
    assert match is not None
    uid_val = match.group(1)
    uuid.UUID(uid_val)  # raises ValueError if not valid UUID


def test_build_cot_xml_parseable() -> None:
    xml = build_cot(48.567, 39.878, "tank", "a-h-G-U-C")
    root = ET.fromstring(xml.strip())  # noqa: S314  # data is our own output, not untrusted
    assert root.tag == "event"
    point = root.find("point")
    assert point is not None
    assert float(point.attrib["lat"]) == pytest.approx(48.567)
    assert float(point.attrib["lon"]) == pytest.approx(39.878)


def test_build_cot_unknown_type_defaults_to_yellow() -> None:
    xml = build_cot(0.0, 0.0, "x", "a-x-unknown")
    assert 'name="Yellow"' in xml
