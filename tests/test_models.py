"""Tests for sharklocal.models."""

import pytest

from sharklocal.models import (
    DeviceInfo,
    ProbeResult,
    VacuumEvent,
    VacuumMode,
    VacuumStatus,
)


# ---------------------------------------------------------------------------
# VacuumMode
# ---------------------------------------------------------------------------


def test_vacuum_mode_all_values():
    expected = {"unknown", "cleaning", "returning_to_dock", "docking", "docked", "idle", "exploring"}
    actual = {m.value for m in VacuumMode}
    assert actual == expected


def test_vacuum_mode_count():
    assert len(VacuumMode) == 7


def test_vacuum_mode_is_str_enum():
    assert VacuumMode.CLEANING == "cleaning"


# ---------------------------------------------------------------------------
# VacuumStatus
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "mode, expected_cleaning",
    [
        (VacuumMode.CLEANING, True),
        (VacuumMode.DOCKED, False),
        (VacuumMode.DOCKING, False),
        (VacuumMode.RETURNING_TO_DOCK, False),
        (VacuumMode.IDLE, False),
        (VacuumMode.EXPLORING, False),
        (VacuumMode.UNKNOWN, False),
    ],
)
def test_vacuum_status_is_cleaning(mode, expected_cleaning):
    status = VacuumStatus(mode=mode)
    assert status.is_cleaning is expected_cleaning


@pytest.mark.parametrize(
    "mode, expected_docked",
    [
        (VacuumMode.DOCKED, True),
        (VacuumMode.DOCKING, True),
        (VacuumMode.CLEANING, False),
        (VacuumMode.RETURNING_TO_DOCK, False),
        (VacuumMode.IDLE, False),
        (VacuumMode.EXPLORING, False),
        (VacuumMode.UNKNOWN, False),
    ],
)
def test_vacuum_status_is_docked(mode, expected_docked):
    status = VacuumStatus(mode=mode)
    assert status.is_docked is expected_docked


def test_vacuum_status_optional_fields_default_none():
    status = VacuumStatus(mode=VacuumMode.IDLE)
    assert status.battery_level is None
    assert status.charging is None


def test_vacuum_status_raw_default_empty_dict():
    status = VacuumStatus(mode=VacuumMode.IDLE)
    assert status.raw == {}


def test_vacuum_status_fields_set():
    status = VacuumStatus(mode=VacuumMode.CLEANING, battery_level=75, charging=False, raw={"x": 1})
    assert status.mode == VacuumMode.CLEANING
    assert status.battery_level == 75
    assert status.charging is False
    assert status.raw == {"x": 1}


# ---------------------------------------------------------------------------
# VacuumEvent
# ---------------------------------------------------------------------------


def test_vacuum_event_fields():
    ts = {"year": 2026, "month": 5, "day": 1}
    event = VacuumEvent(
        id=42,
        type="status_battery_low",
        type_id=1001,
        timestamp=ts,
        current_status="low",
        source_type="operation_unit",
        raw={"extra": True},
    )
    assert event.id == 42
    assert event.type == "status_battery_low"
    assert event.type_id == 1001
    assert event.timestamp == ts
    assert event.current_status == "low"
    assert event.source_type == "operation_unit"
    assert event.raw == {"extra": True}


def test_vacuum_event_raw_default():
    ts = {}
    event = VacuumEvent(id=1, type="t", type_id=0, timestamp=ts, current_status="", source_type="s")
    assert event.raw == {}


# ---------------------------------------------------------------------------
# DeviceInfo
# ---------------------------------------------------------------------------


def test_device_info_all_optional():
    info = DeviceInfo()
    assert info.firmware is None
    assert info.mac_address is None
    assert info.ip_address is None
    assert info.ssid is None
    assert info.rssi is None
    assert info.raw == {}


def test_device_info_fields_set():
    info = DeviceInfo(
        firmware="v1.0",
        mac_address="AA:BB:CC:DD:EE:FF",
        ip_address="192.168.1.10",
        ssid="HomeNet",
        rssi=-50,
        raw={"status": "connected"},
    )
    assert info.firmware == "v1.0"
    assert info.mac_address == "AA:BB:CC:DD:EE:FF"
    assert info.ip_address == "192.168.1.10"
    assert info.ssid == "HomeNet"
    assert info.rssi == -50


# ---------------------------------------------------------------------------
# ProbeResult
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "rest_mapping, mqtt_mapping, has_rest, has_mqtt, is_connected",
    [
        ("sharkiq_v1", "sharkiq_v1", True, True, True),
        ("sharkiq_v1", None, True, False, True),
        (None, "sharkiq_v1", False, True, True),
        (None, None, False, False, False),
    ],
)
def test_probe_result_properties(rest_mapping, mqtt_mapping, has_rest, has_mqtt, is_connected):
    result = ProbeResult(rest_mapping=rest_mapping, mqtt_mapping=mqtt_mapping)
    assert result.has_rest is has_rest
    assert result.has_mqtt is has_mqtt
    assert result.is_connected is is_connected


def test_probe_result_defaults_none():
    result = ProbeResult()
    assert result.rest_mapping is None
    assert result.mqtt_mapping is None
