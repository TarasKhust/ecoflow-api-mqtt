"""
Protobuf decoder for EcoFlow River 3 Plus.

Ported from ecoflow-power-management-staging/services/lib/ecoflow_river3plus.py.
Decodes raw protobuf heartbeat packets sent over EcoFlow Cloud MQTT.

Protocol details:
- Field 6  = Battery SOC (0-100, integer percent)
- Field 16 = Temperature (centidegrees, e.g. 25000 = 25.0°C)
- Field 27 = Grid status (0/1 = connected, >1 = disconnected)
- Field 28 = AC input power (raw value ÷ 10 = watts)

Multi-BMS validation filters out ghost/imposter slots:
1. SOC must be in 0-100 range
2. SOC=0 with Temp=0 → empty slot (ghost), reject
3. Temp in 0-100 range → enum/status field, not real temp, reject
4. Missing temperature → disconnected module, reject
5. Passes all checks → valid BMS, aggregate
"""
from __future__ import annotations

import logging
from typing import Any

_LOGGER = logging.getLogger(__name__)


class River3PlusProtoDecoder:
    """Decoder for raw EcoFlow River 3 Plus protobuf heartbeat packets.

    Maintains SOC state for latch logic (chooses SOC closest to last known value).
    Call decode() with each raw MQTT payload; it returns a sensor-data dict or None.
    """

    def __init__(self, device_sn: str) -> None:
        """Initialise decoder.

        Args:
            device_sn: Device serial number (used in log messages only)
        """
        self._sn = device_sn
        self._soc: float = 0.0
        self._soc_modules: list[int] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def decode(self, payload: bytes) -> dict[str, Any] | None:
        """Decode a raw protobuf payload from the River 3 Plus MQTT stream.

        Applies the 5-stage BMS validation filter (ghost check, enum/imposter
        check, temperature-presence requirement) and SOC latch logic.

        Args:
            payload: Raw bytes from MQTT topic /app/device/property/{sn}

        Returns:
            Dict with any of: battery_level (%), temperature (°C), ac_in_power (W).
            Returns None if the packet contained no valid data.
        """
        try:
            messages = self._parse_proto_structure(payload)

            raw_socs: list[int] = []
            valid_temps: list[float] = []
            ac_in_power: float | None = None
            found_valid = False

            for msg in messages:
                m_soc = msg.get(6)
                m_watts = msg.get(28)
                m_temp = msg.get(16)

                # --- AC Input Power ---
                # Tag 28 treated as unsigned 32-bit, scaled by 10.0
                if m_watts is not None:
                    ac_in_power = float(m_watts) / 10.0
                    found_valid = True

                # --- Battery Module Signature Check ---
                if m_soc is not None:
                    is_valid_bms = True

                    # 1. SOC Range Validation (MUST be 0-100%)
                    if not (0 <= m_soc <= 100):
                        is_valid_bms = False
                        _LOGGER.debug("[%s] Rejected SOC out of range: %s", self._sn, m_soc)

                    # 2. Ghost Check: SOC=0 and Temp=0 (empty slot)
                    elif m_soc == 0:
                        if m_temp is None or m_temp == 0:
                            is_valid_bms = False

                    # 3. Enum/Imposter Check
                    # Valid battery temps are in centidegrees (e.g., 25000 = 25.0°C)
                    # Values 0-100 likely represent status enums, not temperatures
                    elif m_temp is not None and 0 < m_temp < 100:
                        is_valid_bms = False

                    # 4. Require Temperature for Valid BMS Module
                    # Real BMS modules ALWAYS report temperature (field 16)
                    elif m_temp is None:
                        is_valid_bms = False
                        _LOGGER.debug("[%s] Rejected SOC without temp: %s%%", self._sn, m_soc)

                    # 5. Valid BMS — aggregate
                    if is_valid_bms:
                        raw_socs.append(m_soc)
                        if m_temp is not None:
                            valid_temps.append(m_temp / 100.0)
                        found_valid = True
                        _LOGGER.debug(
                            "[%s] Valid BMS: SOC=%s%%, Temp=%s°C",
                            self._sn,
                            m_soc,
                            round(m_temp / 100.0, 2) if m_temp else "N/A",
                        )

            if not found_valid:
                return None

            result: dict[str, Any] = {}

            if valid_temps:
                result["temperature"] = round(sum(valid_temps) / len(valid_temps), 2)

            if raw_socs:
                self._update_soc_latch(raw_socs)
                result["battery_level"] = self._soc

            if ac_in_power is not None:
                result["ac_in_power"] = ac_in_power

            return result if result else None

        except Exception as exc:  # noqa: BLE001
            _LOGGER.error("[%s] Protobuf parse error: %s", self._sn, exc)
            return None

    # ------------------------------------------------------------------
    # SOC latch logic
    # ------------------------------------------------------------------

    def _update_soc_latch(self, valid_socs: list[int]) -> None:
        """Choose the SOC value closest to the last known SOC (stability latch).

        On first call (soc == 0.0), picks the maximum valid SOC.
        """
        candidates = [s for s in valid_socs if 0 <= s <= 100]
        if not candidates:
            return

        if self._soc == 0.0:
            chosen = max(candidates)
        else:
            chosen = min(candidates, key=lambda x: abs(x - self._soc))

        self._soc = float(chosen)
        self._soc_modules = sorted(candidates, reverse=True)

    # ------------------------------------------------------------------
    # Hand-rolled protobuf parser (no compiled .proto needed)
    # ------------------------------------------------------------------

    def _parse_proto_structure(self, payload: bytes) -> list[dict[int, Any]]:
        """Recursively parse protobuf bytes into a flat list of field-dicts.

        Length-delimited fields (wire type 2) are recursively parsed as
        sub-messages; their field dicts are merged into the top-level list.
        """
        messages: list[dict[int, Any]] = []
        current_msg: dict[int, Any] = {}

        i = 0
        while i < len(payload):
            try:
                tag, i = self._read_varint(payload, i)
                field = tag >> 3
                wtype = tag & 0x7

                if wtype == 0:  # Varint
                    val, i = self._read_varint(payload, i)
                    current_msg[field] = val
                elif wtype == 2:  # Length-delimited
                    ln, i = self._read_varint(payload, i)
                    if ln > 0:
                        sub = payload[i : i + ln]
                        sub_msgs = self._parse_proto_structure(sub)
                        if sub_msgs:
                            messages.extend(sub_msgs)
                    i += ln
                elif wtype == 1:  # 64-bit — skip
                    i += 8
                elif wtype == 5:  # 32-bit — skip
                    i += 4
                else:
                    break  # unknown wire type → stop parsing
            except Exception:  # noqa: BLE001
                break

        if current_msg:
            messages.append(current_msg)
        return messages

    @staticmethod
    def _read_varint(buf: bytes, i: int) -> tuple[int, int]:
        """Read a varint from *buf* starting at position *i*.

        Returns (value, new_position).
        Raises ValueError if the buffer is truncated.
        """
        shift = 0
        val = 0
        while True:
            if i >= len(buf):
                raise ValueError("truncated varint")
            b = buf[i]
            i += 1
            val |= (b & 0x7F) << shift
            if not (b & 0x80):
                return val, i
            shift += 7
