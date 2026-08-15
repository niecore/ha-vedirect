"""Push coordinator wrapping the VE.Direct client.

The device broadcasts unsolicited at 1 Hz; there is nothing to poll. A
background task reads frames, merges them (a BMV alternates between two
different blocks, so a single frame never holds the full picture) and pushes
throttled updates into the coordinator. Connection loss flips entities to
unavailable and is retried with capped backoff.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_DEVICE_PATH, CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL, DOMAIN
from .vedirect_x import VEDirect, VEDirectError, product_name

_LOGGER = logging.getLogger(__name__)

_RETRY_INTERVAL = 5.0
_MAX_RETRY_INTERVAL = 60.0

type VEDirectConfigEntry = ConfigEntry[VEDirectCoordinator]


def format_firmware(values: dict[str, Any]) -> str | None:
    """Render FW ("208", "C208") or FWE ("0208FF", "020801") human-readably."""
    if raw := values.get("firmware_version_extended"):
        raw = raw.zfill(6)
        version = f"{int(raw[:2])}.{raw[2:4]}"
        return version if raw[4:6] == "FF" else f"{version}-beta-{raw[4:6]}"
    if raw := values.get("firmware_version"):
        candidate = ""
        if raw and raw[0].isalpha():
            candidate, raw = raw[0], raw[1:]
        if len(raw) >= 3:
            version = f"{int(raw[:-2])}.{raw[-2:]}"
            return f"{version}-rc-{candidate}" if candidate else version
        return raw
    return None


class VEDirectCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Owns the serial connection and read task for one VE.Direct device."""

    config_entry: VEDirectConfigEntry

    def __init__(self, hass: HomeAssistant, entry: VEDirectConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN}:{entry.data[CONF_DEVICE_PATH]}",
            update_interval=None,
        )
        self.client = VEDirect(entry.data[CONF_DEVICE_PATH])
        self._throttle: float = entry.options.get(
            CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
        )
        self._merged: dict[str, Any] = {}
        self._first_frame = asyncio.Event()

    async def async_start(self) -> None:
        """Open the port and start reading; returns after the first frame.

        Raises the underlying OSError/TimeoutError if the port cannot be
        opened or stays silent, so setup can signal ConfigEntryNotReady.
        """
        await self.client.connect()
        self.config_entry.async_create_background_task(
            self.hass, self._read_loop(), name=self.name
        )
        async with asyncio.timeout(15):
            await self._first_frame.wait()

    async def async_stop(self) -> None:
        await self.client.close()

    async def _read_loop(self) -> None:
        backoff = _RETRY_INTERVAL
        last_push = 0.0
        while True:
            try:
                async for reading in self.client.readings():
                    backoff = _RETRY_INTERVAL
                    self._merged.update(reading.values)
                    now = time.monotonic()
                    if not self._first_frame.is_set() or now - last_push >= self._throttle:
                        last_push = now
                        self.async_set_updated_data(dict(self._merged))
                        self._first_frame.set()
            except (OSError, TimeoutError, VEDirectError) as err:
                self.async_set_update_error(UpdateFailed(f"Connection lost: {err}"))
                await self.client.close()
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, _MAX_RETRY_INTERVAL)
                try:
                    await self.client.connect()
                except (OSError, TimeoutError):
                    pass

    @property
    def device_info(self) -> DeviceInfo:
        values = self._merged
        serial = values.get("serial_number")
        model = None
        if pid := values.get("product_id"):
            model = product_name(pid)
        return DeviceInfo(
            identifiers={(DOMAIN, self.config_entry.unique_id or self.config_entry.entry_id)},
            manufacturer="Victron Energy",
            model=model or values.get("model_description"),
            model_id=values.get("product_id"),
            serial_number=serial,
            sw_version=format_firmware(values),
            name=self.config_entry.title,
        )
