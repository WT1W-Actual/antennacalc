"""Amateur radio band tables, one per region, and the Band type."""

from __future__ import annotations

from dataclasses import dataclass


def _range(low: float, high: float) -> str:
    if low >= 1000:
        return f"{low / 1000:g}-{high / 1000:g} GHz"
    return f"{low:g}-{high:g} MHz"


@dataclass(frozen=True)
class Band:
    name: str
    segments: tuple[tuple[float, float], ...]

    def __post_init__(self) -> None:
        if not self.segments:
            raise ValueError(f"{self.name}: a band needs at least one segment")
        prev = None
        for low, high in self.segments:
            if not low < high:
                raise ValueError(f"{self.name}: segment {low}-{high} is empty or reversed")
            if prev is not None and low <= prev:
                raise ValueError(f"{self.name}: segments overlap or are out of order")
            prev = high

    @property
    def low_mhz(self) -> float:
        return self.segments[0][0]

    @property
    def high_mhz(self) -> float:
        return self.segments[-1][1]

    @property
    def range_text(self) -> str:
        return ", ".join(_range(low, high) for low, high in self.segments)

    @property
    def label(self) -> str:
        return f"{self.name} ({self.range_text})"


def band(name: str, low: float, high: float) -> Band:
    return Band(name, ((float(low), float(high)),))


def seg(name: str, *segments: tuple[float, float]) -> Band:
    return Band(name, tuple((float(lo), float(hi)) for lo, hi in segments))


def find(table: tuple[Band, ...], name: str) -> Band:
    for b in table:
        if b.name == name:
            return b
    raise KeyError(name)


# 47 CFR 97.301 (eCFR current text). 13 cm is two segments; 3.3-3.5 GHz is
# no longer an amateur band in the US.
US_BANDS: tuple[Band, ...] = (
    band("630 m", 0.472, 0.479),
    band("160 m", 1.8, 2.0),
    band("80 m", 3.5, 4.0),
    band("60 m", 5.3305, 5.4035),
    band("40 m", 7.0, 7.3),
    band("30 m", 10.1, 10.15),
    band("20 m", 14.0, 14.35),
    band("17 m", 18.068, 18.168),
    band("15 m", 21.0, 21.45),
    band("12 m", 24.89, 24.99),
    band("10 m", 28.0, 29.7),
    band("6 m", 50.0, 54.0),
    band("2 m", 144.0, 148.0),
    band("1.25 m", 222.0, 225.0),
    band("70 cm", 420.0, 450.0),
    band("33 cm", 902.0, 928.0),
    band("23 cm", 1240.0, 1300.0),
    seg("13 cm", (2300.0, 2310.0), (2390.0, 2450.0)),
    band("5 cm", 5650.0, 5925.0),
    band("3 cm", 10000.0, 10500.0),
    band("1.2 cm", 24000.0, 24250.0),
    band("6 mm", 47000.0, 47200.0),
    band("4 mm", 76000.0, 81000.0),
)

# ISED RBR-4 Issue 3 (July 2022), Schedule I.
CA_BANDS: tuple[Band, ...] = (
    band("2200 m", 0.1357, 0.1378),
    band("630 m", 0.472, 0.479),
    band("160 m", 1.8, 2.0),
    band("80 m", 3.5, 4.0),
    seg("60 m", (5.3306, 5.3334), (5.3466, 5.3494), (5.3515, 5.3665),
        (5.3716, 5.3744), (5.4036, 5.4064)),
    band("40 m", 7.0, 7.3),
    band("30 m", 10.1, 10.15),
    band("20 m", 14.0, 14.35),
    band("17 m", 18.068, 18.168),
    band("15 m", 21.0, 21.45),
    band("12 m", 24.89, 24.99),
    band("10 m", 28.0, 29.7),
    band("6 m", 50.0, 54.0),
    band("2 m", 144.0, 148.0),
    seg("1.25 m", (219.0, 220.0), (222.0, 225.0)),
    band("70 cm", 430.0, 450.0),
    band("33 cm", 902.0, 928.0),
    band("23 cm", 1240.0, 1300.0),
    band("13 cm", 2300.0, 2450.0),
    band("9 cm", 3300.0, 3500.0),
    band("5 cm", 5650.0, 5925.0),
    band("3 cm", 10000.0, 10500.0),
    band("1.2 cm", 24000.0, 24250.0),
    band("6 mm", 47000.0, 47200.0),
    band("4 mm", 76000.0, 81500.0),
    band("2.5 mm", 122250.0, 123000.0),
    band("2 mm", 134000.0, 141000.0),
    band("1.2 mm", 241000.0, 250000.0),
)

