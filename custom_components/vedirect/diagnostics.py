"""Diagnostics support for Victron VE.Direct."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.redact import async_redact_data

from .coordinator import VEDirectConfigEntry

TO_REDACT = {"serial_number"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: VEDirectConfigEntry
) -> dict[str, Any]:
    """Return diagnostics: last merged data plus parser frame counters."""
    coordinator = entry.runtime_data
    parser = coordinator.client._parser  # noqa: SLF001
    return {
        "entry": {
            "title": entry.title,
            "options": dict(entry.options),
        },
        "data": async_redact_data(
            {key: str(value) for key, value in (coordinator.data or {}).items()},
            TO_REDACT,
        ),
        "frames_ok": parser.frames_ok,
        "frames_bad": parser.frames_bad,
        "last_update_success": coordinator.last_update_success,
    }
