# HG612 Home Assistant Integration

A custom Home Assistant integration for the Huawei HG612 VDSL modem, using the unlocked firmware's telnet interface to expose DSL line stats as sensors.

The modem's HTTP interface reports DSL uptime as always 0 — this integration reads directly from `xdslcmd info --stats` over telnet to get accurate values.

## Sensors

| Entity | Unit | Description |
|---|---|---|
| `sensor.hg612_dsl_uptime` | h | Time since last DSL sync (`Since Link time`) |
| `sensor.hg612_system_uptime` | h | Time since last modem reboot (`/proc/uptime`) |
| `sensor.hg612_dsl_downstream_rate` | kbit/s | Current downstream sync rate (Bearer 0) |
| `sensor.hg612_dsl_upstream_rate` | kbit/s | Current upstream sync rate (Bearer 0) |
| `sensor.hg612_dsl_max_downstream_rate` | kbit/s | Attainable downstream rate |
| `sensor.hg612_dsl_max_upstream_rate` | kbit/s | Attainable upstream rate |
| `sensor.hg612_dsl_snr_downstream` | dB | Downstream signal-to-noise ratio |
| `sensor.hg612_dsl_snr_upstream` | dB | Upstream signal-to-noise ratio |
| `sensor.hg612_dsl_attenuation_downstream` | dB | Downstream line attenuation |
| `sensor.hg612_dsl_attenuation_upstream` | dB | Upstream line attenuation |
| `sensor.hg612_dsl_power_downstream` | dBm | Downstream transmit power |
| `sensor.hg612_dsl_power_upstream` | dBm | Upstream transmit power |

All sensors are included in Home Assistant's long-term statistics.

## Requirements

- HG612 with unlocked firmware and telnet enabled
- Home Assistant 2024.1 or later

## Installation

1. Copy the `custom_components/hg612` directory into your Home Assistant config directory:
   ```
   <config>/custom_components/hg612/
   ```
2. Restart Home Assistant.
3. Go to **Settings → Integrations → Add Integration** and search for **HG612**.
4. Enter the modem's IP address, username, and password (default: `admin`/`admin`).

## Development

### Prerequisites

[mise](https://mise.jdx.dev) manages the Python version and uv installation.

```sh
mise install
```

### Tasks

```sh
mise run install   # install dev dependencies
mise run test      # run tests
mise run lint      # check with ruff
mise run format    # format with ruff
mise run fix       # auto-fix lint issues and format
```

### Project structure

```
custom_components/hg612/
  __init__.py       entry setup and teardown
  config_flow.py    UI setup flow
  coordinator.py    polls the modem every 60s
  telnet.py         telnet connection and raw data fetch
  parser.py         parses xdslcmd output into stats
  sensor.py         sensor entities
  const.py          constants
  manifest.json     HA integration manifest
  strings.json      UI strings
```
