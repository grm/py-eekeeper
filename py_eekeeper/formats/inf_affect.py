"""Infinity Engine affect/effect structure."""

import struct
from dataclasses import dataclass, field


AFF_V1_SIZE = 48
AFF_V2_SIZE = 264


@dataclass
class InfAffect:
    opcode: int = 0
    target_type: int = 0
    power: int = 0
    parameter1: int = 0
    parameter2: int = 0
    timing_mode: int = 0
    dispel_type: int = 0
    duration: int = 0
    probability1: int = 0
    probability2: int = 0
    resource: str = ""
    dice_thrown: int = 0
    dice_sides: int = 0
    saving_throw_type: int = 0
    saving_throw_bonus: int = 0
    special: int = 0
    raw_data: bytes = field(default_factory=bytes, repr=False)

    @classmethod
    def from_bytes_v1(cls, data: bytes) -> "InfAffect":
        if len(data) < AFF_V1_SIZE:
            return cls(raw_data=data)

        (
            opcode, target_type, power,
            param1, param2,
            timing, dispel, duration,
            prob1, prob2,
        ) = struct.unpack_from("<HBBIIBBIBB", data, 0)

        resource = data[14:22].decode("latin-1").rstrip("\x00")
        dice_thrown, dice_sides = struct.unpack_from("<II", data, 22)
        save_type, save_bonus = struct.unpack_from("<Ii", data, 30)
        special = struct.unpack_from("<I", data, 38)[0]

        return cls(
            opcode=opcode,
            target_type=target_type,
            power=power,
            parameter1=param1,
            parameter2=param2,
            timing_mode=timing,
            dispel_type=dispel,
            duration=duration,
            probability1=prob1,
            probability2=prob2,
            resource=resource,
            dice_thrown=dice_thrown,
            dice_sides=dice_sides,
            saving_throw_type=save_type,
            saving_throw_bonus=save_bonus,
            special=special,
            raw_data=data[:AFF_V1_SIZE],
        )

    @classmethod
    def from_bytes_v2(cls, data: bytes) -> "InfAffect":
        if len(data) < AFF_V2_SIZE:
            return cls.from_bytes_v1(data) if len(data) >= AFF_V1_SIZE else cls(raw_data=data)

        (
            opcode, target_type, power,
            param1, param2,
            timing, duration,
        ) = struct.unpack_from("<IBBIIHI", data, 0)

        resource = data[16:24].decode("latin-1").rstrip("\x00")
        dice_thrown, dice_sides = struct.unpack_from("<II", data, 24)
        save_type, save_bonus = struct.unpack_from("<Ii", data, 32)
        special = struct.unpack_from("<I", data, 40)[0]

        return cls(
            opcode=opcode,
            target_type=target_type,
            power=power,
            parameter1=param1,
            parameter2=param2,
            timing_mode=timing,
            duration=duration,
            resource=resource,
            dice_thrown=dice_thrown,
            dice_sides=dice_sides,
            saving_throw_type=save_type,
            saving_throw_bonus=save_bonus,
            special=special,
            raw_data=data[:AFF_V2_SIZE],
        )

    def to_bytes_v2(self) -> bytes:
        if len(self.raw_data) >= AFF_V2_SIZE:
            result = bytearray(self.raw_data[:AFF_V2_SIZE])
        else:
            result = bytearray(AFF_V2_SIZE)

        struct.pack_into("<IBBIIHi", result, 0,
                         self.opcode, self.target_type, self.power,
                         self.parameter1, self.parameter2,
                         self.timing_mode, self.duration)

        res_bytes = self.resource.encode("latin-1")[:8].ljust(8, b"\x00")
        result[16:24] = res_bytes
        struct.pack_into("<II", result, 24, self.dice_thrown, self.dice_sides)
        struct.pack_into("<Ii", result, 32, self.saving_throw_type, self.saving_throw_bonus)
        struct.pack_into("<I", result, 40, self.special)

        return bytes(result)

    def to_bytes_v1(self) -> bytes:
        if len(self.raw_data) >= AFF_V1_SIZE:
            result = bytearray(self.raw_data[:AFF_V1_SIZE])
        else:
            result = bytearray(AFF_V1_SIZE)

        struct.pack_into("<HBB", result, 0, self.opcode, self.target_type, self.power)
        struct.pack_into("<II", result, 4, self.parameter1, self.parameter2)
        struct.pack_into("<BBI", result, 12, self.timing_mode, self.dispel_type, self.duration)
        result[12] = self.probability1
        result[13] = self.probability2

        res_bytes = self.resource.encode("latin-1")[:8].ljust(8, b"\x00")
        result[14:22] = res_bytes
        struct.pack_into("<II", result, 22, self.dice_thrown, self.dice_sides)
        struct.pack_into("<Ii", result, 30, self.saving_throw_type, self.saving_throw_bonus)
        struct.pack_into("<I", result, 38, self.special)

        return bytes(result)
