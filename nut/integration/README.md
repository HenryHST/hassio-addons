# NUT Hass.io — Home Assistant Integration

Custom integration for the [NUT Home Assistant Add-on](../README.md). Exposes UPS status and numeric sensors in Home Assistant.

## Features

- **Status sensor**: `ONLINE`, `ONBATT`, `LOWBATT`, `FSD`
- **Numeric sensors**: battery charge (%), input voltage (V), UPS load (%), battery runtime (s) when supported by the driver
- **Event listener**: reacts immediately to `nut.ups_event` from the add-on
- **Polling**: refreshes from `upsd` every 30 seconds

## Installation

### Manual (recommended)

Copy `custom_components/nut_hassio` to:

```text
config/custom_components/nut_hassio/
```

Restart Home Assistant, then add the integration via **Settings → Devices & services → Add integration → NUT Hass.io**.

### With the add-on sensor push

If you use this integration, set in the add-on configuration:

```yaml
enable_home_assistant_sensors: false
```

Otherwise you will have duplicate entities (`sensor.nut_addon_*` from the add-on and `sensor.<ups>_*` from the integration).

## Configuration

| Field | Example | Notes |
|-------|---------|-------|
| Host | IP of Home Assistant | Same host as the add-on |
| Port | `3493` | Mapped port from add-on **Info** |
| UPS name | `myups` | As in add-on `devices[].name` |
| Username | add-on user | e.g. first user from add-on config |
| Password | add-on password | |

## Entities

| Entity | Description |
|--------|-------------|
| `sensor.<ups>_status` | ONLINE / ONBATT / LOWBATT / FSD |
| `sensor.<ups>_battery_charge` | Battery level (%) |
| `sensor.<ups>_input_voltage` | Input voltage (V) |
| `sensor.<ups>_load` | Load (%) |
| `sensor.<ups>_battery_runtime` | Runtime on battery (s) |

## HACS

This folder can be published as a separate GitHub repository for HACS (see [bls_nutrition/integration/README.md](../../bls_nutrition/integration/README.md) for the pattern). Do not add `repository.json` to an integration-only repo.

## Add-on only (no integration)

Enable `enable_home_assistant_sensors: true` in the add-on for entities `sensor.nut_addon_<ups>_*` without installing this integration. See [DOCS.md](../DOCS.md).
