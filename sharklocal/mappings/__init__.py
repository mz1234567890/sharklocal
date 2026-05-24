"""Mapping loader utilities for REST and MQTT transport configurations."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Union

import yaml

from ..exceptions import MappingNotFoundError
from .base import MQTTMappingConfig, RESTMappingConfig

_BUILTIN_REST_DIR = Path(__file__).parent / "rest"
_BUILTIN_MQTT_DIR = Path(__file__).parent / "mqtt"


def load_rest_mapping(
    name: str,
    search_paths: Optional[List[Union[str, Path]]] = None,
) -> RESTMappingConfig:
    """Load a REST mapping by name.

    Searches the built-in mappings directory first, then any additional
    paths provided in *search_paths*.

    Args:
        name: Mapping filename stem (e.g. ``"sharkiq_v1"``).
        search_paths: Optional list of additional directories to search.

    Raises:
        MappingNotFoundError: If no matching YAML file is found.
    """
    for directory in [_BUILTIN_REST_DIR, *[Path(p) for p in (search_paths or [])]]:
        candidate = directory / f"{name}.yaml"
        if candidate.is_file():
            with open(candidate) as f:
                data = yaml.safe_load(f)
            return RESTMappingConfig.from_dict(data)
    raise MappingNotFoundError(
        f"REST mapping '{name}' not found. "
        f"Available built-in mappings: {list_rest_mappings()}"
    )


def load_mqtt_mapping(
    name: str,
    search_paths: Optional[List[Union[str, Path]]] = None,
) -> MQTTMappingConfig:
    """Load an MQTT mapping by name.

    Searches the built-in mappings directory first, then any additional
    paths provided in *search_paths*.

    Args:
        name: Mapping filename stem (e.g. ``"sharkiq_v1"``).
        search_paths: Optional list of additional directories to search.

    Raises:
        MappingNotFoundError: If no matching YAML file is found.
    """
    for directory in [_BUILTIN_MQTT_DIR, *[Path(p) for p in (search_paths or [])]]:
        candidate = directory / f"{name}.yaml"
        if candidate.is_file():
            with open(candidate) as f:
                data = yaml.safe_load(f)
            return MQTTMappingConfig.from_dict(data)
    raise MappingNotFoundError(
        f"MQTT mapping '{name}' not found. "
        f"Available built-in mappings: {list_mqtt_mappings()}"
    )


def list_rest_mappings(
    search_paths: Optional[List[Union[str, Path]]] = None,
) -> List[str]:
    """Return names of all available REST mappings."""
    names: set[str] = set()
    for directory in [_BUILTIN_REST_DIR, *[Path(p) for p in (search_paths or [])]]:
        if directory.is_dir():
            names.update(p.stem for p in directory.glob("*.yaml"))
    return sorted(names)


def list_mqtt_mappings(
    search_paths: Optional[List[Union[str, Path]]] = None,
) -> List[str]:
    """Return names of all available MQTT mappings."""
    names: set[str] = set()
    for directory in [_BUILTIN_MQTT_DIR, *[Path(p) for p in (search_paths or [])]]:
        if directory.is_dir():
            names.update(p.stem for p in directory.glob("*.yaml"))
    return sorted(names)
