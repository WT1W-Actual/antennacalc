"""Self-contained HTML report covering one or more evaluated frequencies."""

from __future__ import annotations

import re
from datetime import datetime
from html import escape

from . import __version__
from .evaluate import Evaluation, Station

DISCLAIMER = (
    "This report is an estimate for planning purposes only, based on the far-field "
    "model in FCC OET Bulletin 65 and the limits in 47 CFR 1.1310. It is not valid "
    "for antennas within 20 cm (8 in) of a person, does not model near-field effects, "
    "and evaluates one transmitter at a time. The station licensee is responsible "
    "for compliance."
)

CSS = """
:root { --accent:#1f4e79; --ctrl:#e8f1fa; --unctrl:#fdf0e3; --line:#d0d7de; }
* { box-sizing: border-box; }
body { font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  color:#1f2328; max-width: 860px; margin: 2rem auto; padding: 0 1rem; line-height:1.45; }
h1 { color:var(--accent); margin:0 0 .25rem; }
h2 { color:var(--accent); border-bottom:2px solid var(--accent); padding-bottom:.2rem;
  margin-top:2rem; }
h3 { margin:1rem 0 .4rem; }
.meta { color:#57606a; margin:0 0 1rem; }
table { border-collapse:collapse; width:100%; margin:.5rem 0 1rem; }
th, td { border:1px solid var(--line); padding:.35rem .6rem; text-align:left; }
th { background:#f6f8fa; }
td.num, th.num { text-align:right; font-variant-numeric: tabular-nums; }
table.kv th { width:42%; font-weight:600; background:#f6f8fa; }
.env { border-radius:6px; padding:.5rem .8rem; margin:.8rem 0; }
.env.ctrl { background:var(--ctrl); border-left:5px solid #2f6fb0; }
.env.unctrl { background:var(--unctrl); border-left:5px solid #d9822b; }
.env table { background:#fff; margin:.3rem 0 .4rem; }
.key td, .key th { font-weight:700; }
.warn { background:#fff4ce; border:1px solid #e3b341; padding:.5rem .8rem;
  border-radius:6px; margin:.8rem 0; }
.note { color:#57606a; font-size:.9rem; }
.band { page-break-inside: avoid; }
@media print { body { margin:0; max-width:none; } h2 { page-break-after:avoid; } }
"""


def _kv(rows: list[tuple[str, str]], css: str = "kv") -> str:
    body = "".join(
        f"<tr><th>{escape(k)}</th><td>{escape(v)}</td></tr>" for k, v in rows
    )
    return f'<table class="{css}">{body}</table>'


def _anchor(label: str) -> str:
    return "band-" + re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")


def _env(title: str, css: str, minutes: int, r) -> str:
    rows = [
        ("Max allowed power density", f"{r.limit_mw_cm2:.4g} mW/cm²"),
        ("Time averaged power", f"{r.avg_power_w:.4g} W"),
        ("EIRP", f"{r.eirp_w:.4g} W"),
    ]
    key = [
        ("Minimum safe distance (feet)", f"{r.safe_distance_ft:.2f} ft"),
        ("Minimum safe distance (meters)", f"{r.safe_distance_m:.2f} m"),
    ]
    return (
        f'<div class="env {css}"><h3>{escape(title)} '
        f'<span class="note">({minutes} minute average)</span></h3>'
        f"{_kv(rows)}{_kv(key, 'kv key')}</div>"
    )


def build_report(
    station: Station, evaluations: list[Evaluation], when: datetime | None = None
) -> str:
    when = when or datetime.now()
    stamp = when.strftime("%Y-%m-%d %H:%M")
    p: list[str] = []
    p.append(
        "<!DOCTYPE html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        "<title>Antenna RF Exposure Report</title>"
        f"<style>{CSS}</style></head><body>"
    )
    p.append("<h1>Antenna RF Exposure Report</h1>")
    p.append(
        f'<p class="meta">Generated {escape(stamp)} by antennacalc {escape(__version__)} '
        f"&middot; {len(evaluations)} frequenc{'y' if len(evaluations) == 1 else 'ies'} evaluated</p>"
    )

    p.append("<h2>Station</h2>")
    p.append(_kv([
        ("Antenna type", station.antenna),
        ("Antenna gain", f"{station.gain_dbi:g} dBi"),
        ("Transmitter power", f"{station.tx_power_w:g} W"),
        ("Feedline loss", station.feedline_text()),
        ("Mode", f"{station.mode} ({station.duty_cycle * 100:g}% duty cycle)"),
        ("Transmit pattern",
         f"{station.tx_minutes:g} min transmit, {station.rx_minutes:g} min receive"),
        ("Ground reflection", "included" if station.ground else "not included"),
    ]))

    if len(evaluations) > 1:
        p.append("<h2>Summary: minimum safe distance</h2>")
        rows = "".join(
            f'<tr><td><a href="#{_anchor(e.label)}">{escape(e.label)}</a></td>'
            f'<td class="num">{e.freq_mhz:g}</td>'
            f'<td class="num">{e.controlled.safe_distance_ft:.2f} ft '
            f'({e.controlled.safe_distance_m:.2f} m)</td>'
            f'<td class="num">{e.uncontrolled.safe_distance_ft:.2f} ft '
            f'({e.uncontrolled.safe_distance_m:.2f} m)</td></tr>'
            for e in evaluations
        )
        p.append(
            '<table><tr><th>Band</th><th class="num">Evaluated at (MHz)</th>'
            '<th class="num">Controlled</th><th class="num">Uncontrolled</th></tr>'
            f"{rows}</table>"
        )

    for e in evaluations:
        title = f"Band: {e.label}" if e.band else f"Frequency: {e.label}"
        p.append(f'<div class="band"><h2 id="{_anchor(e.label)}">{escape(title)}</h2>')
        info = [("Frequency evaluated", f"{e.freq_mhz:g} MHz")]
        if e.band:
            info.append(("Band range", f"{e.band.range_text} (evaluated at the most "
                                       "conservative frequency in the band)"))
        info += [
            ("Transmitter power", f"{station.tx_power_w:.4g} W"),
            ("Feedline loss at this frequency", f"{e.loss_db:.2f} dB"),
            ("Power at antenna", f"{e.power_at_antenna_w:.4g} W"),
        ]
        p.append(_kv(info))
        p.append(_env("Controlled environment", "ctrl", 6, e.controlled))
        p.append(_env("Uncontrolled environment", "unctrl", 30, e.uncontrolled))
        if e.too_close:
            p.append('<div class="warn"><strong>Warning:</strong> a distance is under '
                     "20 cm; results are not reliable that close.</div>")
        p.append("</div>")

    p.append("<h2>Notes</h2>")
    p.append(f'<p class="note">{escape(DISCLAIMER)}</p>')
    p.append("</body></html>\n")
    return "\n".join(p)
