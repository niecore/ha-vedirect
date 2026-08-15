"""Async, read-only client library for the Victron VE.Direct TEXT protocol.

Implements VE.Direct protocol 3.34. Vendored inside the Home Assistant
integration until published on PyPI; contains no Home Assistant imports.
"""

from .client import Reading, VEDirect, VEDirectError, VEDirectStalled
from .const import (
    BAUDRATE,
    FRAME_INTERVAL,
    PRODUCT_IDS,
    AlarmReason,
    ChargerError,
    ChargerState,
    DeviceMode,
    MonitorMode,
    OffReason,
    TrackerMode,
    product_name,
)
from .fields import FIELDS, Field, decode
from .parser import FrameParser, HexFrame, TextFrame

__all__ = [
    "BAUDRATE",
    "FIELDS",
    "FRAME_INTERVAL",
    "PRODUCT_IDS",
    "AlarmReason",
    "ChargerError",
    "ChargerState",
    "DeviceMode",
    "Field",
    "FrameParser",
    "HexFrame",
    "MonitorMode",
    "OffReason",
    "Reading",
    "TextFrame",
    "TrackerMode",
    "VEDirect",
    "VEDirectError",
    "VEDirectStalled",
    "decode",
    "product_name",
]