# Radiocommunications (Amateur Stations) Class Licence 2023, Schedule 2 Table C (Advanced).
AU_BANDS: tuple[Band, ...] = (
    band("2200 m", 0.1357, 0.1378),
    band("630 m", 0.472, 0.479),
    band("160 m", 1.8, 1.875),
    seg("80 m", (3.5, 3.7), (3.776, 3.8)),
    band("40 m", 7.0, 7.3),
    band("30 m", 10.1, 10.15),
    band("20 m", 14.0, 14.35),
    band("17 m", 18.068, 18.168),
    band("15 m", 21.0, 21.45),
    band("12 m", 24.89, 24.99),
    band("10 m", 28.0, 29.7),
    band("6 m", 50.0, 54.0),
    band("2 m", 144.0, 148.0),
    band("70 cm", 430.0, 450.0),
    band("23 cm", 1240.0, 1300.0),
    seg("13 cm", (2300.0, 2302.0), (2400.0, 2450.0)),
    band("9 cm", 3300.0, 3600.0),
    band("5 cm", 5650.0, 5850.0),
    band("3 cm", 10000.0, 10500.0),
    band("1.2 cm", 24000.0, 24250.0),
    band("6 mm", 47000.0, 47200.0),
    band("4 mm", 76000.0, 81000.0),
    band("2.5 mm", 122250.0, 123000.0),
    band("2 mm", 134000.0, 141000.0),
    band("1.2 mm", 241000.0, 250000.0),
)

# CEPT European Common Allocation table (ERC Report 25), harmonised edges.
CEPT_BANDS: tuple[Band, ...] = (
    band("2200 m", 0.1357, 0.1378),
    band("630 m", 0.472, 0.479),
    band("160 m", 1.81, 1.85),
    band("80 m", 3.5, 3.8),
    band("60 m", 5.3515, 5.3665),
    band("40 m", 7.0, 7.2),
    band("30 m", 10.1, 10.15),
    band("20 m", 14.0, 14.35),
    band("17 m", 18.068, 18.168),
    band("15 m", 21.0, 21.45),
    band("12 m", 24.89, 24.99),
    band("10 m", 28.0, 29.7),
    band("6 m", 50.0, 52.0),
    band("4 m", 69.9, 70.5),
    band("2 m", 144.0, 146.0),
    band("70 cm", 430.0, 440.0),
    band("23 cm", 1240.0, 1300.0),
    band("13 cm", 2300.0, 2450.0),
    band("9 cm", 3400.0, 3410.0),
    band("5 cm", 5650.0, 5850.0),
    band("3 cm", 10000.0, 10500.0),
    band("1.2 cm", 24000.0, 24250.0),
    band("6 mm", 47000.0, 47200.0),
    band("4 mm", 76000.0, 81000.0),
)

