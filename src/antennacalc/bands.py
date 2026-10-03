"""US amateur radio bands (47 CFR 97.301) and the frequency used to evaluate each."""

from __future__ import annotations

from dataclasses import dataclass

from .limits import mpe_limit_mw_cm2


@dataclass(frozen=True)
class Band:
    name: str
    low_mhz: float
    high_mhz: float

    @property
    def eval_freq_mhz(self) -> float:
        """Most conservative frequency in the band.

        The FCC limit is monotonic in frequency within a band, so one of the band
        edges has the lowest limit. When the limit is flat, the lower edge is used.
        """
        low = mpe_limit_mw_cm2(self.low_mhz, False)
        high = mpe_limit_mw_cm2(self.high_mhz, False)
        return self.high_mhz if high < low else self.low_mhz

    @property
    def range_text(self) -> str:
        if self.low_mhz >= 1000:
            return f"{self.low_mhz / 1000:g}-{self.high_mhz / 1000:g} GHz"
        return f"{self.low_mhz:g}-{self.high_mhz:g} MHz"

    @property
    def label(self) -> str:
        return f"{self.name} ({self.range_text})"


BANDS: list[Band] = [
    Band("630 m", 0.472, 0.479),
    Band("160 m", 1.8, 2.0),
    Band("80 m", 3.5, 4.0),
    Band("60 m", 5.3305, 5.4035),
    Band("40 m", 7.0, 7.3),
    Band("30 m", 10.1, 10.15),
    Band("20 m", 14.0, 14.35),
    Band("17 m", 18.068, 18.168),
    Band("15 m", 21.0, 21.45),
    Band("12 m", 24.89, 24.99),
    Band("10 m", 28.0, 29.7),
    Band("6 m", 50.0, 54.0),
    Band("2 m", 144.0, 148.0),
    Band("1.25 m", 222.0, 225.0),
    Band("70 cm", 420.0, 450.0),
    Band("33 cm", 902.0, 928.0),
    Band("23 cm", 1240.0, 1300.0),
    Band("13 cm", 2300.0, 2450.0),
    Band("9 cm", 3300.0, 3500.0),
    Band("5 cm", 5650.0, 5925.0),
    Band("3 cm", 10000.0, 10500.0),
    Band("1.2 cm", 24000.0, 24250.0),
    Band("6 mm", 47000.0, 47200.0),
    Band("4 mm", 76000.0, 81000.0),
]


def by_name(name: str) -> Band:
    for b in BANDS:
        if b.name == name:
            return b
    raise KeyError(name)
