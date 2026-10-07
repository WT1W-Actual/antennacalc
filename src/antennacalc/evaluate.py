"""Evaluate a station at one or more frequencies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from . import calc
from .bands import Band
from .feedline import FeedlineConfig
from .regions import DEFAULT, Region


@dataclass(frozen=True)
class Station:
    tx_power_w: float
    gain_dbi: float
    mode: str
    duty_cycle: float
    tx_minutes: float
    rx_minutes: float
    ground: bool
    antenna: str = "Custom"
    fixed_loss_db: float = 0.0
    feedline: FeedlineConfig | None = None

    def loss_db(self, freq_mhz: float) -> float:
        if self.feedline is not None:
            return self.feedline.evaluate(freq_mhz).total_loss_db
        return self.fixed_loss_db

    def feedline_text(self) -> str:
        if self.feedline is not None:
            return f"Estimated per frequency ({self.feedline.describe()})"
        return f"{self.fixed_loss_db:g} dB (entered manually)"


NOT_APPLICABLE = "Not applicable: {region} sets no controlled tier for amateur stations."


@dataclass(frozen=True)
class Evaluation:
    label: str
    freq_mhz: float
    band: Band | None
    loss_db: float
    power_at_antenna_w: float
    controlled: Optional[calc.Result]
    uncontrolled: calc.Result
    region: Region = DEFAULT

    @property
    def too_close(self) -> bool:
        results = [r for r in (self.controlled, self.uncontrolled) if r is not None]
        return min(r.safe_distance_m for r in results) * 100 < calc.MIN_DISTANCE_CM

    @property
    def plane_wave(self) -> bool:
        return self.freq_mhz < self.region.limit.plane_wave_below_mhz


@dataclass(frozen=True)
class Environment:
    role: str                     # "controlled" or "uncontrolled"
    title: str
    short: str
    css: str                      # "ctrl" or "unctrl"
    minutes: Optional[float]
    result: Optional[calc.Result]


def environments(e: Evaluation) -> list[Environment]:
    lim = e.region.limit
    out = []
    if lim.operator is None:
        out.append(Environment("controlled", "Controlled environment", "Controlled",
                               "ctrl", None, None))
    else:
        out.append(Environment("controlled", lim.operator.label, lim.operator.short,
                               "ctrl", lim.operator.avg_minutes(e.freq_mhz), e.controlled))
    out.append(Environment("uncontrolled", lim.public.label, lim.public.short, "unctrl",
                           lim.public.avg_minutes(e.freq_mhz), e.uncontrolled))
    return out


def evaluate(station: Station, freq_mhz: float, band: Band | None = None,
             region: Region | None = None) -> Evaluation:
    region = region or DEFAULT
    if station.tx_power_w <= 0:
        raise ValueError("Transmitter power must be greater than zero")
    region.limit.check(freq_mhz)
    loss = station.loss_db(freq_mhz)
    if loss < 0:
        raise ValueError("Feedline loss cannot be negative")
    ant_w = station.tx_power_w / 10 ** (loss / 10)

    def one(tier) -> calc.Result:
        return calc.calculate(
            freq_mhz=freq_mhz, power_w=ant_w, gain_dbi=station.gain_dbi,
            duty_cycle=station.duty_cycle, tx_minutes=station.tx_minutes,
            rx_minutes=station.rx_minutes, controlled=tier is region.limit.operator,
            ground=station.ground, tier=tier,
        )

    if band:
        label = band.label
    elif region.in_bands(freq_mhz):
        label = f"{freq_mhz:g} MHz"
    else:
        label = f"{freq_mhz:g} MHz (outside {region.name} amateur bands)"
    op = region.limit.operator
    return Evaluation(label, freq_mhz, band, loss, ant_w,
                      one(op) if op else None, one(region.limit.public), region)
