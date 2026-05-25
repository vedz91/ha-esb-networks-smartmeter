<p align="center">
  <img src="https://raw.githubusercontent.com/vedz91/ha-esb-networks-smartmeter/main/custom_components/esb_networks_smartmeter/brand/logo.png" alt="ESB Networks Smart Meter" width="200"/>
</p>

# ESB Networks Smart Meter

Monitor your Irish electricity usage directly in Home Assistant.

Connects to your **ESB Networks** account and automatically downloads your smart meter data every 24 hours.

## What You Get

**19 sensors** including:
- Electricity consumption — today, last 24h, this week, last 7 days, this month, last 30 days
- Grid export / microgeneration return — same time periods (reports 0 on standard accounts)
- Current 30-minute interval readings — most recent import and export values
- Diagnostic sensors — last update time, latest reading timestamp, API status, data age, circuit breaker state

## Energy Dashboard Ready

Automatically injects 15 days of 30-minute interval historical data into HA's long-term statistics on every successful refresh, so the Energy Dashboard shows real historical usage immediately after setup — no waiting for data to accumulate.

## Key Features

- Handles ESB's multi-step authentication automatically
- 24-hour smart caching to minimise API calls
- Circuit breaker prevents hammering the API on repeated failures
- 70+ rotating user agents to reduce CAPTCHA triggers
- Manual cookie bypass available if CAPTCHA is encountered
- Works for both standard and microgeneration (solar) accounts

## Requirements

- ESB Networks account at [myaccount.esbnetworks.ie](https://myaccount.esbnetworks.ie)
- 11-digit MPRN (on your electricity bill)
- Home Assistant 2023.1.0 or later
