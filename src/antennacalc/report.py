"""Plain-text report covering one or more evaluated frequencies."""

from __future__ import annotations

import textwrap
from datetime import datetime

from . import __version__
from .evaluate import Evaluation, Station

WIDTH = 72
DISCLAIMER = (
    "This report is an estimate for planning purposes only, based on the far-field "
    "model in FCC OET Bulletin 65 and the limits in 47 CFR 1.1310. It is not valid "
    "for antennas within 20 cm (8 in) of a person, does not model near-field effects, "
    "and evaluates one transmitter at a time. The station licensee is responsible "
    "for compliance."
)


def _wrap(text: str) -> list[str]:
    return textwrap.wrap(text, WIDTH)


def _line(label: str, value: str, indent: int = 2) -> str:
    return f"{' ' * indent}{label:<34}{value}"


def _env_block(title: str, minutes: int, r) -> list[str]:
    return [
        f"{title} ({minutes} minute average)",
        "-" * WIDTH,
        _line("Max allowed power density:", f"{r.limit_mw_cm2:.4g} mW/cm^2"),
        _line("Time averaged power:", f"{r.avg_power_w:.4g} W"),
        _line("EIRP:", f"{r.eirp_w:.4g} W"),
        _line("Minimum safe distance (feet):", f"{r.safe_distance_ft:.2f} ft"),
        _line("Minimum safe distance (meters):", f"{r.safe_distance_m:.2f} m"),
    ]


def build_report(
    station: Station, evaluations: list[Evaluation], when: datetime | None = None
) -> str:
    when = when or datetime.now()
    out: list[str] = []
    bar = "=" * WIDTH
    out += [bar, "ANTENNA RF EXPOSURE REPORT".center(WIDTH), bar]
    out.append(_line("Generated:", when.strftime("%Y-%m-%d %H:%M"), 0))
    out.append(_line("Program:", f"antennacalc {__version__}", 0))
    out.append(_line("Frequencies evaluated:", str(len(evaluations)), 0))
    out += ["", "STATION", "-" * WIDTH]
    out += [
        _line("Antenna type:", station.antenna),
        _line("Antenna gain:", f"{station.gain_dbi:g} dBi"),
        _line("Transmitter power:", f"{station.tx_power_w:g} W"),
        _line("Feedline loss:", station.feedline_text()),
        _line("Mode:", f"{station.mode} ({station.duty_cycle * 100:g}% duty cycle)"),
        _line("Transmit pattern:",
              f"{station.tx_minutes:g} min transmit, {station.rx_minutes:g} min receive"),
        _line("Ground reflection:", "included" if station.ground else "not included"),
    ]

    if len(evaluations) > 1:
        out += ["", "SUMMARY - MINIMUM SAFE DISTANCE (feet)", "-" * WIDTH]
        out.append(f"  {'Band':<26}{'MHz':>10}{'Controlled':>16}{'Uncontrolled':>16}")
        for e in evaluations:
            out.append(
                f"  {e.label:<26}{e.freq_mhz:>10g}"
                f"{e.controlled.safe_distance_ft:>13.2f} ft"
                f"{e.uncontrolled.safe_distance_ft:>13.2f} ft"
            )

    for e in evaluations:
        out += ["", bar, f"BAND: {e.label}" if e.band else f"FREQUENCY: {e.label}", bar]
        out.append(_line("Frequency evaluated:", f"{e.freq_mhz:g} MHz", 0))
        if e.band:
            out.append(_line("Band range:", e.band.range_text, 0))
            out.append(_line("", "(most conservative frequency in the band)", 0))
        out.append(_line("Transmitter power:", f"{station.tx_power_w:.4g} W", 0))
        out.append(_line("Feedline loss at this frequency:", f"{e.loss_db:.2f} dB", 0))
        out.append(_line("Power at antenna:", f"{e.power_at_antenna_w:.4g} W", 0))
        out.append("")
        out += _env_block("CONTROLLED ENVIRONMENT", 6, e.controlled)
        out.append("")
        out += _env_block("UNCONTROLLED ENVIRONMENT", 30, e.uncontrolled)
        if e.too_close:
            out += ["", "  WARNING: a distance is under 20 cm; results are not reliable that close."]

    out += ["", bar, "NOTES", bar]
    out += _wrap(DISCLAIMER)
    out.append("")
    return "\n".join(out)
