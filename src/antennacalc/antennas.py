"""Antenna presets: typical gain (dBi) and whether ground reflection applies by default."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Antenna:
    name: str
    gain_dbi: float
    ground: bool


ANTENNAS: list[Antenna] = [
    Antenna("Dipole (horizontal, low)", 2.15, True),
    Antenna("Inverted-V", 2.15, True),
    Antenna("Vertical (1/4 wave)", 2.15, True),
    Antenna("Multiband vertical (about 10 m / 33 ft, DX Commander style)", 3.0, True),
    Antenna("Loaded / short HF vertical", 0.0, True),
    Antenna("End-fed wire", 2.15, True),
    Antenna("Loop (full wave)", 3.5, True),
    Antenna("J-pole / VHF-UHF vertical", 2.15, True),
    Antenna("VHF/UHF collinear vertical (5/8 wave or more)", 6.0, True),
    Antenna("Handheld / rubber duck", 0.0, True),
    Antenna("Mobile whip", 0.0, True),
    Antenna("HF Yagi, 2 element", 6.5, False),
    Antenna("HF Yagi, 3 element", 8.5, False),
    Antenna("HF Yagi, 4 element", 10.0, False),
    Antenna("HF Yagi, 5 element", 11.0, False),
    Antenna("HF Yagi, 6 element", 12.0, False),
    Antenna("VHF/UHF Yagi, 3 element", 7.5, False),
    Antenna("VHF/UHF Yagi, 5 element", 10.0, False),
    Antenna("VHF/UHF Yagi, 7 element", 12.0, False),
    Antenna("VHF/UHF Yagi, 9 element", 13.5, False),
    Antenna("VHF/UHF Yagi, 11 element", 14.5, False),
    Antenna("VHF/UHF Yagi, 13 element", 15.5, False),
    Antenna("VHF/UHF Yagi, 15+ element", 17.0, False),
    Antenna("Quad (2 el)", 7.0, False),
    Antenna("Quad (3 el)", 8.5, False),
    Antenna("Satellite / dish / high-gain directional", 15.0, False),
    Antenna("Custom", 0.0, True),
]


def by_name(name: str) -> Antenna:
    for a in ANTENNAS:
        if a.name == name:
            return a
    raise KeyError(name)
