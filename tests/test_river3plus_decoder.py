"""Unit tests for the River 3 Plus protobuf decoder (PR #40 review follow-up).

The decoder is hand-rolled binary parsing of EcoFlow's `thing/property/get_reply`
frames. These tests build frames with a tiny local protobuf encoder and assert
the decoder extracts the right metrics — including the documented `field 28`
regression where a BMS "remaining time" field was previously misread as AC watts.

Pure stdlib (no Home Assistant import) so it runs under plain ``python -m pytest``.
"""

from __future__ import annotations

import importlib.util
import struct
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_DECODER_PATH = (
    ROOT
    / "custom_components"
    / "ecoflow_api"
    / "devices"
    / "river3plus"
    / "proto_decoder.py"
)

# Load the decoder module directly from its file so the test stays HA-free
# (importing the package would pull in const.py, which imports Home Assistant).
_spec = importlib.util.spec_from_file_location("river3plus_proto_decoder", _DECODER_PATH)
assert _spec is not None and _spec.loader is not None
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
River3PlusProtoDecoder = _module.River3PlusProtoDecoder


# --- minimal protobuf wire encoder (mirrors the shapes the decoder reads) ---


def _varint(value: int) -> bytes:
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            return bytes(out)


def _vfield(field: int, value: int) -> bytes:
    """Varint (wire type 0) field."""
    return _varint((field << 3) | 0) + _varint(value)


def _f64field(field: int, value: float) -> bytes:
    """Fixed64 / double (wire type 1) field."""
    return _varint((field << 3) | 1) + struct.pack("<d", value)


def _bytesfield(field: int, payload: bytes) -> bytes:
    """Length-delimited (wire type 2) field."""
    return _varint((field << 3) | 2) + _varint(len(payload)) + payload


def _envelope(cmd_func: int, cmd_id: int, inner: bytes) -> bytes:
    """One typed envelope: top-level field 1 -> {f8=cmd_func, f9=cmd_id, f1=inner}."""
    header = _vfield(8, cmd_func) + _vfield(9, cmd_id) + _bytesfield(1, inner)
    return _bytesfield(1, header)


class River3PlusDecoderTest(unittest.TestCase):
    def test_display_properties_decode(self) -> None:
        decoder = River3PlusProtoDecoder("BKR3PLUSTEST0001")
        inner = _vfield(3, 143) + _vfield(4, 200) + _vfield(54, 143)
        frame = _envelope(254, 21, inner)

        result = decoder.decode(frame)

        assert result is not None
        self.assertEqual(result["pow_in_sum_w"], 143.0)
        self.assertEqual(result["pow_out_sum_w"], 200.0)
        self.assertEqual(result["ac_in_power"], 143.0)

    def test_runtime_properties_decode(self) -> None:
        decoder = River3PlusProtoDecoder("BKR3PLUSTEST0001")
        inner = (
            _f64field(26, 31.5)  # PCS DC temp
            + _f64field(68, 230.0)  # AC input voltage
            + _f64field(223, 0.62)  # AC input current
        )
        frame = _envelope(254, 22, inner)

        result = decoder.decode(frame)

        assert result is not None
        self.assertEqual(result["temp_pcs_dc"], 31.5)
        self.assertEqual(result["ac_in_voltage"], 230.0)
        self.assertEqual(result["ac_in_current"], 0.62)

    def test_bms_field28_not_treated_as_watts(self) -> None:
        """Regression: BMS field 28 (remaining time) must not become AC watts."""
        decoder = River3PlusProtoDecoder("BKR3PLUSTEST0001")
        # field 6 = SOC, field 16 = temp (centi-degrees), field 28 = 593 (minutes).
        inner = _vfield(6, 50) + _vfield(16, 2500) + _vfield(28, 593)
        frame = _envelope(32, 50, inner)

        result = decoder.decode(frame)

        assert result is not None
        self.assertEqual(result["battery_level"], 50.0)
        self.assertEqual(result["temperature"], 25.0)
        # The 593 from field 28 must NOT have leaked into any power metric.
        self.assertNotIn("ac_in_power", result)
        self.assertNotIn("pow_in_sum_w", result)

    def test_out_of_range_values_are_dropped(self) -> None:
        decoder = River3PlusProtoDecoder("BKR3PLUSTEST0001")
        # 99999 W is outside the 0..10000 sanity window and must be rejected.
        inner = _vfield(3, 99999)
        frame = _envelope(254, 21, inner)

        result = decoder.decode(frame)

        self.assertIsNone(result)

    def test_garbage_payload_returns_none(self) -> None:
        decoder = River3PlusProtoDecoder("BKR3PLUSTEST0001")
        # Truncated varint -> parse error -> decoder swallows and returns None.
        self.assertIsNone(decoder.decode(b"\xff"))
        self.assertIsNone(decoder.decode(b""))


if __name__ == "__main__":
    unittest.main()
