"""Async VE.Direct client built on serialx. Read-only.

Nothing in this module ever writes to the port. The TEXT protocol is a pure
broadcast — the device emits one block per second unprompted — so listening is
sufficient for monitoring. Writing would mean the HEX protocol, which is out of
scope for now.

serialx notes
-------------
* ``serialx.open_serial_connection()`` gives a plain asyncio
  ``(StreamReader, StreamWriter)`` pair with native async on every platform.
* The URL is passed through opaquely, so the same client works for
  ``/dev/serial/by-id/...`` and for a Home Assistant ESPHome serial proxy
  without this library knowing the difference.
* serialx raises ``OSError`` / ``TimeoutError`` rather than pyserial's catch-all
  ``SerialException``, so error handling below is deliberately granular.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Self

import serialx

from .const import BAUDRATE, FRAME_INTERVAL
from .fields import decode
from .parser import FrameParser, HexFrame, TextFrame

_LOGGER = logging.getLogger(__name__)

_READ_SIZE = 512
# Five missed blocks is generous; the device emits one per second.
_STALL_TIMEOUT = FRAME_INTERVAL * 5


class VEDirectError(Exception):
    """Base error."""


class VEDirectStalled(VEDirectError):
    """Port is open but the device stopped talking."""


@dataclass(slots=True)
class Reading:
    """A decoded TEXT block."""

    values: dict[str, Any] = field(default_factory=dict)

    def __getitem__(self, name: str) -> Any:
        return self.values[name]

    def get(self, name: str, default: Any = None) -> Any:
        return self.values.get(name, default)


class VEDirect:
    """Read a Victron device over VE.Direct.

    ```python
    async with VEDirect("/dev/serial/by-id/usb-VictronEnergy_BV_...") as vedirect:
        async for reading in vedirect.readings():
            print(reading.get("battery_voltage"), reading.get("panel_power"))
    ```
    """

    def __init__(self, url: str, *, baudrate: int = BAUDRATE) -> None:
        self._url = url
        self._baudrate = baudrate
        self._parser = FrameParser()
        self._reader: asyncio.StreamReader | None = None
        # Retained solely as the teardown handle. Never written to.
        self._writer: asyncio.StreamWriter | None = None

    # -- lifecycle ---------------------------------------------------------

    async def connect(self) -> None:
        self._reader, self._writer = await serialx.open_serial_connection(
            self._url, baudrate=self._baudrate
        )
        _LOGGER.debug("Opened %s at %d baud (read-only)", self._url, self._baudrate)

    async def close(self) -> None:
        if self._writer is not None:
            self._writer.close()
            try:
                await self._writer.wait_closed()
            except OSError:
                pass
        self._reader = self._writer = None

    async def __aenter__(self) -> Self:
        await self.connect()
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    # -- reading -----------------------------------------------------------

    async def readings(self) -> AsyncIterator[Reading]:
        """Yield one decoded block per second until the connection drops."""
        if self._reader is None:
            raise VEDirectError("Not connected")

        while True:
            try:
                chunk = await asyncio.wait_for(
                    self._reader.read(_READ_SIZE), timeout=_STALL_TIMEOUT
                )
            except TimeoutError as err:
                raise VEDirectStalled(f"No data for {_STALL_TIMEOUT}s") from err

            if not chunk:
                raise VEDirectStalled("Port closed by peer")

            for frame in self._parser.feed(chunk):
                if isinstance(frame, TextFrame):
                    yield Reading(decode(frame.fields))
                elif isinstance(frame, HexFrame):
                    # We never send HEX, so this should be rare. Handled
                    # anyway: the bytes must stay out of the TEXT checksum or
                    # we would drop the surrounding block.
                    _LOGGER.debug("Ignoring unsolicited HEX frame")

    async def stream(self, *, retry_interval: float = 5.0) -> AsyncIterator[Reading]:
        """As `readings()`, but reconnects forever with a capped backoff.

        Cable unplugged, ESP proxy rebooting, USB re-enumerating — all of these
        are routine on a boat or in a van, not exceptional.
        """
        backoff = retry_interval
        while True:
            try:
                if self._reader is None:
                    await self.connect()
                    backoff = retry_interval
                async for reading in self.readings():
                    yield reading
            except (OSError, VEDirectStalled) as err:
                _LOGGER.debug("Connection lost (%s); retrying in %.0fs", err, backoff)
                await self.close()
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60.0)
