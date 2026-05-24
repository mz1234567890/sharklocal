# sharklocal

A Python library for local control of Shark robot vacuums, designed for use with Home Assistant integrations. No cloud connection required.

Supports two transport protocols:

- **REST** — Onboard HTTP API
- **MQTT** — Onboard broker on port 1883 using base64-encoded protobuf messages

## Requirements

- Python 3.11+
- `aiohttp` — HTTP/S transport
- `aiomqtt` — MQTT transport
- `PyYAML` — mapping configuration loading

```
pip install sharklocal
```

---

## Quickstart

```python
import asyncio
from sharklocal import VacuumClient

async def main():
    async with VacuumClient(
        "192.168.1.100",
        rest_mappings="sharkiq_v1",
        mqtt_mappings="sharkiq_v1",
    ) as vacuum:
        status = await vacuum.get_status()
        print(status.mode, status.battery_level)

        await vacuum.start_cleaning()

asyncio.run(main())
```

---

## Architecture

```
sharklocal/
├── client.py          # VacuumClient — unified entry point with transport selection
├── rest_client.py     # RESTVacuumClient — async HTTPS/HTTP client (aiohttp)
├── mqtt_client.py     # MQTTVacuumClient — async MQTT client (aiomqtt)
├── protobuf.py        # Pure-Python schema-free protobuf decoder
├── models.py          # VacuumStatus, VacuumEvent, DeviceInfo, VacuumMode
├── exceptions.py      # Typed exception hierarchy
└── mappings/
    ├── __init__.py    # load_* / list_* utilities
    ├── base.py        # RESTMappingConfig, MQTTMappingConfig dataclasses
    ├── rest/
    │   └── sharkiq_v1.yaml
    └── mqtt/
        └── sharkiq_v1.yaml
```

### Transport Selection

`VacuumClient` evaluates which transport to use at action call time:

1. **REST is tried first** if the loaded REST mapping defines the action.
2. **MQTT is the fallback** — used only when REST raises `ConnectError` (host unreachable).
3. If neither transport supports the action, `ActionNotSupportedError` is raised.

All other exceptions (`CommandError`, `DecoderError`, etc.) propagate immediately without attempting the fallback.

---

## Mapping Comparison

The table below shows which features are available per built-in mapping and transport. Use this to decide which transports to configure and whether `probe()` is needed.

| Feature | `sharkiq_v1` REST | `sharkiq_v1` MQTT |
|---|:---:|:---:|
| **Commands** | | |
| Start cleaning | ✅ | ✅ |
| Stop (pause) | ✅ | ✅ |
| Return to dock | ✅ | ✅ |
| Explore / map room | ✅ | ❌ |
| **Status** | | |
| Polling status (mode + battery) | ✅ | ✅ |
| Real-time status (mode) | ❌  | ✅ |
| Event log | ✅ | ❌ |
| **Device info** | | |
| Firmware version | ✅ | ❌ |
| MAC address / unique ID | ✅ | ❌ |
| Wi-Fi SSID + RSSI | ✅ | ❌ |
| IP address | ✅ | ❌ |
| **Reported modes** | | |
| Cleaning | ✅ | ✅ |
| Returning to dock | ✅ | ✅ |
| Docking | ❌ | ✅ |
| Docked (calculated) | ✅ ¹ | ✅ |
| Idle / stopped off dock (calculated) | ✅ ¹ | ❌ |
| Exploring / mapping | ✅ | ❌ |
| **Connection** | | |
| Protocol | HTTPS | MQTT |
| Port | 443 | 1883 |
| SSL | Self-signed (verify disabled) | None |

> ¹ `DOCKED` and `IDLE` are derived from the combination of `mode` and `charging` fields in the REST response — neither is reported directly by the API.  Charging reports connected or not connected, not active charging of the battery.

