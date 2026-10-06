"""Exposure limits by jurisdiction. FCC 47 CFR 1.1310 is the original."""

from __future__ import annotations

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
