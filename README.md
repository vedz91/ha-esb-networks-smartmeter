# ESB Networks Smart Meter — Home Assistant Integration

<p align="center">
  <img src="https://raw.githubusercontent.com/vedz91/ha-esb-networks-smartmeter/main/custom_components/esb_networks_smartmeter/brand/logo.png" alt="ESB Networks Smart Meter" width="200"/>
</p>

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/vedz91/ha-esb-networks-smartmeter)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2023.1.0%2B-brightgreen.svg)](https://www.home-assistant.io/)

Monitor your Irish electricity usage directly in Home Assistant. This integration connects to your [ESB Networks My Account](https://myaccount.esbnetworks.ie) portal and automatically downloads your smart meter's 30-minute interval data every 24 hours, tracking both active import (consumption) and active export (solar microgeneration return). It also injects 15 days of historical interval data into Home Assistant's Energy Dashboard on every successful refresh.

> **Attribution:** This integration is a fork of [antoine-voiry/home-assistant-esb-smart-meter-integration](https://github.com/antoine-voiry/home-assistant-esb-smart-meter-integration), with additional features added for export/microgen support, diagnostic sensors, current-interval readings, and Energy Dashboard integration.

---

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Sensors](#sensors)
- [Energy Dashboard](#energy-dashboard)
- [How It Works](#how-it-works)
- [CAPTCHA Handling](#captcha-handling)
- [Known Limitations](#known-limitations)
- [Troubleshooting](#troubleshooting)
- [Changelog](#changelog)
- [License & Credits](#license--credits)

---

## Features

- **19 sensors** covering consumption, grid export, current interval, and diagnostics
- **Energy Dashboard ready** — automatically injects 15 days of 30-minute historical statistics into HA Recorder on every successful refresh
- **Microgen/solar support** — partitions CSV data by read type, so export sensors accurately track energy sent back to the grid (reports 0 on standard accounts)
- **24-hour smart caching** to minimise API calls
- **Circuit breaker pattern** to prevent hammering the ESB API on repeated failures
- **70+ rotating user agents** to reduce CAPTCHA trigger frequency
- **CAPTCHA detection** with persistent HA notification and manual cookie bypass option
- **Session reuse** — caches authentication sessions for up to 14 days
- **Startup delay** — waits 5–10 minutes after HA boot before first poll to avoid login failures during startup

---

## Prerequisites

- An ESB Networks account at [myaccount.esbnetworks.ie](https://myaccount.esbnetworks.ie)
- Your 11-digit MPRN (Meter Point Reference Number) — found on your electricity bill
- Home Assistant 2023.1.0 or later
- A smart meter installed at your premises

---

## Installation

### HACS (Recommended)

1. Open **HACS** in Home Assistant
2. Go to **Integrations**
3. Click the **three dots** (⋮) in the top right corner → **Custom repositories**
4. Paste `https://github.com/vedz91/ha-esb-networks-smartmeter` in the URL field
5. Set category to **Integration** and click **Add**
6. Search for **ESB Networks Smart Meter** and click **Download**
7. Restart Home Assistant

### Manual

1. Download or clone this repository
2. Copy the `custom_components/esb_networks_smartmeter/` directory into your Home Assistant `config/custom_components/` folder
3. Restart Home Assistant

---

## Configuration

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for **ESB Networks Smart Meter**
3. Enter your ESB Networks credentials:
   - **Username** — your ESB Networks account email
   - **Password** — your ESB Networks account password
   - **MPRN** — your 11-digit meter point reference number
4. Click **Submit**

The integration will authenticate and begin fetching data. The first successful data pull may take a few minutes.

---

## Sensors

All sensors are grouped under a single **ESB Smart Meter ({MPRN})** device in the Home Assistant UI.

### Consumption (Import)

| Sensor Name | Entity ID | Unit | Description |
|-------------|-----------|------|-------------|
| ESB Electricity Usage: Today | `sensor.esb_electricity_usage_today` | kWh | Total import since midnight |
| ESB Electricity Usage: Last 24 Hours | `sensor.esb_electricity_usage_last_24_hours` | kWh | Import over the past 24 hours |
| ESB Electricity Usage: This Week | `sensor.esb_electricity_usage_this_week` | kWh | Total import since Monday |
| ESB Electricity Usage: Last 7 Days | `sensor.esb_electricity_usage_last_7_days` | kWh | Import over the past 7 days |
| ESB Electricity Usage: This Month | `sensor.esb_electricity_usage_this_month` | kWh | Total import since the 1st of the month |
| ESB Electricity Usage: Last 30 Days | `sensor.esb_electricity_usage_last_30_days` | kWh | Import over the past 30 days |

### Grid Export (Microgen / Solar)

Reports `0.0` on standard (non-solar) accounts. No configuration needed — the integration automatically detects export rows in the ESB CSV data.

| Sensor Name | Entity ID | Unit | Description |
|-------------|-----------|------|-------------|
| ESB Electricity Exported: Today | `sensor.esb_electricity_exported_today` | kWh | Total export since midnight |
| ESB Electricity Exported: Last 24 Hours | `sensor.esb_electricity_exported_last_24_hours` | kWh | Export over the past 24 hours |
| ESB Electricity Exported: This Week | `sensor.esb_electricity_exported_this_week` | kWh | Total export since Monday |
| ESB Electricity Exported: Last 7 Days | `sensor.esb_electricity_exported_last_7_days` | kWh | Export over the past 7 days |
| ESB Electricity Exported: This Month | `sensor.esb_electricity_exported_this_month` | kWh | Total export since the 1st of the month |
| ESB Electricity Exported: Last 30 Days | `sensor.esb_electricity_exported_last_30_days` | kWh | Export over the past 30 days |

### Current Interval

The most recent 30-minute interval reading from the ESB CSV. ESB data is typically 1–2 days behind real time, so these reflect the most recent available reading rather than live usage.

| Sensor Name | Entity ID | Unit | Description |
|-------------|-----------|------|-------------|
| ESB Electricity Usage: Now | `sensor.esb_electricity_usage_now` | kWh | Most recent 30-min import interval |
| ESB Electricity Export: Now | `sensor.esb_electricity_export_now` | kWh | Most recent 30-min export interval |

### Diagnostic

| Sensor Name | Entity ID | Description |
|-------------|-----------|-------------|
| ESB Smart Meter: Last Update | `sensor.esb_smart_meter_last_update` | Timestamp of the last successful integration poll |
| ESB Smart Meter: Latest Reading | `sensor.esb_smart_meter_latest_reading` | Timestamp of the most recent row in the ESB CSV data |
| ESB Smart Meter: API Status | `sensor.esb_smart_meter_api_status` | `online` / `error` / `unknown` |
| ESB Smart Meter: Data Age | `sensor.esb_smart_meter_data_age` | Hours since the last successful data refresh |
| ESB Smart Meter: Circuit Breaker | `sensor.esb_smart_meter_circuit_breaker` | `closed` / `open` / `half_open` with failure counts in attributes |

---

## Energy Dashboard

On every successful data refresh, this integration injects the last 15 days of 30-minute interval data directly into Home Assistant's long-term statistics. This means the Energy Dashboard shows real historical usage immediately after setup — no waiting for data to accumulate day by day.

### Adding to the Energy Dashboard

1. Go to **Settings** → **Dashboards** → **Energy**
2. Under **Electricity grid** → **Grid consumption**, click **Add consumption**
3. Search for the statistic ID: `esb_networks_smartmeter:{your_mprn}_import`
4. For solar/microgen accounts, under **Return to grid**, add: `esb_networks_smartmeter:{your_mprn}_export`

Replace `{your_mprn}` with your 11-digit MPRN.

---

## How It Works

1. **Authentication** — the integration performs an 8-step OAuth2-like login flow against the ESB Networks portal, mimicking browser behaviour with randomised request delays and rotating user agents
2. **Data fetch** — after a successful login, it downloads your meter's full CSV history from ESB's `DataHub/DownloadHdfPeriodic` endpoint
3. **CSV parsing** — rows are partitioned by `Read Type` column into import (`Active Import Interval`) and export (`Active Export Interval`) streams
4. **Session caching** — the authenticated session is cached on disk for up to 14 days, so the full login flow only runs when the session expires
5. **Statistics injection** — after each successful fetch, 15 days of 30-minute interval data is written to HA's Recorder via `async_import_statistics`, using statistic IDs `esb_networks_smartmeter:{mprn}_import` and `esb_networks_smartmeter:{mprn}_export`
6. **24-hour polling** — the coordinator refreshes once per day; on failure it retries up to 3 times with 30-minute waits before giving up until the next day

---

## CAPTCHA Handling

ESB Networks may occasionally serve a CAPTCHA challenge during login, which the integration cannot solve automatically.

**When CAPTCHA is detected:**
- A persistent notification appears in Home Assistant explaining the issue
- The integration backs off for 24 hours before retrying
- The circuit breaker may open if failures accumulate

**Manual bypass:**
1. Visit [myaccount.esbnetworks.ie](https://myaccount.esbnetworks.ie) in your browser
2. Complete the CAPTCHA and log in manually
3. Leave your browser session active for ~5 minutes
4. The integration will detect the active session and resume automatically on the next retry

**Reducing CAPTCHA frequency:**
- The integration uses 70+ rotating user agents and randomised request timing to mimic organic browser traffic
- Avoid triggering too many manual re-authentications in a short period

---

## Known Limitations

- **ESB data lag** — meter readings are typically 1–2 days behind real time; "Now" sensors reflect the most recent available reading, not live usage
- **Unofficial API** — this integration uses ESB Networks' web portal, not an official API. ESB Networks could change their login flow at any time, which may break authentication
- **CAPTCHA risk** — frequent restarts or re-authentications increase the chance of CAPTCHA challenges
- **Ireland only** — this integration is specific to ESB Networks (Republic of Ireland)

---

## Troubleshooting

### Enable debug logging

Add the following to your `configuration.yaml` and restart Home Assistant:

```yaml
logger:
  default: info
  logs:
    custom_components.esb_networks_smartmeter: debug
```

### Common issues

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Sensors show `Unavailable` after setup | Initial fetch still in progress | Wait 10–15 minutes; check logs for errors |
| `API Status` shows `error` | Authentication failed or CAPTCHA | Check logs; try the manual CAPTCHA bypass above |
| Circuit breaker `open` | Multiple consecutive auth failures | Wait for the backoff period (up to 12 hours) or restart the integration |
| Energy Dashboard shows no history | Statistics not yet injected | Trigger a manual refresh via Developer Tools → Services → `homeassistant.reload_config_entry` |
| Data is 1–2 days stale | Expected behaviour | ESB Networks publishes meter data with a 1–2 day delay |

---

## Changelog

### v1.0.0
Initial release of the standalone `esb_networks_smartmeter` integration, incorporating all features developed in the source fork:

- **Grid export sensors** — 6 sensors tracking electricity exported to the grid for microgen/solar accounts; reports 0 on standard accounts. CSV rows are partitioned by `Read Type` to accurately separate import from export.
- **Latest Reading diagnostic sensor** — shows the timestamp of the most recent row in the ESB CSV, making it easy to see how fresh the data is (distinct from "Last Update" which reflects when the integration last polled).
- **TIMESTAMP sensor fix** — `Last Update` and `Latest Reading` sensors now return timezone-aware `datetime` objects as required by Home Assistant's TIMESTAMP device class validation, resolving "Unavailable" state on both sensors.
- **Current-interval sensors** — `ESB Electricity Usage: Now` and `ESB Electricity Export: Now` expose the most recent 30-minute interval reading from the CSV.
- **Historical statistics injection** — on every successful refresh, 15 days of 30-minute interval data is injected into HA's long-term Recorder statistics, enabling full historical charts in the Energy Dashboard immediately after setup.

---

## License & Credits

Licensed under the [Apache License 2.0](LICENSE).

**Credits:**
- [antoine-voiry](https://github.com/antoine-voiry) — original integration this fork is based on
- [badger707](https://github.com/badger707) — contributions to the upstream project
- [RobinJ1995](https://github.com/RobinJ1995) — contributions to the upstream project