**Recommendations:**
- Configure **both transports** (`rest_mappings` + `mqtt_mappings`) to get full feature coverage: REST for device info, events, and explore; MQTT for real-time monitoring and docking state.
- If only one transport is available, **REST** provides broader feature coverage. **MQTT** is the better choice when real-time status updates without polling are required.
- Use `probe()` when the correct mapping is not known ahead of time.

---

## VacuumClient

The recommended entry point. Wraps both transport clients and handles selection automatically.

```python
from sharklocal import VacuumClient

async with VacuumClient(
    host="192.168.1.100",
    rest_mappings="sharkiq_v1",          # single string or list
    mqtt_mappings="sharkiq_v1",          # single string or list
    mapping_search_paths=["/custom/mappings"],  # optional
) as vacuum:
    ...
```

Either mapping may be omitted. If only one transport is configured, it is used exclusively.

### Mapping probe

When multiple mapping candidates are supplied, call `probe()` during setup. It tests each mapping by requesting the vacuum status and pins the first one that responds. All subsequent calls use the pinned mapping.

```python
async with VacuumClient(
    "192.168.1.100",
    rest_mappings=["sharkiq_v1", "other_model_v1"],
    mqtt_mappings=["sharkiq_v1"],
) as vacuum:
    result = await vacuum.probe()

    print(result.rest_mapping)   # "sharkiq_v1" or None
    print(result.mqtt_mapping)   # "sharkiq_v1" or None
    print(result.is_connected)   # True if at least one transport responded

    if not result.is_connected:
        raise RuntimeError("Vacuum not reachable")

    status = await vacuum.get_status()
```

With a single mapping per transport, `probe()` is not required — the mapping is pinned automatically.

`probe()` can be called again to re-test and re-pin (e.g. after a firmware update changes the API).

### Active mapping inspection

```python
vacuum.active_rest_mapping   # "sharkiq_v1" or None
vacuum.active_mqtt_mapping   # "sharkiq_v1" or None
```

### `via` — primary transport in use

`vacuum.via` is a string attribute that reflects which transport is the primary connection. It is set automatically on init (single mapping) or after `probe()` (multiple candidates).

| Value | Meaning |
|---|---|
| `"REST"` | REST mapping is pinned and was the first to respond |
| `"MQTT"` | No REST mapping responded; MQTT is the primary transport |
| `"NONE"` | No transport has been confirmed yet (multiple candidates, `probe()` not called, or all candidates failed) |

```python
# Single mapping — via is set immediately on init
vacuum = VacuumClient("192.168.1.100", rest_mappings="sharkiq_v1")
print(vacuum.via)   # "REST"

vacuum = VacuumClient("192.168.1.100", mqtt_mappings="sharkiq_v1")
print(vacuum.via)   # "MQTT"

vacuum = VacuumClient("192.168.1.100", rest_mappings="sharkiq_v1", mqtt_mappings="sharkiq_v1")
print(vacuum.via)   # "REST"  (REST takes priority)

# Multiple candidates — via is NONE until probe() runs
vacuum = VacuumClient("192.168.1.100", rest_mappings=["sharkiq_v1", "other_v1"])
print(vacuum.via)   # "NONE"

result = await vacuum.probe()
print(vacuum.via)   # "REST", "MQTT", or "NONE" depending on what responded
```

### Actions

| Method | REST endpoint | MQTT action |
|---|---|---|
| `get_status()` | `GET /get/status` | `get_status` (status request) |
| `start_cleaning()` | `GET /set/clean_all` | `start_cleaning` (command) |
| `stop()` | `GET /set/stop` | `stop` (command) |
| `go_home()` | `GET /set/go_home` | `go_home` (command) |
| `explore()` | `GET /set/explore` | *(not in MQTT mapping)* |
| `get_events()` | `GET /get/event_log` | *(not in MQTT mapping)* |
| `get_device_info()` | `GET /get/robot_id` | *(not in MQTT mapping)* |
| `get_wifi_status()` | `GET /get/wifi_status` | *(not in MQTT mapping)* |

