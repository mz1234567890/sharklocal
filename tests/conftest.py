"""Shared fixtures for the sharklocal test suite."""

from __future__ import annotations

import asyncio
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock

import pytest

from sharklocal.mappings.base import (
    MQTTActionSpec,
    MQTTMappingConfig,
    RESTActionSpec,
    RESTMappingConfig,
)
from sharklocal.models import VacuumMode, VacuumStatus


# ---------------------------------------------------------------------------
# Mapping config fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def rest_mapping() -> RESTMappingConfig:
    return RESTMappingConfig(
        id="test_rest_v1",
        description="Test REST mapping",
        transport="https",
        port=443,
        verify_ssl=False,
        actions={
            "get_status": RESTActionSpec(
                method="GET",
                path="/get/status",
                response_map="status",
            ),
            "get_events": RESTActionSpec(
                method="GET",
                path="/get/event_log",
                response_map="events",
            ),
            "get_robot_id": RESTActionSpec(
                method="GET",
                path="/get/robot_id",
                response_map="robot_id",
            ),
            "get_wifi_status": RESTActionSpec(
                method="GET",
                path="/get/wifi_status",
                response_map="wifi_status",
            ),
            "start_cleaning": RESTActionSpec(
                method="GET",
                path="/set/clean_all",
            ),
            "stop": RESTActionSpec(
                method="GET",
                path="/set/stop",
            ),
            "go_home": RESTActionSpec(
                method="GET",
                path="/set/go_home",
            ),
            "explore": RESTActionSpec(
                method="GET",
                path="/set/explore",
            ),
        },
        mode_map={
            "ready": "docked",
            "cleaning": "cleaning",
            "go_home": "returning_to_dock",
            "exploring": "exploring",
        },
    )


@pytest.fixture()
def mqtt_mapping() -> MQTTMappingConfig:
    return MQTTMappingConfig(
        id="test_mqtt_v1",
        description="Test MQTT mapping",
        port=1883,
        command_topic="/qfeel/PbInput",
        status_topic="/qfeel/PbOutput",
        encoding="base64",
        status_decoder="sharkiq_protobuf_v1",
        actions={
            "start_cleaning": MQTTActionSpec(type="command", payload="AAAA"),
            "stop": MQTTActionSpec(type="command", payload="BBBB"),
            "go_home": MQTTActionSpec(type="command", payload="CCCC"),
            "get_status": MQTTActionSpec(type="status_request", payload="DDDD", timeout=5.0),
        },
        modes={6: "cleaning", 7: "returning_to_dock", 13: "docking", 14: "docked"},
    )


# ---------------------------------------------------------------------------
# Sample API response dicts (mirrors apidocs/example.*.json)
# ---------------------------------------------------------------------------


@pytest.fixture()
def status_json() -> Dict[str, Any]:
    return {
        "voltage": 16640,
        "mode": "ready",
        "cleaning_parameter_set": 1,
        "battery_level": 77,
        "charging": "charging",
        "time": {"year": 2026, "month": 5, "day": 1, "hour": 3, "min": 11, "sec": 6, "day_of_week": 5},
        "startup_time": {"year": 2026, "month": 5, "day": 1, "hour": 0, "min": 46, "sec": 51, "day_of_week": 5},
    }


@pytest.fixture()
def events_json() -> Dict[str, Any]:
    return {
        "robot_events": [
            {
                "id": 1,
                "type": "status_robot_lifted",
                "type_id": 2010,
                "timestamp": {"year": 2026, "month": 5, "day": 1, "hour": 0, "min": 46, "sec": 50},
                "current_status": "",
                "source_type": "operation_unit",
            },
            {
                "id": 2,
                "type": "status_robot_setback",
                "type_id": 2011,
                "timestamp": {"year": 2026, "month": 5, "day": 1, "hour": 0, "min": 46, "sec": 51},
                "current_status": "",
                "source_type": "operation_unit",
            },
        ]
    }


@pytest.fixture()
def robot_id_json() -> Dict[str, Any]:
    return {
        "firmware": "RV2000-1.15.0-release:3.10.2821",
        "model": "005:000:000:000:005",
        "name": "Maggie",
        "unique_id": "aicu-aicguckbqchxpajqiliu",
        "devices": [],
    }


@pytest.fixture()
def wifi_json() -> Dict[str, Any]:
    return {
        "status": "connected",
        "ssid": "MyWifi",
        "rssi": -45,
        "mac_address": "AA:BB:CC:DD:EE:FF",
        "ip_address": "192.168.1.100",
        "type": "wifi",
    }


# ---------------------------------------------------------------------------
# Reusable VacuumStatus
# ---------------------------------------------------------------------------


@pytest.fixture()
def docked_status() -> VacuumStatus:
    return VacuumStatus(mode=VacuumMode.DOCKED, battery_level=80, charging=True, raw={})


@pytest.fixture()
def cleaning_status() -> VacuumStatus:
    return VacuumStatus(mode=VacuumMode.CLEANING, battery_level=50, charging=False, raw={})
