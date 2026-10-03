"""Feedline loss estimate: matched cable loss, connectors, and SWR mismatch."""

from __future__ import annotations

import math
from dataclasses import dataclass

FT_PER_M = 3.280839895

# Approximate manufacturer matched loss, dB per 100 ft, at (MHz, dB) points.
# Typical values only; use a custom dB/100 ft figure for your exact cable.
CABLES: dict[str, list[tuple[float, float]]] = {
    "RG-58": [(1, 0.4), (10, 1.4), (50, 3.3), (100, 4.9), (200, 7.3), (400, 11.2), (700, 16.5), (1000, 21.5)],
    "RG-8X": [(1, 0.3), (10, 1.0), (50, 2.4), (100, 3.4), (200, 4.9), (400, 7.4), (700, 10.4), (1000, 12.9)],
    "RG-213 / RG-8": [(1, 0.2), (10, 0.6), (50, 1.3), (100, 1.8), (200, 2.6), (400, 3.8), (700, 5.2), (1000, 6.5)],
    "LMR-400 / 9913": [(1, 0.12), (10, 0.39), (50, 0.9), (100, 1.28), (200, 1.8), (400, 2.6), (700, 3.4), (1000, 4.1)],
    "LMR-600": [(1, 0.07), (10, 0.23), (50, 0.52), (100, 0.73), (200, 1.0), (400, 1.5), (700, 2.0), (1000, 2.4)],
}
CUSTOM = "Custom (dB per 100 ft)"


def loss_per_100ft(cable: str, freq_mhz: float) -> float:
    """Log-log interpolation (extrapolating at the ends) of matched loss in dB/100 ft."""
    pts = CABLES[cable]
    if freq_mhz <= 0:
        raise ValueError("Frequency must be positive")
    i = 0
    while i < len(pts) - 2 and freq_mhz > pts[i + 1][0]:
        i += 1
    (f1, l1), (f2, l2) = pts[i], pts[i + 1]
    slope = math.log(l2 / l1) / math.log(f2 / f1)
    return l1 * (freq_mhz / f1) ** slope


@dataclass(frozen=True)
class FeedlineResult:
    matched_loss_db: float
    mismatch_loss_db: float
    connector_loss_db: float
    total_loss_db: float
    power_at_antenna_w: float


def total_line_loss_db(matched_db: float, swr: float) -> float:
    """Cable loss including SWR at the antenna (ARRL Handbook total-loss formula)."""
    if swr < 1:
        raise ValueError("SWR must be 1.0 or greater")
    if matched_db < 0:
        raise ValueError("Cable loss cannot be negative")
    rho = (swr - 1) / (swr + 1)
    a = 10 ** (matched_db / 10)
    if rho == 0:
        return matched_db
    return 10 * math.log10((a * a - rho * rho) / (a * (1 - rho * rho)))


def power_at_antenna(
    tx_power_w: float,
    length: float,
    loss_db_per_100ft: float,
    swr: float = 1.0,
    connector_loss_db: float = 0.0,
    length_in_meters: bool = False,
) -> FeedlineResult:
    if tx_power_w < 0 or length < 0 or connector_loss_db < 0 or loss_db_per_100ft < 0:
        raise ValueError("Power, length, and losses must be non-negative")
    length_ft = length * FT_PER_M if length_in_meters else length
    matched = loss_db_per_100ft * length_ft / 100
    with_swr = total_line_loss_db(matched, swr)
    total = with_swr + connector_loss_db
    return FeedlineResult(
        matched_loss_db=matched,
        mismatch_loss_db=with_swr - matched,
        connector_loss_db=connector_loss_db,
        total_loss_db=total,
        power_at_antenna_w=tx_power_w / 10 ** (total / 10),
    )


@dataclass(frozen=True)
class FeedlineConfig:
    """Cable description that can be evaluated at any frequency."""

    cable: str
    length: float
    length_in_meters: bool = False
    swr: float = 1.0
    connector_loss_db: float = 0.0
    custom_db_per_100ft: float = 0.0

    def per_100ft(self, freq_mhz: float) -> float:
        if self.cable == CUSTOM:
            return self.custom_db_per_100ft
        return loss_per_100ft(self.cable, freq_mhz)

    def evaluate(self, freq_mhz: float) -> FeedlineResult:
        return power_at_antenna(
            1.0, self.length, self.per_100ft(freq_mhz), self.swr,
            self.connector_loss_db, self.length_in_meters,
        )

    def describe(self) -> str:
        unit = "m" if self.length_in_meters else "ft"
        cable = "custom cable" if self.cable == CUSTOM else self.cable
        return f"{cable}, {self.length:g} {unit}, SWR {self.swr:g}, connectors {self.connector_loss_db:g} dB"
