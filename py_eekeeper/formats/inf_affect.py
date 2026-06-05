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
    resource3: str = ""
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

        opcode, target_type, power = struct.unpack_from("<HBB", data, 0)
        param1, param2 = struct.unpack_from("<II", data, 4)
        timing, dispel = struct.unpack_from("<BB", data, 12)
        duration = struct.unpack_from("<I", data, 14)[0]
        prob1, prob2 = struct.unpack_from("<BB", data, 18)
        resource = data[20:28].decode("latin-1").rstrip("\x00")
        dice_thrown, dice_sides = struct.unpack_from("<II", data, 28)
        save_type, save_bonus = struct.unpack_from("<Ii", data, 36)
        special = struct.unpack_from("<I", data, 44)[0]

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
            return cls(raw_data=data)

        opcode, target_type = struct.unpack_from("<II", data, 8)
        param1, param2 = struct.unpack_from("<ii", data, 20)
        timing = struct.unpack_from("<I", data, 28)[0]
        duration = struct.unpack_from("<i", data, 32)[0]
        prob1, prob2 = struct.unpack_from("<HH", data, 36)
        resource = data[40:48].decode("latin-1").rstrip("\x00")
        resource3 = data[140:148].decode("latin-1").rstrip("\x00")
        dice_sides, dice_thrown = struct.unpack_from("<II", data, 48)
        save_type, save_bonus = struct.unpack_from("<II", data, 56)
        special = struct.unpack_from("<I", data, 84)[0]

        return cls(
            opcode=opcode,
            target_type=target_type,
            parameter1=param1,
            parameter2=param2,
            timing_mode=timing,
            duration=duration,
            probability1=prob1,
            probability2=prob2,
            resource=resource,
            resource3=resource3,
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

        struct.pack_into("<II", result, 8, self.opcode, self.target_type)
        struct.pack_into("<ii", result, 20, self.parameter1, self.parameter2)
        struct.pack_into("<I", result, 28, self.timing_mode)
        struct.pack_into("<i", result, 32, self.duration)
        struct.pack_into("<HH", result, 36, self.probability1, self.probability2)

        res_bytes = self.resource.encode("latin-1")[:8].ljust(8, b"\x00")
        result[40:48] = res_bytes
        res3_bytes = self.resource3.encode("latin-1")[:8].ljust(8, b"\x00")
        result[140:148] = res3_bytes
        struct.pack_into("<II", result, 48, self.dice_sides, self.dice_thrown)
        struct.pack_into("<II", result, 56, self.saving_throw_type, self.saving_throw_bonus)
        struct.pack_into("<I", result, 84, self.special)

        return bytes(result)

    def to_bytes_v1(self) -> bytes:
        if len(self.raw_data) >= AFF_V1_SIZE:
            result = bytearray(self.raw_data[:AFF_V1_SIZE])
        else:
            result = bytearray(AFF_V1_SIZE)

        struct.pack_into("<HBB", result, 0, self.opcode, self.target_type, self.power)
        struct.pack_into("<II", result, 4, self.parameter1, self.parameter2)
        struct.pack_into("<BB", result, 12, self.timing_mode, self.dispel_type)
        struct.pack_into("<I", result, 14, self.duration)
        struct.pack_into("<BB", result, 18, self.probability1, self.probability2)

        res_bytes = self.resource.encode("latin-1")[:8].ljust(8, b"\x00")
        result[20:28] = res_bytes
        struct.pack_into("<II", result, 28, self.dice_thrown, self.dice_sides)
        struct.pack_into("<Ii", result, 36, self.saving_throw_type, self.saving_throw_bonus)
        struct.pack_into("<I", result, 44, self.special)

        return bytes(result)
