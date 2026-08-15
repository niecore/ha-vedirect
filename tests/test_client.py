"""End-to-end client test with a synthetic byte stream, no hardware."""

import asyncio

import pytest

from vedirect_x import VEDirect, VEDirectStalled
from test_parser import MPPT_FIELDS, make_block


def test_readings_end_to_end() -> None:
    async def run() -> list:
        client = VEDirect("loop://")
        reader = asyncio.StreamReader()
        reader.feed_data(make_block(MPPT_FIELDS) * 2 + b":A0102000543\n")
        reader.feed_eof()
        client._reader = reader  # noqa: SLF001
        readings = []
        with pytest.raises(VEDirectStalled):
            async for reading in client.readings():
                readings.append(reading)
        return readings

    readings = asyncio.run(run())
    assert len(readings) == 2
    first = readings[0]
    assert first.get("battery_voltage") == 13.79
    assert first.get("panel_power") == 7
    assert first.get("serial_number") == "HQ2132XXXXX"
    assert first["charger_state"].name == "BULK"
    assert first.get("yield_total") == 12.34
