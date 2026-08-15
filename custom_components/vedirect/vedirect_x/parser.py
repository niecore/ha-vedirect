"""Byte-level frame assembly for VE.Direct.

Why a byte state machine and not `readline()`
---------------------------------------------
The TEXT protocol looks line-oriented::

    \\r\\nPID\\t0xA053
    \\r\\nV\\t12432
    \\r\\nChecksum\\t<byte>

but the checksum is a *raw byte* chosen so the block sums to zero mod 256. That
byte is frequently 0x0A, 0x0D or 0x09 — i.e. it will happily masquerade as a
newline or a tab. Any parser built on `readline()` will silently corrupt a few
percent of frames and then drift. So: feed bytes, track state.

HEX frames (`:` ... `\\n`) can be interleaved *between* TEXT records at any
point and are explicitly excluded from the TEXT checksum. This mirrors Victron's
reference framehandler, which enters a HEX state on any `:` outside the checksum
state and stops accumulating the checksum while there.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from dataclasses import dataclass, field
from enum import Enum, auto

_LOGGER = logging.getLogger(__name__)

_CR = 0x0D
_LF = 0x0A
_TAB = 0x09
_COLON = 0x3A

# Compared case-insensitively. Victron's reference framehandler uppercases
# every byte before parsing, so it can only ever match `CHECKSUM`; devices in
# practice send `Checksum`. Case-folding just this comparison keeps us
# compatible with both without mangling values or mixed-case labels like
# `Relay`, which must stay verbatim for the field registry to find them.
_CHECKSUM_LABEL = b"checksum"

# Guard rails against a stuck line feeding us garbage forever.
_MAX_LABEL_LEN = 32
_MAX_VALUE_LEN = 64
_MAX_FIELDS = 64


@dataclass(slots=True)
class TextFrame:
    """One complete, checksum-verified block of label/value pairs."""

    fields: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class HexFrame:
    """One raw HEX-protocol frame, colon and newline stripped."""

    payload: bytes


class _State(Enum):
    IDLE = auto()
    LABEL = auto()
    VALUE = auto()
    CHECKSUM = auto()
    HEX = auto()


class FrameParser:
    """Incremental parser. Push bytes in, get frames out."""

    def __init__(self) -> None:
        self._state = _State.IDLE
        self._checksum = 0
        self._label = bytearray()
        self._value = bytearray()
        self._hex = bytearray()
        self._fields: dict[str, str] = {}
        self.frames_ok = 0
        self.frames_bad = 0

    def feed(self, data: bytes) -> Iterator[TextFrame | HexFrame]:
        """Consume a chunk of bytes, yielding whatever frames it completed."""
        for byte in data:
            frame = self._feed_byte(byte)
            if frame is not None:
                yield frame

    def _abort(self) -> None:
        """Discard the partial block. The device resends every second anyway."""
        self._state = _State.IDLE
        self._checksum = 0
        self._label.clear()
        self._value.clear()
        self._fields.clear()

    def _feed_byte(self, byte: int) -> TextFrame | HexFrame | None:
        if self._state is _State.HEX:
            if byte == _LF:
                payload = bytes(self._hex)
                self._hex.clear()
                self._state = _State.IDLE
                return HexFrame(payload)
            if byte != _CR:
                self._hex.append(byte)
            return None

        # A colon starts a HEX frame — unless we are in CHECKSUM, where the
        # byte is opaque data and 0x3A is a perfectly legal checksum value.
        if byte == _COLON and self._state is not _State.CHECKSUM:
            self._hex.clear()
            self._state = _State.HEX
            return None

        # Every TEXT byte counts toward the running checksum, including the
        # \r\n separators and the label/value delimiters.
        self._checksum = (self._checksum + byte) & 0xFF

        match self._state:
            case _State.IDLE:
                if byte == _LF:
                    self._label.clear()
                    self._state = _State.LABEL
                # \r and stray bytes: stay idle, keep summing.

            case _State.LABEL:
                if byte == _TAB:
                    if self._label.lower() == _CHECKSUM_LABEL:
                        self._state = _State.CHECKSUM
                    else:
                        self._value.clear()
                        self._state = _State.VALUE
                elif len(self._label) >= _MAX_LABEL_LEN:
                    _LOGGER.debug("Oversized label, resynchronising")
                    self._abort()
                else:
                    self._label.append(byte)

            case _State.VALUE:
                if byte == _CR:
                    self._store_field()
                    self._state = _State.IDLE
                elif len(self._value) >= _MAX_VALUE_LEN:
                    _LOGGER.debug("Oversized value, resynchronising")
                    self._abort()
                else:
                    self._value.append(byte)

            case _State.CHECKSUM:
                # This byte was already folded into the sum above.
                valid = self._checksum == 0
                fields = self._fields
                self._checksum = 0
                self._fields = {}
                self._state = _State.IDLE
                if not valid:
                    self.frames_bad += 1
                    _LOGGER.debug("Checksum mismatch, dropping frame")
                    return None
                self.frames_ok += 1
                return TextFrame(fields)

        return None

    def _store_field(self) -> None:
        if len(self._fields) >= _MAX_FIELDS:
            self._abort()
            return
        try:
            label = self._label.decode("ascii")
            value = self._value.decode("ascii")
        except UnicodeDecodeError:
            _LOGGER.debug("Non-ASCII record, resynchronising")
            self._abort()
            return
        self._fields[label] = value
