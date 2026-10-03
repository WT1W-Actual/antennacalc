"""Evaluate a station at one or more frequencies."""

from __future__ import annotations

from dataclasses import dataclass

from . import calc
from .bands import Band
from .feedline import FeedlineConfig


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


@dataclass(frozen=True)
class Evaluation:
    label: str
    freq_mhz: float
    band: Band | None
    loss_db: float
    power_at_antenna_w: float
    controlled: calc.Result
    uncontrolled: calc.Result

    @property
    def too_close(self) -> bool:
        return min(
            self.controlled.safe_distance_m, self.uncontrolled.safe_distance_m
        ) * 100 < calc.MIN_DISTANCE_CM


def evaluate(station: Station, freq_mhz: float, band: Band | None = None) -> Evaluation:
    if station.tx_power_w <= 0:
        raise ValueError("Transmitter power must be greater than zero")
    loss = station.loss_db(freq_mhz)
    if loss < 0:
        raise ValueError("Feedline loss cannot be negative")
    ant_w = station.tx_power_w / 10 ** (loss / 10)

    def one(controlled: bool) -> calc.Result:
        return calc.calculate(
            freq_mhz=freq_mhz,
            power_w=ant_w,
            gain_dbi=station.gain_dbi,
            duty_cycle=station.duty_cycle,
            tx_minutes=station.tx_minutes,
            rx_minutes=station.rx_minutes,
            controlled=controlled,
            ground=station.ground,
        )

    label = band.label if band else f"{freq_mhz:g} MHz"
    return Evaluation(label, freq_mhz, band, loss, ant_w, one(True), one(False))