### Return Types

- **`get_status()`** → `VacuumStatus`
- **`get_events()`** → `list[VacuumEvent]`
- **`get_device_info()`**, **`get_wifi_status()`** → `DeviceInfo`
- Command methods → `bool` (`True` on success)

### Real-Time Monitoring (MQTT)

`VacuumClient` can subscribe to the vacuum's MQTT status topic and invoke a callback on every update. Both sync and `async` callables are supported.

```python
async with VacuumClient("192.168.1.100", mqtt_mappings="sharkiq_v1") as vacuum:
    vacuum.on_status_update(lambda s: print(s.mode, s.battery_level))
    await vacuum.start_monitoring()

    # Monitoring runs as a background task.
    await asyncio.sleep(60)

    await vacuum.stop_monitoring()
```

### Transport Introspection

```python
vacuum.via                              # "REST", "MQTT", or "NONE"
vacuum.active_rest_mapping              # "sharkiq_v1" or None
vacuum.active_mqtt_mapping              # "sharkiq_v1" or None
vacuum.supported_actions()              # ["explore", "get_events", "get_status", ...]
vacuum.transports_for("get_status")     # ["rest", "mqtt"]
vacuum.transports_for("explore")        # ["rest"]
```

---

## Direct Transport Clients

Use the transport clients directly when you need full control.

### RESTVacuumClient

```python
from sharklocal import RESTVacuumClient, load_rest_mapping

mapping = load_rest_mapping("sharkiq_v1")
client = RESTVacuumClient("192.168.1.100", mapping)

status = await client.call("get_status")        # VacuumStatus
events = await client.call("get_events")        # list[VacuumEvent]
wifi   = await client.call("get_wifi_status")   # DeviceInfo

await client.call("start_cleaning")             # True
await client.close()
```

### MQTTVacuumClient

```python
from sharklocal import MQTTVacuumClient, load_mqtt_mapping

mapping = load_mqtt_mapping("sharkiq_v1")
client = MQTTVacuumClient("192.168.1.100", mapping)

status = await client.call("get_status")       # VacuumStatus
await client.call("start_cleaning")            # True

# Monitor with a callback
stop = asyncio.Event()
await client.monitor(lambda s: print(s.mode), stop_event=stop)
```

---

## Data Models

### VacuumStatus

```python
@dataclass
class VacuumStatus:
    mode: VacuumMode           # Normalized operating mode
    battery_level: int | None  # 0–100, or None if unavailable
    charging: bool | None      # True = "connected", False = "unconnected"
    raw: dict                  # Full original response

    @property
    def is_cleaning(self) -> bool: ...
    @property
    def is_docked(self) -> bool: ...  # True for DOCKED and DOCKING only
```

### VacuumMode

```python
class VacuumMode(str, Enum):
    UNKNOWN           = "unknown"
    CLEANING          = "cleaning"
    RETURNING_TO_DOCK = "returning_to_dock"
    DOCKING           = "docking"
    DOCKED            = "docked"
    IDLE              = "idle"       # Stopped and off the dock (mode=ready, charging=unconnected)
    EXPLORING         = "exploring"  # Mapping/exploration run in progress
```

The REST API does not expose `docked` directly. `DOCKED` is derived automatically from two fields:
- `mode: "ready"` **and** `charging: "connected"` → `DOCKED`
- `mode: "ready"` **and** `charging: "unconnected"` → `IDLE` (stopped, off dock)

This combined evaluation is handled automatically by the library — `mode_map` alone is insufficient for the `"ready"` state.

`is_docked` returns `True` only for `DOCKED` and `DOCKING`. `IDLE` and `EXPLORING` vacuums are not considered docked.

### VacuumEvent

```python
@dataclass
class VacuumEvent:
    id: int
    type: str              # e.g. "status_water_tank_removed" (also dustbin on vacuums)
    type_id: int
    timestamp: dict        # {"year": ..., "month": ..., ...}
    current_status: str
    source_type: str
    raw: dict
```

