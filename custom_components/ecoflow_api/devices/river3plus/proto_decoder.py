"""Protobuf decoder for EcoFlow River 3 Plus MQTT telemetry.

The River 3 Plus `thing/property/get_reply` payload is a bundle of typed
protobuf envelopes. The important ones seen from live packets are:

- `cmdFunc=32`, `cmdId=50`: BMS heartbeat
- `cmdFunc=254`, `cmdId=21`: display properties
- `cmdFunc=254`, `cmdId=22`: runtime properties

The original staging decoder flattened all sub-messages and treated any
`field 28` as AC input watts. That works accidentally for some packets, but in
the BMS heartbeat `field 28` is remaining time, which is why Home Assistant
could show `593.9 W` instead of the real `~143 W`.
"""
from __future__ import annotations

from dataclasses import dataclass
import logging
import struct
from typing import Any

_LOGGER = logging.getLogger(__name__)

_CMD_FUNC_BMS = 32
_CMD_ID_BMS_HEARTBEAT = 50
_CMD_FUNC_PROPERTIES = 254
_CMD_ID_DISPLAY_PROPERTIES = 21
_CMD_ID_RUNTIME_PROPERTIES = 22


@dataclass(slots=True)
class _ProtoEnvelope:
    """Typed protobuf envelope extracted from the MQTT reply."""

    cmd_func: int
    cmd_id: int
    payload: dict[int, int | float]


