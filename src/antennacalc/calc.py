"""RF exposure calculations based on FCC OET Bulletin 65 far-field equations."""

from __future__ import annotations

import math
from dataclasses import dataclass

from .limits import FCC, Tier, mpe_limit_mw_cm2

# Ground reflection: field factor 1.6 -> power factor 1.6^2.
GROUND_REFLECTION_FACTOR = 2.56
FT_PER_M = 3.280839895
MIN_DISTANCE_CM = 20.0

# Mode name -> duty cycle (fraction), per ARRL instructions.
MODE_DUTY_CYCLES: dict[str, float] = {
    "Conversational SSB (no speech processing)": 0.20,
    "Conversational SSB (heavy speech processing)": 0.50,
    "Conversational CW": 0.40,
    "FM": 1.00,
    "AM": 1.00,
    "FSK / RTTY": 1.00,
    "AFSK SSB": 1.00,
    "Carrier always on (tune-up)": 1.00,
    "Other / unknown (worst case)": 1.00,
}


@dataclass(frozen=True)
class Result:
    limit_mw_cm2: float
    avg_power_w: float
    eirp_w: float
    safe_distance_m: float

    @property
    def safe_distance_ft(self) -> float:
        return self.safe_distance_m * FT_PER_M


CONTROLLED_AVG_MIN = 6.0
UNCONTROLLED_AVG_MIN = 30.0


def tx_fraction(tx_minutes: float, rx_minutes: float, interval_min: float) -> float:
    """Fraction of the averaging interval spent transmitting.

    Repeats the tx+rx cycle across the interval (worst case: transmit first),
    counting a partial final cycle, as the ARRL calculator does.
    """
    if tx_minutes <= 0 or rx_minutes < 0:
        raise ValueError("Transmit minutes must be positive and receive minutes non-negative")
    cycle = tx_minutes + rx_minutes
    if tx_minutes >= interval_min:
        return 1.0
    if cycle >= interval_min:
        return tx_minutes / interval_min
    remainder = interval_min % cycle
    complete = (interval_min // cycle) * tx_minutes
    return (complete + min(tx_minutes, remainder)) / interval_min


def average_power_w(power_w: float, duty_cycle: float, tx_frac: float) -> float:
    if power_w < 0:
        raise ValueError("Power must be non-negative")
    if not 0 <= duty_cycle <= 1 or not 0 <= tx_frac <= 1:
        raise ValueError("Duty cycle and transmit fraction must be between 0 and 1")
    return power_w * duty_cycle * tx_frac


def eirp_w(avg_power_w: float, gain_dbi: float) -> float:
    return avg_power_w * 10 ** (gain_dbi / 10)


def power_density_mw_cm2(eirp: float, distance_m: float, ground: bool) -> float:
    """Power density at a distance (m) from the antenna, in mW/cm^2."""
    if distance_m <= 0:
        raise ValueError("Distance must be positive")
    factor = GROUND_REFLECTION_FACTOR if ground else 1.0
    r_cm = distance_m * 100
    return eirp * 1000 * factor / (4 * math.pi * r_cm**2)


def calculate(
    freq_mhz: float,
    power_w: float,
    gain_dbi: float,
    duty_cycle: float,
    tx_minutes: float,
    rx_minutes: float,
    controlled: bool,
    ground: bool,
    tier: "Tier | None" = None,
) -> Result:
    if tier is None:
        tier = FCC.operator if controlled else FCC.public
    limit = tier.limit_mw_cm2(freq_mhz)
    interval = tier.avg_minutes(freq_mhz)
    avg = average_power_w(power_w, duty_cycle, tx_fraction(tx_minutes, rx_minutes, interval))
    eirp = eirp_w(avg, gain_dbi)
    factor = GROUND_REFLECTION_FACTOR if ground else 1.0
    r_cm = math.sqrt(eirp * 1000 * factor / (4 * math.pi * limit))
    return Result(limit, avg, eirp, r_cm / 100)