### DeviceInfo

```python
@dataclass
class DeviceInfo:
    firmware: str | None
    mac_address: str | None  # Use this as unique_id in Home Assistant
    ip_address: str | None
    ssid: str | None
    rssi: int | None
    raw: dict
```

> **Note:** The MAC address returned by `get_wifi_status()` is the recommended value to use as `unique_id` when configuring a Home Assistant device. The robot ID endpoint does not expose a serial number.

---

## Mapping Configuration

Mappings are YAML files that describe how to communicate with a specific vacuum model over each transport. Built-in mappings live inside the package. Custom mappings can be placed in any directory and discovered via `mapping_search_paths`.

### REST Mapping

```yaml
id: sharkiq_v1
description: "SharkIQ vacuum local REST API (HTTPS with self-signed certificate)"
transport: https        # "http" or "https"
connection:
  port: 443
  verify_ssl: false     # Set true for CA-signed certs; false for self-signed

# Maps raw mode strings from /get/status to normalized VacuumMode values.
# Note: "ready" cannot be resolved by this map alone — it requires the
# "charging" field. The library evaluates both fields together:
#   mode=ready + charging=connected   → DOCKED
#   mode=ready + charging=unconnected → IDLE
# The "ready": "docked" entry below is a fallback and is overridden in code.
mode_map:
  "ready": "docked"
  "cleaning": "cleaning"
  "go_home": "returning_to_dock"
  "exploring": "exploring"

actions:
  start_cleaning:
    method: GET
    path: "/set/clean_all"

  get_status:
    method: GET
    path: "/get/status"
    response_map: status   # Triggers normalized response parsing
```

**`response_map` values** that trigger normalized parsing:

| Value | Return type |
|---|---|
| `status` | `VacuumStatus` |
| `events` | `list[VacuumEvent]` |
| `robot_id` | `DeviceInfo` |
| `wifi_status` | `DeviceInfo` |

Omitting `response_map` returns the raw parsed JSON.

### MQTT Mapping

```yaml
id: sharkiq_v1
description: "SharkIQ vacuum local MQTT protocol"
connection:
  port: 1883

topics:
  command: "/qfeel/PbInput"
  status:  "/qfeel/PbOutput"

encoding: base64         # Payload encoding for both send and receive

# Name of the registered decoder function (see Extending below)
status_decoder: sharkiq_protobuf_v1

# Maps protobuf OperatingMode integers to normalized VacuumMode strings
modes:
  6: cleaning
  7: returning_to_dock
  13: docking
  14: docked

actions:
  start_cleaning:
    type: command          # Fire-and-forget MQTT publish
    payload: "OgQKAhBLgAEJ"

  get_status:
    type: status_request   # Publish then wait for a response message
    payload: "QgIIAw=="
    timeout: 5.0
```

**Action types:**

- `command` — publishes the payload and returns `True`
- `status_request` — publishes the payload, then subscribes and waits up to `timeout` seconds for the first response; returns the decoded `VacuumStatus`

### Listing and Loading Mappings

```python
from sharklocal import list_rest_mappings, list_mqtt_mappings
from sharklocal import load_rest_mapping, load_mqtt_mapping

list_rest_mappings()                           # ["sharkiq_v1"]
list_mqtt_mappings()                           # ["sharkiq_v1"]
list_rest_mappings(["/custom/mappings"])       # includes custom dir

cfg = load_rest_mapping("sharkiq_v1")
cfg = load_mqtt_mapping("my_model", ["/custom/mappings"])
```

---

## Extending

### Adding a New Mapping

Mappings are YAML files. No code changes are required to add support for a new vacuum model or firmware revision — only a new YAML file (and optionally a decoder function for MQTT).

#### Step 1 — Create the YAML file(s)

