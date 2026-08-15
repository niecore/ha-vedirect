"""Parser tests: framing, checksum, HEX demux, resynchronisation."""

from vedirect_x.parser import FrameParser, HexFrame, TextFrame


def make_block(fields: dict[str, str]) -> bytes:
    """Build a wire-format block with a correct checksum byte."""
    body = b""
    for label, value in fields.items():
        body += b"\r\n" + label.encode() + b"\t" + value.encode()
    body += b"\r\nChecksum\t"
    checksum = (256 - sum(body)) & 0xFF
    return body + bytes([checksum])


MPPT_FIELDS = {
    "PID": "0xA053",
    "FW": "159",
    "SER#": "HQ2132XXXXX",
    "V": "13790",
    "I": "500",
    "VPV": "18650",
    "PPV": "7",
    "CS": "3",
    "MPPT": "2",
    "ERR": "0",
    "H19": "1234",
    "H20": "5",
    "H21": "36",
    "H22": "8",
    "H23": "52",
    "HSDS": "12",
}


def test_valid_block() -> None:
    parser = FrameParser()
    frames = list(parser.feed(make_block(MPPT_FIELDS)))
    assert len(frames) == 1
    assert isinstance(frames[0], TextFrame)
    assert frames[0].fields == MPPT_FIELDS
    assert parser.frames_ok == 1
    assert parser.frames_bad == 0


def test_byte_at_a_time() -> None:
    parser = FrameParser()
    frames = []
    for byte in make_block(MPPT_FIELDS):
        frames.extend(parser.feed(bytes([byte])))
    assert len(frames) == 1
    assert frames[0].fields == MPPT_FIELDS


def _block_with_checksum(target: int) -> bytes:
    """Pad the serial field until the checksum byte equals `target`."""
    from itertools import product

    printable = [chr(code) for code in range(33, 127)]
    for length in range(4):
        for pad in product(printable, repeat=length):
            block = make_block({**MPPT_FIELDS, "SER#": "HQ" + "".join(pad)})
            if block[-1] == target:
                return block
    raise AssertionError(f"no padding yields checksum {target:#x}")


def test_checksum_byte_that_looks_like_newline() -> None:
    """A checksum landing on \\n, \\r or \\t must not confuse the framing."""
    for target in (0x0A, 0x0D, 0x09):
        block = _block_with_checksum(target)
        parser = FrameParser()
        frames = list(parser.feed(block * 3))
        assert len(frames) == 3
        assert all(isinstance(frame, TextFrame) for frame in frames)
        assert parser.frames_bad == 0


def test_corrupted_block_dropped_then_resync() -> None:
    good = make_block(MPPT_FIELDS)
    corrupted = good[:20] + bytes([good[20] ^ 0xFF]) + good[21:]
    parser = FrameParser()
    frames = list(parser.feed(corrupted + good))
    assert len(frames) == 1
    assert parser.frames_bad == 1
    assert parser.frames_ok == 1


def test_start_mid_stream() -> None:
    """Opening the port mid-block loses at most that one block."""
    good = make_block(MPPT_FIELDS)
    parser = FrameParser()
    frames = list(parser.feed(good[13:] + good + good))
    assert len(frames) >= 2
    assert all(frame.fields == MPPT_FIELDS for frame in frames[-2:])


def test_hex_frame_interleaved() -> None:
    """A HEX frame between blocks is demuxed and excluded from the checksum."""
    good = make_block(MPPT_FIELDS)
    hex_frame = b":A0102000543\n"
    parser = FrameParser()
    frames = list(parser.feed(good + hex_frame + good))
    assert [type(frame) for frame in frames] == [TextFrame, HexFrame, TextFrame]
    assert frames[1].payload == b"A0102000543"
    assert parser.frames_bad == 0


def test_checksum_label_case_insensitive() -> None:
    body = b"\r\nV\t12000\r\nCHECKSUM\t"
    block = body + bytes([(256 - sum(body)) & 0xFF])
    parser = FrameParser()
    frames = list(parser.feed(block))
    assert len(frames) == 1
    assert frames[0].fields == {"V": "12000"}


def test_garbage_resync() -> None:
    parser = FrameParser()
    garbage = bytes(range(256)) * 4
    list(parser.feed(garbage))
    frames = list(parser.feed(make_block(MPPT_FIELDS) * 2))
    assert any(
        frame.fields == MPPT_FIELDS
        for frame in frames
        if isinstance(frame, TextFrame)
    )
