"""Constants for the Victron VE.Direct integration."""

from __future__ import annotations

DOMAIN = "vedirect"

CONF_DEVICE_PATH = "device_path"
CONF_UPDATE_INTERVAL = "update_interval"

#: Seconds between pushed state updates. The device broadcasts at 1 Hz; the
#: default throttles that to keep the recorder database sane. Configurable
#: per entry via the options flow.
DEFAULT_UPDATE_INTERVAL = 5
MIN_UPDATE_INTERVAL = 1
MAX_UPDATE_INTERVAL = 60

#: How long the config flow waits for a first valid frame when probing a port.
#: A BMV alternates between two blocks, so allow a few broadcast cycles.
PROBE_TIMEOUT = 12.0