Place files under `sharklocal/mappings/rest/` and/or `sharklocal/mappings/mqtt/`. The filename stem becomes the mapping name used in `VacuumClient`.

**Minimal REST mapping** (`sharklocal/mappings/rest/mymodel_v1.yaml`):

```yaml
id: mymodel_v1
description: "My vacuum REST API"
transport: https        # "http" or "https"
connection:
  port: 443
  verify_ssl: true      # false for self-signed certificates

# Map raw mode strings returned by /get/status to normalized VacuumMode values.
mode_map:
  "idle": "docked"
  "cleaning": "cleaning"
  "returning": "returning_to_dock"

actions:
  get_status:
    method: GET
    path: "/api/status"
    response_map: status   # Parses response into VacuumStatus

  start_cleaning:
    method: GET
    path: "/api/clean"

  stop:
    method: POST
    path: "/api/stop"
    body:                  # Optional JSON request body
      force: true
    headers:               # Optional per-action headers
      X-Auth: "token"

  go_home:
    method: GET
    path: "/api/dock"
```

**Minimal MQTT mapping** (`sharklocal/mappings/mqtt/mymodel_v1.yaml`):

```yaml
id: mymodel_v1
description: "My vacuum MQTT protocol"
connection:
  port: 1883

topics:
  command: "/device/cmd"     # Topic to publish commands to
  status:  "/device/status"  # Topic to subscribe to for status

encoding: base64             # "base64" or "raw"
status_decoder: sharkiq_protobuf_v1  # See Step 2 if you need a custom decoder

# Map integer mode values in the payload to normalized VacuumMode strings.
modes:
  1: cleaning
  2: docked
  3: returning_to_dock

actions:
  start_cleaning:
    type: command            # Fire-and-forget publish
    payload: "BASE64_HERE"

  get_status:
    type: status_request     # Publish then wait for a status message
    payload: "BASE64_HERE"
    timeout: 5.0
```

#### Step 2 — Register a custom MQTT decoder (if needed)

Skip this step if your model's MQTT messages use the same protobuf layout as the SharkIQ (`sharkiq_protobuf_v1`) and you can reuse that decoder.

If the payload format differs, register a named decoder in your integration's setup code:

```python
from sharklocal import register_decoder
from sharklocal.models import VacuumMode, VacuumStatus

@register_decoder("mymodel_v1_decoder")
def _decode_mymodel(payload: bytes, modes: dict[int, str]) -> VacuumStatus:
    # payload is the already-decoded bytes (base64 unwrapped if encoding=base64)
    # modes is the dict from the YAML mapping: {int_value: "mode_string", ...}
    mode_int = payload[0]  # example — parse however your protocol requires
    mode_str = modes.get(mode_int, "unknown")
    battery  = payload[1]
    return VacuumStatus(
        mode=VacuumMode(mode_str),
        battery_level=battery,
        raw={"raw_bytes": list(payload)},
    )
```

Then set `status_decoder: mymodel_v1_decoder` in the MQTT YAML.

#### Step 3 — Use the mapping

```python
from sharklocal import VacuumClient

async with ```python
VacuumClient(
    "192.168.1.100",
    rest_mappings="mymodel_v1",
    mqtt_mappings="mymodel_v1",
) as vacuum:
    status = await vacuum.get_status()