class River3PlusProtoDecoder:
    """Decoder for raw EcoFlow River 3 Plus protobuf MQTT replies."""

    def __init__(self, device_sn: str) -> None:
        """Initialise decoder state."""
        self._sn = device_sn
        self._soc: float = 0.0
        self._soc_modules: list[int] = []

    def decode(self, payload: bytes) -> dict[str, Any] | None:
        """Decode a raw `thing/property/get_reply` payload into sensor values."""
        try:
            raw_socs: list[int] = []
            valid_temps: list[float] = []
            result: dict[str, Any] = {}

            for envelope in self._iter_envelopes(payload):
                if (
                    envelope.cmd_func == _CMD_FUNC_BMS
                    and envelope.cmd_id == _CMD_ID_BMS_HEARTBEAT
                ):
                    self._collect_bms_metrics(
                        envelope.payload,
                        raw_socs=raw_socs,
                        valid_temps=valid_temps,
                    )
                    continue

                if (
                    envelope.cmd_func == _CMD_FUNC_PROPERTIES
                    and envelope.cmd_id == _CMD_ID_DISPLAY_PROPERTIES
                ):
                    result.update(self._decode_display_properties(envelope.payload))
                    continue

                if (
                    envelope.cmd_func == _CMD_FUNC_PROPERTIES
                    and envelope.cmd_id == _CMD_ID_RUNTIME_PROPERTIES
                ):
                    result.update(self._decode_runtime_properties(envelope.payload))

            if valid_temps:
                result["temperature"] = round(sum(valid_temps) / len(valid_temps), 2)

            if raw_socs:
                self._update_soc_latch(raw_socs)
                result["battery_level"] = self._soc

            return result or None

        except Exception as exc:  # noqa: BLE001
            _LOGGER.error("[%s] Protobuf parse error: %s", self._sn, exc)
            return None

    def _collect_bms_metrics(
        self,
        payload: dict[int, int | float],
        raw_socs: list[int],
        valid_temps: list[float],
    ) -> None:
        """Apply the staging decoder's multi-BMS filtering to heartbeat data."""
        m_soc = self._read_int(payload, 6)
        m_temp = self._read_int(payload, 16)

        if m_soc is None:
            return

        is_valid_bms = True

        if not (0 <= m_soc <= 100):
            is_valid_bms = False
            _LOGGER.debug("[%s] Rejected SOC out of range: %s", self._sn, m_soc)
        elif m_soc == 0:
            if m_temp is None or m_temp == 0:
                is_valid_bms = False
        elif m_temp is not None and 0 < m_temp < 100:
            # Low integer temperatures are status-like fields, not centidegrees.
            is_valid_bms = False
        elif m_temp is None:
            is_valid_bms = False
            _LOGGER.debug("[%s] Rejected SOC without temp: %s%%", self._sn, m_soc)

        if not is_valid_bms:
            return

        raw_socs.append(m_soc)
        valid_temps.append(m_temp / 100.0)
        _LOGGER.debug(
            "[%s] Valid BMS: SOC=%s%%, Temp=%s°C",
            self._sn,
            m_soc,
            round(m_temp / 100.0, 2),
        )

    def _decode_display_properties(
        self, payload: dict[int, int | float]
    ) -> dict[str, Any]:
        """Extract stable read-only values from the display property upload."""
        metrics: dict[str, Any] = {}

        total_input_power = self._read_float(payload, 3)
        total_output_power = self._read_float(payload, 4)
        ac_input_power = self._read_float(payload, 54)

        if total_input_power is not None:
            metrics["pow_in_sum_w"] = round(total_input_power, 1)
        if total_output_power is not None:
            metrics["pow_out_sum_w"] = round(total_output_power, 1)

        # Field 54 is the real AC input power. Field 28 in BMS packets is
        # remaining time and must not be interpreted as watts.
        if ac_input_power is None:
            ac_input_power = total_input_power
        if ac_input_power is not None:
            metrics["ac_in_power"] = round(ac_input_power, 1)

        return metrics

    def _decode_runtime_properties(
        self, payload: dict[int, int | float]
    ) -> dict[str, Any]:
        """Extract stable read-only values from the runtime property upload."""
        metrics: dict[str, Any] = {}

        pcs_dc_temperature = self._read_float(payload, 26)
        pcs_ac_temperature = self._read_float(payload, 27)
        ac_output_voltage = self._read_float(payload, 67)
        ac_input_voltage = self._read_float(payload, 68)
        ac_input_current = self._read_float(payload, 223)
        ac_output_current = self._read_float(payload, 224)

        if pcs_dc_temperature is not None:
            metrics["temp_pcs_dc"] = round(pcs_dc_temperature, 2)
        if pcs_ac_temperature is not None:
            metrics["temp_pcs_ac"] = round(pcs_ac_temperature, 2)
        if ac_input_voltage is not None:
            metrics["ac_in_voltage"] = round(ac_input_voltage, 2)
        if ac_output_voltage is not None:
            metrics["ac_out_voltage"] = round(ac_output_voltage, 2)
        if ac_input_current is not None:
            metrics["ac_in_current"] = round(ac_input_current, 3)
        if ac_output_current is not None:
            metrics["ac_out_current"] = round(ac_output_current, 3)

        return metrics

    def _update_soc_latch(self, valid_socs: list[int]) -> None:
        """Choose the SOC closest to the previous stable value."""
        candidates = [soc for soc in valid_socs if 0 <= soc <= 100]
        if not candidates:
            return

        if self._soc == 0.0:
            chosen = max(candidates)
        else:
            chosen = min(candidates, key=lambda candidate: abs(candidate - self._soc))

        self._soc = float(chosen)
        self._soc_modules = sorted(candidates, reverse=True)

    def _iter_envelopes(self, payload: bytes) -> list[_ProtoEnvelope]:
        """Parse the top-level MQTT reply into typed protobuf envelopes."""
        envelopes: list[_ProtoEnvelope] = []

        for field_number, wire_type, raw_value in self._parse_message(payload):
            if field_number != 1 or wire_type != 2 or not isinstance(raw_value, bytes):
                continue

            header_fields = self._parse_message(raw_value)
            header_map = self._scalar_field_map(header_fields)
            payload_bytes = self._first_bytes_field(header_fields, 1)

            cmd_func = self._read_int(header_map, 8)
            cmd_id = self._read_int(header_map, 9)

            if payload_bytes is None or cmd_func is None or cmd_id is None:
                continue

            envelopes.append(
                _ProtoEnvelope(
                    cmd_func=cmd_func,
                    cmd_id=cmd_id,
                    payload=self._scalar_field_map(self._parse_message(payload_bytes)),
                )
            )

        return envelopes

    def _scalar_field_map(
        self, fields: list[tuple[int, int, int | float | bytes]]
    ) -> dict[int, int | float]:
        """Collapse parsed fields into a map of scalar values."""
        field_map: dict[int, int | float] = {}
        for field_number, _wire_type, value in fields:
            if isinstance(value, bytes):
                continue
            field_map[field_number] = value
        return field_map

    def _first_bytes_field(
        self,
        fields: list[tuple[int, int, int | float | bytes]],
        field_number: int,
    ) -> bytes | None:
        """Return the first bytes field matching `field_number`."""
        for current_field, _wire_type, value in fields:
            if current_field == field_number and isinstance(value, bytes):
                return value
        return None

    def _parse_message(self, payload: bytes) -> list[tuple[int, int, int | float | bytes]]:
        """Parse a protobuf message without a compiled schema."""
        fields: list[tuple[int, int, int | float | bytes]] = []
        index = 0

        while index < len(payload):
            tag, index = self._read_varint(payload, index)
            field_number = tag >> 3
            wire_type = tag & 0x7

            if wire_type == 0:
                value, index = self._read_varint(payload, index)
                fields.append((field_number, wire_type, value))
                continue

            if wire_type == 1:
                value = struct.unpack("<d", payload[index : index + 8])[0]
                fields.append((field_number, wire_type, value))
                index += 8
                continue

            if wire_type == 2:
                length, index = self._read_varint(payload, index)
                value = payload[index : index + length]
                fields.append((field_number, wire_type, value))
                index += length
                continue

            if wire_type == 5:
                value = struct.unpack("<f", payload[index : index + 4])[0]
                fields.append((field_number, wire_type, value))
                index += 4
                continue

            raise ValueError(f"unsupported wire type {wire_type}")

        return fields

    @staticmethod
    def _read_varint(buffer: bytes, index: int) -> tuple[int, int]:
        """Read a protobuf varint starting at `index`."""
        shift = 0
        value = 0

        while True:
            if index >= len(buffer):
                raise ValueError("truncated varint")
            byte = buffer[index]
            index += 1
            value |= (byte & 0x7F) << shift
            if not (byte & 0x80):
                return value, index
            shift += 7

    @staticmethod
    def _read_int(payload: dict[int, int | float], field_number: int) -> int | None:
        """Return a field as an integer when possible."""
        value = payload.get(field_number)
        if isinstance(value, float):
            return int(round(value))
        if isinstance(value, int):
            return value
        return None

    @staticmethod
    def _read_float(payload: dict[int, int | float], field_number: int) -> float | None:
        """Return a field as a float when possible."""
        value = payload.get(field_number)
        if isinstance(value, (int, float)):
            return float(value)
        return None
