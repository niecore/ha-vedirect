# Victron VE.Direct for Home Assistant

A Home Assistant custom integration for Victron Energy devices with a
VE.Direct port: **SmartSolar / BlueSolar MPPT** chargers, **BMV / SmartShunt**
battery monitors, **Phoenix** inverters and chargers, and the **Smart
BuckBoost** DC/DC converter.

Implements the VE.Direct TEXT protocol as specified in
[VE.Direct-Protocol-3.34](https://www.victronenergy.com/upload/documents/VE.Direct-Protocol-3.34.pdf).
Read-only: nothing is ever written to the device.

## Features

- **Local push** — the device broadcasts every second over the serial cable;
  no polling, no cloud.
- **Multiple devices** — each cable is its own config entry with its own
  connection. Two (or ten) VE.Direct USB cables on one Home Assistant work
  independently; uniqueness is enforced on the device serial number
  (`SER#`), with the stable `/dev/serial/by-id/…` path as fallback for BMVs,
  which don't broadcast a serial number.
- **USB discovery** — genuine VE.Direct USB cables (FTDI, `VE Direct cable`)
  are auto-discovered.
- **Dynamic entities** — entities are created for exactly the fields your
  device broadcasts. An MPPT gets solar yield entities, a SmartShunt gets
  battery history, an inverter gets AC output.
- **Robust framing** — a byte-level state machine with checksum verification
  and HEX-frame demultiplexing; survives checksum bytes that masquerade as
  newlines, mid-stream connects, garbage bursts, cable unplug/replug and
  device reboots (automatic reconnect with backoff, entities go unavailable
  meanwhile).
- **Energy dashboard ready** — solar yield and BMV charged/discharged energy
  are `total_increasing` kWh sensors.

## Installation

### HACS (recommended)

1. HACS → Integrations → ⋮ → *Custom repositories* → add this repository as
   type *Integration*.
2. Install **Victron VE.Direct** and restart Home Assistant.

### Manual

Copy `custom_components/vedirect/` into your Home Assistant `config/custom_components/`
directory and restart.

## Configuration

*Settings → Devices & Services → Add Integration → Victron VE.Direct.*

Pick the serial port, or type a path/URL. When more than one cable is
connected, prefer the stable `/dev/serial/by-id/…` paths — `/dev/ttyUSB0`
and `/dev/ttyUSB1` can swap after a reboot (the integration resolves
`by-id` paths automatically when possible). Repeat *Add Integration* once
per cable.

Because the transport is [serialx](https://pypi.org/project/serialx/), the
port can also be a network URL (e.g. an ESPHome/ser2net serial proxy):
`socket://192.168.1.50:6638`.

### Options

- **Update interval** (default 5 s): the device broadcasts at 1 Hz; this
  throttles how often states are written, keeping the recorder database sane.

## Entities

| Device | Examples |
|---|---|
| MPPT charger | battery voltage/current, panel voltage/power, charger state, MPPT mode, yield today/total, max power, error, off reason |
| BMV / SmartShunt | voltage, current, power, state of charge, time to go, consumed Ah, starter/mid-point voltage, alarm, history (H1–H18, mostly disabled by default) |
| Phoenix inverter | AC output voltage/current/apparent power, device mode, state, warning/alarm reason |
| Phoenix charger / BuckBoost | per-output voltage & current, DC input voltage/current/power, state, error |

Identification fields (`PID`, `SER#`, `FW`/`FWE`) populate the device
registry (model, serial number, firmware version) instead of being entities.

## Troubleshooting

- **No data with a VE.Direct-to-RS232 interface**: the isolated side is
  powered from DTR/RTS; both are asserted on open by the serial backend, but
  some USB-RS232 adapters need a moment before the first frame arrives.
- **`cannot_connect` during setup**: check that nothing else (VictronConnect,
  ser2net) holds the port, and that the cable is a data cable.
- Diagnostics (device page → *Download diagnostics*) include the merged
  decoded data and good/bad frame counters.

## Development

The protocol implementation lives in `custom_components/vedirect/vedirect_x/`
as a vendored, Home-Assistant-free library (parser, field registry, async
client). Run its tests with:

```bash
pip install pytest serialx
pytest tests
```
