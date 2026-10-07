"""Regions: a band table bound to the exposure limits that apply there."""

from __future__ import annotations

from dataclasses import dataclass

from . import bands as _b
from . import limits as _l
from .bands import Band


@dataclass(frozen=True)
class Region:
    name: str
    bands: tuple
    limit: _l.Limit

    def eval_freq_mhz(self, band: Band) -> float:
        """Most conservative frequency in the band under this region's public tier.

        Candidates are every segment edge plus every limit breakpoint inside a
        segment; ties go to the lowest frequency.
        """
        cands = set()
        for low, high in band.segments:
            cands.update((low, high))
            cands.update(p for p in self.limit.breakpoints if low < p < high)
        return min(sorted(cands), key=self.limit.public.limit_mw_cm2)

    def in_bands(self, f_mhz: float) -> bool:
        return any(lo <= f_mhz <= hi for b in self.bands for lo, hi in b.segments)

    def find(self, name: str) -> Band:
        return _b.find(self.bands, name)


US = Region("United States", _b.US_BANDS, _l.FCC)
CANADA = Region("Canada", _b.CA_BANDS, _l.SC6)
AUSTRALIA = Region("Australia", _b.AU_BANDS, _l.ARPANSA)
GERMANY = Region("Germany", _b.DE_BANDS, _l.GERMANY)
FRANCE = Region("France", _b.FR_BANDS, _l.FRANCE)
ITALY = Region("Italy", _b.IT_BANDS, _l.ITALY)
CEPT = Region("Europe (CEPT)", _b.CEPT_BANDS, _l.EU)

REGIONS = (US, CANADA, AUSTRALIA, GERMANY, FRANCE, ITALY, CEPT)
DEFAULT = US


def by_name(name: str) -> Region:
    for r in REGIONS:
        if r.name == name:
            return r
    raise KeyError(name)
