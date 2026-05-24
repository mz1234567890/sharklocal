"""Data models for vacuum state and device information."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class VacuumMode(str, Enum):
    """Normalized operating modes across all transports."""

    UNKNOWN = "unknown"
    CLEANING = "cleaning"
    RETURNING_TO_DOCK = "returning_to_dock"
    DOCKING = "docking"
    DOCKED = "docked"
    IDLE = "idle"  # Powered on but not cleaning and not on the charging dock
    EXPLORING = "exploring"  # Mapping/exploration run in progress



@dataclass
class VacuumStatus:
    """Normalized vacuum status, independent of transport protocol."""

    mode: VacuumMode
    battery_level: Optional[int] = None
    charging: Optional[bool] = None
    raw: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_cleaning(self) -> bool:
        return self.mode == VacuumMode.CLEANING

    @property
    def is_docked(self) -> bool:
        return self.mode in (VacuumMode.DOCKED, VacuumMode.DOCKING)


@dataclass
class VacuumEvent:
    """A single event from the vacuum event log."""

    id: int
    type: str
    type_id: int
    timestamp: Dict[str, int]
    current_status: str
    source_type: str
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DeviceInfo:
    """Device identity and connectivity information."""

    firmware: Optional[str] = None
    mac_address: Optional[str] = None
    ip_address: Optional[str] = None
    ssid: Optional[str] = None
    rssi: Optional[int] = None
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProbeResult:
    """Result of a :meth:`VacuumClient.probe` call."""

    rest_mapping: Optional[str] = None
    """``id`` of the REST mapping that responded successfully, or ``None``."""

    mqtt_mapping: Optional[str] = None
    """``id`` of the MQTT mapping that responded successfully, or ``None``."""

    @property
    def has_rest(self) -> bool:
        """``True`` if a working REST mapping was found."""
        return self.rest_mapping is not None

    @property
    def has_mqtt(self) -> bool:
        """``True`` if a working MQTT mapping was found."""
        return self.mqtt_mapping is not None

    @property
    def is_connected(self) -> bool:
        """``True`` if at least one transport responded successfully."""
        return self.has_rest or self.has_mqtt
