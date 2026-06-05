"""Parser for Infinity Engine journal entries within GAM files."""

import struct
from dataclasses import dataclass

JOURNAL_ENTRY_SIZE = 0x0C


@dataclass
class JournalEntry:
    strref: int = 0
    time: int = 0
    chapter: int = 0
    flags: int = 0
    section_id: int = 0


def parse_journal_data(data: bytes, count: int) -> list[JournalEntry]:
    entries = []
    for i in range(count):
        offset = i * JOURNAL_ENTRY_SIZE
        if offset + JOURNAL_ENTRY_SIZE > len(data):
            break
        strref = struct.unpack_from("<I", data, offset)[0]
        time = struct.unpack_from("<I", data, offset + 4)[0]
        chapter = data[offset + 8]
        flags = data[offset + 9]
        section_id = struct.unpack_from("<H", data, offset + 10)[0]
        entries.append(JournalEntry(
            strref=strref, time=time, chapter=chapter,
            flags=flags, section_id=section_id,
        ))
    return entries


def build_journal_data(entries: list[JournalEntry]) -> bytes:
    result = bytearray()
    for entry in entries:
        result.extend(struct.pack("<I", entry.strref))
        result.extend(struct.pack("<I", entry.time))
        result.append(entry.chapter & 0xFF)
        result.append(entry.flags & 0xFF)
        result.extend(struct.pack("<H", entry.section_id & 0xFFFF))
    return bytes(result)
