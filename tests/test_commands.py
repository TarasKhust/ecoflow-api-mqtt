"""Tests for command builders."""

from __future__ import annotations

import pytest

from custom_components.ecoflow_api.commands import build_command, get_command_builder
from custom_components.ecoflow_api.commands.base import CommandFormat
from custom_components.ecoflow_api.commands.delta_v2 import DeltaV2CommandBuilder
from custom_components.ecoflow_api.commands.pro_v1 import ProV1CommandBuilder
from custom_components.ecoflow_api.commands.pro_v2 import ProV2CommandBuilder
from custom_components.ecoflow_api.commands.smart_plug import SmartPlugCommandBuilder


class TestCommandFormat:
    """Test CommandFormat enum values."""

    def test_all_formats_defined(self):
        assert CommandFormat.PRO_V2 == "pro_v2"
        assert CommandFormat.PRO_V1 == "pro_v1"
        assert CommandFormat.DELTA_V2 == "delta_v2"
        assert CommandFormat.SMART_PLUG == "smart_plug"

    def test_format_count(self):
        assert len(CommandFormat) == 4


class TestGetCommandBuilder:
    """Test get_command_builder factory."""

    def test_pro_v2_builder(self):
        builder = get_command_builder(CommandFormat.PRO_V2)
        assert isinstance(builder, ProV2CommandBuilder)

    def test_pro_v1_builder(self):
        builder = get_command_builder(CommandFormat.PRO_V1)
        assert isinstance(builder, ProV1CommandBuilder)

    def test_delta_v2_builder(self):
        builder = get_command_builder(CommandFormat.DELTA_V2)
        assert isinstance(builder, DeltaV2CommandBuilder)

    def test_smart_plug_builder(self):
        builder = get_command_builder(CommandFormat.SMART_PLUG)
        assert isinstance(builder, SmartPlugCommandBuilder)

    def test_unknown_format_raises(self):
        with pytest.raises(KeyError):
            get_command_builder("nonexistent")


class TestProV2CommandBuilder:
    """Test ProV2 command format (Delta Pro 3, Stream Ultra X)."""

    def test_build_basic_command(self):
        result = build_command(
            CommandFormat.PRO_V2,
            "DCABCD1234",
            {"cfgAcOutOpen": True},
        )
        assert result == {
            "sn": "DCABCD1234",
            "cmdId": 17,
            "cmdFunc": 254,
            "dirDest": 1,
            "dirSrc": 1,
            "dest": 2,
            "needAck": True,
            "params": {"cfgAcOutOpen": True},
        }

    def test_build_with_multiple_params(self):
        result = build_command(
            CommandFormat.PRO_V2,
            "SN123",
            {"cfgMaxChgSoc": 80, "cfgMinDsgSoc": 20},
        )
        assert result["sn"] == "SN123"
        assert result["params"] == {"cfgMaxChgSoc": 80, "cfgMinDsgSoc": 20}
        assert result["cmdId"] == 17
        assert result["cmdFunc"] == 254

    def test_build_with_empty_params(self):
        result = build_command(
            CommandFormat.PRO_V2,
            "SN123",
            {},
        )
        assert result["params"] == {}
        assert result["sn"] == "SN123"

    def test_fixed_fields_always_present(self):
        result = build_command(CommandFormat.PRO_V2, "SN", {"x": 1})
        assert result["dirDest"] == 1
        assert result["dirSrc"] == 1
        assert result["dest"] == 2
        assert result["needAck"] is True