```

If the YAML files are not inside the package (e.g. shipped alongside a custom integration), pass their directory via `mapping_search_paths`:

```python
VacuumClient(
    "192.168.1.100",
    rest_mappings="mymodel_v1",
    mapping_search_paths=["/config/custom_components/my_integration/mappings"],
)
```

Built-in mappings are always searched before custom paths. If a name matches in both locations, the built-in mapping takes precedence.

#### Reference — all YAML fields

**REST mapping**

| Field | Required | Default | Description |
|---|---|---|---|
| `id` | yes | — | Unique identifier (should match filename stem) |
| `description` | no | `""` | Human-readable description |
| `transport` | no | `https` | `"http"` or `"https"` |
| `connection.port` | no | `443` | TCP port |
| `connection.verify_ssl` | no | `true` | Disable for self-signed certs |
| `mode_map` | no | `{}` | Raw mode string → `VacuumMode` string |
| `actions.<name>.method` | yes | — | HTTP verb (`GET`, `POST`, etc.) |
| `actions.<name>.path` | yes | — | URL path (e.g. `/get/status`) |
| `actions.<name>.response_map` | no | — | Parser to apply: `status`, `events`, `robot_id`, `wifi_status` |
| `actions.<name>.body` | no | — | JSON body to send with the request |
| `actions.<name>.headers` | no | — | Additional HTTP headers for the action |

**MQTT mapping**

| Field | Required | Default | Description |
|---|---|---|---|
| `id` | yes | — | Unique identifier |
| `description` | no | `""` | Human-readable description |
| `connection.port` | no | `1883` | MQTT broker port |
| `topics.command` | no | `/qfeel/PbInput` | Topic for outbound commands |
| `topics.status` | no | `/qfeel/PbOutput` | Topic for inbound status |
| `encoding` | no | `base64` | `"base64"` or `"raw"` |
| `status_decoder` | yes | — | Name of registered decoder function |
| `modes` | no | `{}` | Integer mode → `VacuumMode` string |
| `actions.<name>.type` | yes | — | `"command"` or `"status_request"` |
| `actions.<name>.payload` | yes | — | Payload string to publish |
| `actions.<name>.timeout` | no | `5.0` | Seconds to wait for `status_request` response |

### Custom Mapping Search Path

```python
VacuumClient(
    "192.168.1.100",
    rest_mappings="my_model_v1",
    mapping_search_paths=["/etc/sharklocal/mappings"],
)
```

Built-in mappings are always searched before custom paths.

---

## Exceptions

All exceptions inherit from `SharklocalError`.

| Exception | When raised |
|---|---|
| `ConnectError` | Host unreachable or connection refused |
| `CommandError` | HTTP error response or MQTT timeout waiting for status |
| `ActionNotSupportedError` | Action not defined in the configured mapping(s) |
| `MappingNotFoundError` | YAML mapping file not found |
| `DecoderError` | MQTT payload cannot be decoded |

```python
from sharklocal import SharklocalError, ConnectError, ActionNotSupportedError

try:
    status = await vacuum.get_status()
except ConnectError:
    # Vacuum is offline
    ...
except ActionNotSupportedError:
    # Mapping doesn't define this action
    ...
except SharklocalError:
    # Catch-all for any library error
    ...
```

---

## Known Quirks

- The `status_water_tank_removed` event type is fired for dustbin removal on vacuums, not only water tank removal on mops. Handle accordingly in Home Assistant event translation.
- The `/get/robot_id` endpoint does not expose a serial number. Use the `mac_address` from `/get/wifi_status` as the device `unique_id`.
- MQTT `go_home` and `stop` send identical payloads in the `sharkiq_v1` mapping — both issue the protobuf stop-and-return command.
- The REST API uses a self-signed TLS certificate. SSL verification is disabled in the `sharkiq_v1` mapping (`verify_ssl: false`).
- The REST `charging` field returns `"connected"` or `"unconnected"` as strings, not a boolean. The library normalises this to `True`/`False` on `VacuumStatus.charging`.
- The REST `mode` field alone is insufficient to determine if a vacuum is docked. `mode: "ready"` with `charging: "connected"` means docked (`VacuumMode.DOCKED`); `mode: "ready"` with `charging: "unconnected"` means the vacuum is stopped but off the dock (`VacuumMode.IDLE`). This combined evaluation is handled automatically by the library.
- `mode: "exploring"` means the vacuum is performing a mapping run, not cleaning. It maps to `VacuumMode.EXPLORING`, not `VacuumMode.CLEANING`.
