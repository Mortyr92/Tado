# TadoLocal for Home Assistant

A Home Assistant custom integration for the [TadoLocal](https://github.com/ampscm/TadoLocal) bridge.
It talks to the TadoLocal REST API on your local network – no Tado cloud, no rate limits.

## Features

- **Climate** entity per Tado zone: set target temperature, switch heating on/off, see current heating action.
- **Sensors** for every zone and every physical device: temperature, humidity, target temperature, valve position, mode.
- **Binary sensors**: heating active, window open, battery low, zone leader, bridge connected, cloud authenticated.
- Optional Bearer API key support (`TADO_API_KEYS` on the bridge).
- Configurable polling interval.
- New zones/devices on the bridge are picked up automatically.

## Installation (HACS)

1. In HACS go to **Integrations → ⋮ → Custom repositories**.
2. Add this repository URL with category **Integration**.
3. Search for **TadoLocal** in HACS and install it.
4. Restart Home Assistant.
5. Go to **Settings → Devices & services → Add integration** and search for **TadoLocal**.
6. Enter the host/IP of your TadoLocal bridge, the port (default `4407`) and, if configured, the API key.

### Manual installation

Copy `custom_components/tadolocal` into `<config>/custom_components/` and restart Home Assistant.

## Controlling zones

Each zone gets a `climate.<zone_name>` entity:

| Action | TadoLocal call |
|---|---|
| Set temperature | `POST /zones/{id}/set?temperature=X&heating_enabled=true` |
| HVAC mode **heat** | `POST /zones/{id}/set?temperature=-1&heating_enabled=true` (keeps stored setpoint) |
| HVAC mode **off** | `POST /zones/{id}/set?heating_enabled=false` |

## Options

Polling interval can be changed via **Configure** on the integration entry (minimum 5 seconds).
