"""Parser for Infinity Engine BAM (animation/sprite) files."""

import struct
from dataclasses import dataclass


@dataclass
class BamFrame:
    width: int
    height: int
    center_x: int
    center_y: int
    data_offset: int
    is_rle: bool


class InfBam:
    """Decodes BAM sprite files with palette and RLE compression."""

    def __init__(self):
        self._frames: list[BamFrame] = []
        self._palette: list[tuple[int, int, int, int]] = []  # BGRA
        self._data: bytes = b""
        self._transparent_index: int = 0

    def read(self, data: bytes) -> bool:
        if len(data) < 24:
            return False

        sig = data[0:4]
        if sig != b"BAM ":
            return False
        if data[4:8] != b"V1  ":
            return False

        frame_count, cycle_count, transparent_index = struct.unpack_from(
            "<HBB", data, 8
        )
        frames_offset = struct.unpack_from("<I", data, 12)[0]
        palette_offset = struct.unpack_from("<I", data, 16)[0]
        lookup_table_offset = struct.unpack_from("<I", data, 20)[0]
        if frames_offset + frame_count * 12 > len(data):
            return False
        if palette_offset + 256 * 4 > len(data):
            return False
        if lookup_table_offset > len(data):
            return False

        self._transparent_index = transparent_index
        self._data = data

        # Read palette (256 entries, 4 bytes each BGRA).
        self._palette = []
        for i in range(256):
            off = palette_offset + i * 4
            b, g, r, a = struct.unpack_from("<BBBB", data, off)
            self._palette.append((r, g, b, a))

        # Read frames
        self._frames = []
        for i in range(frame_count):
            off = frames_offset + i * 12
            if off + 12 > len(data):
                break
            w, h, cx, cy, frame_data_offset = struct.unpack_from("<HHhhI", data, off)
            is_rle = not bool(frame_data_offset & 0x80000000)
            data_offset = frame_data_offset & 0x7FFFFFFF
            if data_offset > len(data):
                return False

            self._frames.append(BamFrame(
                width=w, height=h,
                center_x=cx, center_y=cy,
                data_offset=data_offset,
                is_rle=is_rle,
            ))

        return True

    def get_frame_count(self) -> int:
        return len(self._frames)

    def get_frame_dimensions(self, frame_idx: int) -> tuple[int, int]:
        if 0 <= frame_idx < len(self._frames):
            f = self._frames[frame_idx]
            return (f.width, f.height)
        return (0, 0)

    def get_frame_pixels(self, frame_idx: int) -> list[tuple[int, int, int, int]] | None:
        """Returns RGBA pixel data for a frame."""
        if frame_idx < 0 or frame_idx >= len(self._frames):
            return None

        frame = self._frames[frame_idx]
        if frame.width == 0 or frame.height == 0:
            return None

        pixel_count = frame.width * frame.height
        pixels: list[tuple[int, int, int, int]] = []

        if frame.is_rle:
            offset = frame.data_offset
            while len(pixels) < pixel_count and offset < len(self._data):
                byte = self._data[offset]
                offset += 1
                if byte == self._transparent_index:
                    # Check if next byte is a count
                    if offset < len(self._data):
                        count = self._data[offset] + 1
                        offset += 1
                        pixels.extend([(0, 0, 0, 0)] * count)
                    else:
                        pixels.append((0, 0, 0, 0))
                else:
                    r, g, b, a = self._palette[byte]
                    pixels.append((r, g, b, a))
        else:
            offset = frame.data_offset
            for _ in range(pixel_count):
                if offset >= len(self._data):
                    pixels.append((0, 0, 0, 0))
                    continue
                idx = self._data[offset]
                offset += 1
                if idx == self._transparent_index:
                    pixels.append((0, 0, 0, 0))
                else:
                    r, g, b, a = self._palette[idx]
                    pixels.append((r, g, b, a))

        return pixels[:pixel_count]

    @property
    def palette(self) -> list[tuple[int, int, int, int]]:
        return self._palette