# AFuV Anlage 1 part A, class A (docs/SOURCES.md, "Transcribed values").
DE_BANDS: tuple[Band, ...] = (
    band("2200 m", 0.1357, 0.1378),
    band("630 m", 0.472, 0.479),
    band("160 m", 1.81, 2.0),
    band("80 m", 3.5, 3.8),
    band("60 m", 5.3515, 5.3665),
    band("40 m", 7.0, 7.2),
    band("30 m", 10.1, 10.15),
    band("20 m", 14.0, 14.35),
    band("17 m", 18.068, 18.168),
    band("15 m", 21.0, 21.45),
    band("12 m", 24.89, 24.99),
    band("10 m", 28.0, 29.7),
    band("6 m", 50.0, 52.0),
    band("2 m", 144.0, 146.0),
    band("70 cm", 430.0, 440.0),
    band("23 cm", 1240.0, 1300.0),
    band("13 cm", 2320.0, 2450.0),
    band("9 cm", 3400.0, 3475.0),
    band("5 cm", 5650.0, 5850.0),
    band("3 cm", 10000.0, 10500.0),
    band("1.2 cm", 24000.0, 24250.0),
    band("6 mm", 47000.0, 47200.0),
    band("4 mm", 76000.0, 81000.0),
    band("2.5 mm", 122250.0, 123000.0),
    band("2 mm", 134000.0, 141000.0),
    band("1.2 mm", 241000.0, 250000.0),
)

# ARCEP decision 2019-1412 annex, paragraph 1, Region 1 (docs/SOURCES.md).
FR_BANDS: tuple[Band, ...] = (
    band("2200 m", 0.1357, 0.1378),
    band("630 m", 0.472, 0.479),
    band("160 m", 1.81, 1.85),
    band("80 m", 3.5, 3.8),
    band("60 m", 5.3515, 5.3665),
    band("40 m", 7.0, 7.2),
    band("30 m", 10.1, 10.15),
    band("20 m", 14.0, 14.35),
    band("17 m", 18.068, 18.168),
    band("15 m", 21.0, 21.45),
    band("12 m", 24.89, 24.99),
    band("10 m", 28.0, 29.7),
    band("6 m", 50.0, 52.0),
    band("2 m", 144.0, 146.0),
    band("70 cm", 430.0, 440.0),
    band("23 cm", 1240.0, 1300.0),
    band("13 cm", 2300.0, 2450.0),
    band("5 cm", 5650.0, 5850.0),
    band("3 cm", 10000.0, 10500.0),
    band("1.2 cm", 24000.0, 24250.0),
    band("6 mm", 47000.0, 47200.0),
    band("4 mm", 76000.0, 81500.0),
    band("2.5 mm", 122250.0, 123000.0),
    band("2 mm", 134000.0, 141000.0),
    band("1.2 mm", 241000.0, 250000.0),
)

# Italian PNRF amateur rows (docs/SOURCES.md, "Transcribed values").
IT_BANDS: tuple[Band, ...] = (
    band("2200 m", 0.1357, 0.1378),
    band("630 m", 0.472, 0.479),
    band("160 m", 1.83, 1.85),
    band("80 m", 3.5, 3.8),
    band("60 m", 5.3515, 5.3665),
    band("40 m", 7.0, 7.2),
    band("30 m", 10.1, 10.15),
    band("20 m", 14.0, 14.35),
    band("17 m", 18.068, 18.168),
    band("15 m", 21.0, 21.45),
    band("12 m", 24.89, 24.99),
    band("10 m", 28.0, 29.7),
    band("6 m", 50.0, 52.0),
    band("2 m", 144.0, 146.0),
    seg("70 cm", (430.0, 434.0), (435.0, 438.0)),
    seg("23 cm", (1240.0, 1245.0), (1270.0, 1298.0)),
    band("13 cm", 2300.0, 2450.0),
    seg("5 cm", (5760.0, 5770.0), (5830.0, 5850.0)),
    band("3 cm", 10300.0, 10500.0),
    band("1.2 cm", 24000.0, 24050.0),
    band("6 mm", 47000.0, 47200.0),
    band("4 mm", 76000.0, 81500.0),
    band("2.5 mm", 122250.0, 123000.0),
    band("2 mm", 134000.0, 141000.0),
    band("1.2 mm", 241000.0, 250000.0),
)

BANDS = US_BANDS


def by_name(name: str) -> Band:
    return find(US_BANDS, name)
