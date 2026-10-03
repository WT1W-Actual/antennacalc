"""FCC 47 CFR 1.1310 maximum permissible exposure (MPE) limits."""

from __future__ import annotations

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