class TestProV1CommandBuilder:
    """Test ProV1 command format (Delta Pro original)."""

    def test_build_with_cmd_set_and_id(self):
        result = build_command(
            CommandFormat.PRO_V1,
            "DCPRO1234",
            {"cfgAcOutOpen": 1},
            cmd_set=32,
            cmd_id=66,
        )
        assert result == {
            "sn": "DCPRO1234",
            "params": {
                "cmdSet": 32,
                "id": 66,
                "cfgAcOutOpen": 1,
            },
        }

    def test_params_merged_with_cmd_set_id(self):
        result = build_command(
            CommandFormat.PRO_V1,
            "SN",
            {"a": 1, "b": 2},
            cmd_set=10,
            cmd_id=20,
        )
        params = result["params"]
        assert params["cmdSet"] == 10
        assert params["id"] == 20
        assert params["a"] == 1
        assert params["b"] == 2

    def test_missing_cmd_set_raises(self):
        with pytest.raises(KeyError):
            build_command(
                CommandFormat.PRO_V1,
                "SN",
                {"x": 1},
                cmd_id=1,
            )

    def test_missing_cmd_id_raises(self):
        with pytest.raises(KeyError):
            build_command(
                CommandFormat.PRO_V1,
                "SN",
                {"x": 1},
                cmd_set=1,
            )


class TestDeltaV2CommandBuilder:
    """Test DeltaV2 command format (Delta 2)."""

    def test_build_with_module_and_operate_type(self):
        result = build_command(
            CommandFormat.DELTA_V2,
            "DELT2SN",
            {"acOutOpen": 1},
            module_type=5,
            operate_type="acOutCfg",
        )
        assert result["sn"] == "DELT2SN"
        assert result["version"] == "1.0"
        assert result["moduleType"] == 5
        assert result["operateType"] == "acOutCfg"
        assert result["params"] == {"acOutOpen": 1}
        assert isinstance(result["id"], int)

    def test_id_is_timestamp_ms(self):
        result = build_command(
            CommandFormat.DELTA_V2,
            "SN",
            {},
            module_type=1,
            operate_type="test",
        )
        # ID should be roughly current time in milliseconds
        assert result["id"] > 1_000_000_000_000  # After year 2001 in ms

    def test_missing_module_type_raises(self):
        with pytest.raises(KeyError):
            build_command(
                CommandFormat.DELTA_V2,
                "SN",
                {"x": 1},
                operate_type="test",
            )

    def test_missing_operate_type_raises(self):
        with pytest.raises(KeyError):
            build_command(
                CommandFormat.DELTA_V2,
                "SN",
                {"x": 1},
                module_type=1,
            )


class TestSmartPlugCommandBuilder:
    """Test SmartPlug command format (Smart Plug S401)."""

    def test_build_with_cmd_code(self):
        result = build_command(
            CommandFormat.SMART_PLUG,
            "SP401SN",
            {"plugSwitch": 1},
            cmd_code="WN511_SOCKET_SET_PLUG_SWITCH_MESSAGE",
        )
        assert result == {
            "sn": "SP401SN",
            "cmdCode": "WN511_SOCKET_SET_PLUG_SWITCH_MESSAGE",
            "params": {"plugSwitch": 1},
        }

    def test_missing_cmd_code_raises(self):
        with pytest.raises(KeyError):
            build_command(
                CommandFormat.SMART_PLUG,
                "SN",
                {"x": 1},
            )

    def test_build_with_multiple_params(self):
        result = build_command(
            CommandFormat.SMART_PLUG,
            "SN",
            {"brightness": 512, "colorTem": 4000},
            cmd_code="WN511_SET_BRIGHTNESS",
        )
        assert result["params"]["brightness"] == 512
        assert result["params"]["colorTem"] == 4000
        assert result["cmdCode"] == "WN511_SET_BRIGHTNESS"


class TestBuildCommandFactory:
    """Test the build_command factory function dispatching."""

    def test_dispatches_to_correct_builder(self):
        """Verify each format produces a different payload structure."""
        sn = "SN123"
        params = {"key": "value"}

        pro_v2 = build_command(CommandFormat.PRO_V2, sn, params)
        assert "cmdId" in pro_v2
        assert "cmdFunc" in pro_v2

        pro_v1 = build_command(CommandFormat.PRO_V1, sn, params, cmd_set=1, cmd_id=2)
        assert "cmdSet" in pro_v1["params"]

        delta_v2 = build_command(CommandFormat.DELTA_V2, sn, params, module_type=1, operate_type="t")
        assert "moduleType" in delta_v2

        smart = build_command(CommandFormat.SMART_PLUG, sn, params, cmd_code="CMD")
        assert "cmdCode" in smart
