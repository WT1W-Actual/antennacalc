"""Exposure limits by jurisdiction. FCC 47 CFR 1.1310 is the original."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Optional

MIN_FREQ_MHZ = 0.3
MAX_FREQ_MHZ = 100_000.0


def mpe_limit_mw_cm2(freq_mhz: float, controlled: bool) -> float:
    """Return the power density limit in mW/cm^2 for a frequency in MHz."""
    f = freq_mhz
    if not MIN_FREQ_MHZ <= f <= MAX_FREQ_MHZ:
        raise ValueError(
            f"Frequency must be between {MIN_FREQ_MHZ} and {MAX_FREQ_MHZ:g} MHz"
        )
    if controlled:
        if f < 3.0:
            return 100.0
        if f < 30.0:
            return 900.0 / f**2
        if f < 300.0:
            return 1.0
        if f < 1500.0:
            return f / 300.0
        return 5.0
    if f < 1.34:
        return 100.0
    if f < 30.0:
        return 180.0 / f**2
    if f < 300.0:
        return 0.2
    if f < 1500.0:
        return f / 1500.0
    return 1.0


Z0 = 377.0  # free-space impedance, ohms


def plane_wave_w_m2(e_v_m: Optional[float] = None, h_a_m: Optional[float] = None) -> float:
    """Plane-wave equivalent power density (W/m^2) of an E and/or H limit; the smaller wins."""
    vals = []
    if e_v_m is not None:
        vals.append(e_v_m * e_v_m / Z0)
    if h_a_m is not None:
        vals.append(Z0 * h_a_m * h_a_m)
    if not vals:
        raise ValueError("plane_wave_w_m2 needs an E or an H value")
    return min(vals)


@dataclass(frozen=True)
class Tier:
    label: str                                  # shown in the GUI and reports
    short: str                                  # summary-table column heading
    limit_mw_cm2: Callable[[float], float]
    avg_minutes: Callable[[float], float]


@dataclass(frozen=True)
class Limit:
    name: str
    citation: str
    min_mhz: float
    max_mhz: float
    public: Tier
    operator: Optional[Tier]
    breakpoints: tuple
    plane_wave_below_mhz: float
    notes: tuple = field(default=())

    def tier(self, controlled: bool) -> Optional[Tier]:
        return self.operator if controlled else self.public

    def check(self, f_mhz: float) -> None:
        if not self.min_mhz <= f_mhz <= self.max_mhz:
            raise ValueError(
                f"Frequency must be between {self.min_mhz:g} and {self.max_mhz:g} MHz "
                f"under {self.name}"
            )


FCC = Limit(
    name="FCC 47 CFR 1.1310",
    citation="47 CFR 1.1310, Table 1 (FCC), with the far-field method of OET Bulletin 65",
    min_mhz=MIN_FREQ_MHZ,
    max_mhz=MAX_FREQ_MHZ,
    public=Tier("Uncontrolled environment", "Uncontrolled",
                lambda f: mpe_limit_mw_cm2(f, False), lambda f: 30.0),
    operator=Tier("Controlled environment", "Controlled",
                  lambda f: mpe_limit_mw_cm2(f, True), lambda f: 6.0),
    breakpoints=(1.34, 3.0, 30.0, 300.0, 1500.0),
    plane_wave_below_mhz=0.0,
)


def _in(f: float, lo: float, hi: float, name: str) -> None:
    if not lo <= f <= hi:
        raise ValueError(f"Frequency must be between {lo:g} and {hi:g} MHz under {name}")


def sc6_uncontrolled_w_m2(f: float) -> float:
    """Safety Code 6 (2015), uncontrolled environment. Tables 3 and 5."""
    _in(f, 0.1, 300_000.0, "Safety Code 6")
    if f < 10:
        return plane_wave_w_m2(min(83.0, 87.0 / math.sqrt(f)), min(90.0, 0.73 / f))
    if f < 20:
        return 2.0
    if f < 48:
        return 8.944 / math.sqrt(f)
    if f < 300:
        return 1.291
    if f < 6000:
        return 0.02619 * f ** 0.6834
    if f < 150_000:
        return 10.0
    return 6.67e-5 * f


def sc6_controlled_w_m2(f: float) -> float:
    """Safety Code 6 (2015), controlled environment. Tables 4 and 6."""
    _in(f, 0.1, 300_000.0, "Safety Code 6")
    if f < 10:
        return plane_wave_w_m2(min(170.0, 193.0 / math.sqrt(f)), min(180.0, 1.6 / f))
    if f < 20:
        return 10.0
    if f < 48:
        return 44.72 / math.sqrt(f)
    if f < 100:
        return 6.455
    if f < 6000:
        return 0.6455 * math.sqrt(f)
    if f < 150_000:
        return 50.0
    return 3.33e-4 * f


def sc6_avg_minutes(f: float) -> float:
    return 6.0 if f < 15_000 else 616_000.0 / f ** 1.2


SC6 = Limit(
    name="Health Canada Safety Code 6",
    citation=("Health Canada Safety Code 6 (2015), Tables 3 to 6; applied to amateur "
              "stations by ISED RBR-4 Issue 3 s.12 and CPC-2-0-03 Issue 6 s.7.1"),
    min_mhz=0.1,
    max_mhz=300_000.0,
    public=Tier("Uncontrolled environment", "Uncontrolled",
                lambda f: sc6_uncontrolled_w_m2(f) / 10, sc6_avg_minutes),
    operator=Tier("Controlled environment", "Controlled",
                  lambda f: sc6_controlled_w_m2(f) / 10, sc6_avg_minutes),
    breakpoints=(10.0, 20.0, 48.0, 100.0, 300.0, 6000.0, 15_000.0, 150_000.0),
    plane_wave_below_mhz=10.0,
    notes=("Below 10 MHz, Safety Code 6's instantaneous nerve-stimulation limits "
           "(83 V/m uncontrolled, 170 V/m controlled) are applied as averaged limits, "
           "which is conservative.",),
)


def arpansa_public_w_m2(f: float) -> float:
    """ARPANSA RPS S-1 (2021) Table 4, general public whole body; E below 6.27 MHz
    from Table 7 (83 V/m)."""
    _in(f, 0.1, 300_000.0, "ARPANSA RPS S-1")
    if f <= 30:
        e = 83.0 if f <= 6.27 else 300.0 / f ** 0.7
        return plane_wave_w_m2(e, 2.2 / f)
    if f <= 400:
        return 2.0
    if f <= 2000:
        return f / 200.0
    return 10.0


ARPANSA = Limit(
    name="ARPANSA RPS S-1",
    citation=("ARPANSA RPS S-1 (2021), Table 4, general public; applied to amateur "
              "stations by the Radiocommunications (Amateur Stations) Class Licence 2023, "
              "Schedule 1 clause 2"),
    min_mhz=0.1,
    max_mhz=300_000.0,
    public=Tier("General public", "General public",
                lambda f: arpansa_public_w_m2(f) / 10, lambda f: 30.0),
    operator=None,
    breakpoints=(6.27, 30.0, 400.0, 2000.0),
    plane_wave_below_mhz=30.0,
)
