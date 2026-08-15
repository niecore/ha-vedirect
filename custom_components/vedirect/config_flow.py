"""Config flow for the Victron VE.Direct integration.

Multiple entries are explicitly supported — one per cable. Uniqueness is
enforced on the device serial number (`SER#`) when the device broadcasts one
(MPPT, Phoenix, BuckBoost), falling back to the stable
``/dev/serial/by-id/...`` path for devices that do not (BMV battery
monitors). The same port can never be claimed by two entries.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

try:
    from homeassistant.helpers.service_info.usb import UsbServiceInfo
except ImportError:  # HA < 2024.12
    from homeassistant.components.usb import UsbServiceInfo  # type: ignore[no-redef]

from homeassistant.components import usb

from .const import (
    CONF_DEVICE_PATH,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    MAX_UPDATE_INTERVAL,
    MIN_UPDATE_INTERVAL,
    PROBE_TIMEOUT,
)
from .coordinator import VEDirectConfigEntry
from .vedirect_x import VEDirect, product_name

_LOGGER = logging.getLogger(__name__)


class CannotConnect(Exception):
    """No valid VE.Direct frame could be read from the port."""


async def probe(device_path: str) -> dict[str, Any]:
    """Open the port and merge decoded frames until identification is seen."""
    values: dict[str, Any] = {}
    frames = 0
    try:
        async with VEDirect(device_path) as client, asyncio.timeout(PROBE_TIMEOUT):
            async for reading in client.readings():
                values.update(reading.values)
                frames += 1
                # Stop once identified; devices without SER# (BMV) alternate
                # between two blocks, so four frames covers the full field set.
                if ("product_id" in values and "serial_number" in values) or frames >= 4:
                    break
    except TimeoutError:
        # Timeout with at least one valid frame just means the device does
        # not broadcast SER#/PID (e.g. BMV); that is still a success.
        if not values:
            raise CannotConnect("No valid VE.Direct frames received") from None
    except OSError as err:
        raise CannotConnect(str(err)) from err
    return values


def _list_ports() -> list[str]:
    """Enumerate serial ports, blocking; run in executor."""
    from serial.tools import list_ports

    return [port.device for port in list_ports.comports(include_links=True)]


class VEDirectConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle config flows for VE.Direct devices."""

    VERSION = 1

    def __init__(self) -> None:
        self._device_path: str | None = None

    @staticmethod
    @callback
    def async_get_options_flow(entry: VEDirectConfigEntry) -> VEDirectOptionsFlow:
        return VEDirectOptionsFlow()

    async def _async_probe_and_create(self, device_path: str) -> ConfigFlowResult:
        """Validate the port, set the unique id and create the entry."""
        device_path = await self.hass.async_add_executor_job(
            usb.get_serial_by_id, device_path
        )
        self._async_abort_entries_match({CONF_DEVICE_PATH: device_path})

        values = await probe(device_path)

        unique_id = values.get("serial_number") or device_path
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured(updates={CONF_DEVICE_PATH: device_path})

        title = "VE.Direct device"
        if pid := values.get("product_id"):
            title = product_name(pid) or title
        elif model := values.get("model_description"):
            title = f"BMV-{model}"
        return self.async_create_entry(
            title=title, data={CONF_DEVICE_PATH: device_path}
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Let the user pick a serial port or type a path/URL."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                return await self._async_probe_and_create(
                    user_input[CONF_DEVICE_PATH]
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"

        ports = await self.hass.async_add_executor_job(_list_ports)
        schema = vol.Schema(
            {
                vol.Required(CONF_DEVICE_PATH): SelectSelector(
                    SelectSelectorConfig(
                        options=ports,
                        custom_value=True,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                )
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )

    async def async_step_usb(self, discovery_info: UsbServiceInfo) -> ConfigFlowResult:
        """Handle a discovered VE.Direct USB cable."""
        device_path = await self.hass.async_add_executor_job(
            usb.get_serial_by_id, discovery_info.device
        )
        self._async_abort_entries_match({CONF_DEVICE_PATH: device_path})
        self._device_path = device_path
        self.context["title_placeholders"] = {"device": device_path}
        return await self.async_step_usb_confirm()

    async def async_step_usb_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm adding the discovered cable."""
        assert self._device_path is not None
        if user_input is not None:
            try:
                return await self._async_probe_and_create(self._device_path)
            except CannotConnect:
                return self.async_abort(reason="cannot_connect")
        return self.async_show_form(
            step_id="usb_confirm",
            description_placeholders={"device": self._device_path},
        )


class VEDirectOptionsFlow(OptionsFlow):
    """Options: how often pushed readings become state updates."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_UPDATE_INTERVAL,
                    default=self.config_entry.options.get(
                        CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
                    ),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=MIN_UPDATE_INTERVAL,
                        max=MAX_UPDATE_INTERVAL,
                        step=1,
                        unit_of_measurement="s",
                        mode=NumberSelectorMode.SLIDER,
                    )
                )
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
