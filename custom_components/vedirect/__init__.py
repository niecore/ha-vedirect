"""The Victron VE.Direct integration.

Each config entry owns exactly one serial port and one coordinator, so any
number of VE.Direct cables can be attached in parallel — every device is a
separate entry with its own connection, entities and options.
"""

from __future__ import annotations

import logging

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import CONF_DEVICE_PATH
from .coordinator import VEDirectConfigEntry, VEDirectCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: VEDirectConfigEntry) -> bool:
    """Set up a VE.Direct device from a config entry."""
    coordinator = VEDirectCoordinator(hass, entry)
    try:
        await coordinator.async_start()
    except (OSError, TimeoutError) as err:
        await coordinator.async_stop()
        raise ConfigEntryNotReady(
            f"No VE.Direct data on {entry.data[CONF_DEVICE_PATH]}: {err}"
        ) from err

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: VEDirectConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await entry.runtime_data.async_stop()
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: VEDirectConfigEntry) -> None:
    """Reload the entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
