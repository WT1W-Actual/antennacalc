"""Reports covering one or more evaluated frequencies, as HTML, PDF, plain text or CSV.

The row helpers below hold every label and value once; each format only lays
them out.
"""

from __future__ import annotations

import csv
import io
import os
import re
import textwrap
from datetime import datetime
from html import escape

from . import __version__
from .evaluate import Evaluation, Station

TITLE = "Antenna RF Exposure Report"

DISCLAIMER = (
    "This report is an estimate for planning purposes only, based on the far-field "
    "model in FCC OET Bulletin 65 and the limits in 47 CFR 1.1310. It is not valid "
    "for antennas within 20 cm (8 in) of a person, does not model near-field effects, "
    "and evaluates one transmitter at a time. The station licensee is responsible "
    "for compliance."
)

TOO_CLOSE = "a distance is under 20 cm; results are not reliable that close."

# (title, css class, averaging minutes, Evaluation attribute)
ENVIRONMENTS = (
    ("Controlled environment", "ctrl", 6, "controlled"),
    ("Uncontrolled environment", "unctrl", 30, "uncontrolled"),
)

# Save formats: key -> (file dialog label, extension)
FORMATS = {
    "html": ("HTML report", ".html"),
    "pdf": ("PDF document", ".pdf"),
    "txt": ("Plain text", ".txt"),
    "csv": ("CSV spreadsheet", ".csv"),
}
_BY_EXTENSION = {".html": "html", ".htm": "html", ".pdf": "pdf", ".txt": "txt",
                 ".csv": "csv"}

Rows = list[tuple[str, str]]


# --- shared content ----------------------------------------------------------

def station_rows(station: Station) -> Rows:
    return [
        ("Antenna type", station.antenna),
        ("Antenna gain", f"{station.gain_dbi:g} dBi"),
        ("Transmitter power", f"{station.tx_power_w:g} W"),
        ("Feedline loss", station.feedline_text()),
        ("Mode", f"{station.mode} ({station.duty_cycle * 100:g}% duty cycle)"),
        ("Transmit pattern",
         f"{station.tx_minutes:g} min transmit, {station.rx_minutes:g} min receive"),
        ("Ground reflection", "included" if station.ground else "not included"),
    ]


def frequency_rows(station: Station, e: Evaluation) -> Rows:
    rows = [("Frequency evaluated", f"{e.freq_mhz:g} MHz")]
    if e.band:
        rows.append(("Band range", f"{e.band.range_text} (evaluated at the most "
                                   "conservative frequency in the band)"))
    rows += [
        ("Transmitter power", f"{station.tx_power_w:.4g} W"),
        ("Feedline loss at this frequency", f"{e.loss_db:.2f} dB"),
        ("Power at antenna", f"{e.power_at_antenna_w:.4g} W"),
    ]
    return rows


def environment_rows(r) -> Rows:
    return [
        ("Max allowed power density", f"{r.limit_mw_cm2:.4g} mW/cm²"),
        ("Time averaged power", f"{r.avg_power_w:.4g} W"),
        ("EIRP", f"{r.eirp_w:.4g} W"),
    ]


def distance_rows(r) -> Rows:
    return [
        ("Minimum safe distance (feet)", f"{r.safe_distance_ft:.2f} ft"),
        ("Minimum safe distance (meters)", f"{r.safe_distance_m:.2f} m"),
    ]


def section_title(e: Evaluation) -> str:
    return f"Band: {e.label}" if e.band else f"Frequency: {e.label}"


def count_text(evaluations: list[Evaluation]) -> str:
    n = len(evaluations)
    return f"{n} frequenc{'y' if n == 1 else 'ies'} evaluated"


def distance_text(r) -> str:
    return f"{r.safe_distance_ft:.2f} ft ({r.safe_distance_m:.2f} m)"


# --- HTML --------------------------------------------------------------------

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


def _kv(rows: Rows, css: str = "kv") -> str:
    body = "".join(
        f"<tr><th>{escape(k)}</th><td>{escape(v)}</td></tr>" for k, v in rows
    )
    return f'<table class="{css}">{body}</table>'


def _anchor(label: str) -> str:
    return "band-" + re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")


def _env(title: str, css: str, minutes: int, r) -> str:
    return (
        f'<div class="env {css}"><h3>{escape(title)} '
        f'<span class="note">({minutes} minute average)</span></h3>'
        f"{_kv(environment_rows(r))}{_kv(distance_rows(r), 'kv key')}</div>"
    )


def build_report(
    station: Station, evaluations: list[Evaluation], when: datetime | None = None
) -> str:
    """Self-contained HTML report."""
    when = when or datetime.now()
    stamp = when.strftime("%Y-%m-%d %H:%M")
    p: list[str] = []
    p.append(
        "<!DOCTYPE html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        f"<title>{TITLE}</title>"
        f"<style>{CSS}</style></head><body>"
    )
    p.append(f"<h1>{TITLE}</h1>")
    p.append(
        f'<p class="meta">Generated {escape(stamp)} by antennacalc {escape(__version__)} '
        f"&middot; {count_text(evaluations)}</p>"
    )

    p.append("<h2>Station</h2>")
    p.append(_kv(station_rows(station)))

    if len(evaluations) > 1:
        p.append("<h2>Summary: minimum safe distance</h2>")
        rows = "".join(
            f'<tr><td><a href="#{_anchor(e.label)}">{escape(e.label)}</a></td>'
            f'<td class="num">{e.freq_mhz:g}</td>'
            f'<td class="num">{distance_text(e.controlled)}</td>'
            f'<td class="num">{distance_text(e.uncontrolled)}</td></tr>'
            for e in evaluations
        )
        p.append(
            '<table><tr><th>Band</th><th class="num">Evaluated at (MHz)</th>'
            '<th class="num">Controlled</th><th class="num">Uncontrolled</th></tr>'
            f"{rows}</table>"
        )

    for e in evaluations:
        p.append(f'<div class="band"><h2 id="{_anchor(e.label)}">'
                 f"{escape(section_title(e))}</h2>")
        p.append(_kv(frequency_rows(station, e)))
        for title, css, minutes, attr in ENVIRONMENTS:
            p.append(_env(title, css, minutes, getattr(e, attr)))
        if e.too_close:
            p.append(f'<div class="warn"><strong>Warning:</strong> {TOO_CLOSE}</div>')
        p.append("</div>")

    p.append("<h2>Notes</h2>")
    p.append(f'<p class="note">{escape(DISCLAIMER)}</p>')
    p.append("</body></html>\n")
    return "\n".join(p)


# --- plain text --------------------------------------------------------------

WIDTH = 72
_LABEL = 34


def _text_rows(rows: Rows, indent: int = 2) -> list[str]:
    out = []
    for label, value in rows:
        lines = textwrap.wrap(value, WIDTH - indent - _LABEL) or [""]
        out.append(f"{' ' * indent}{label + ':':<{_LABEL}}{lines[0]}")
        out += [" " * (indent + _LABEL) + more for more in lines[1:]]
    return out


def build_text_report(
    station: Station, evaluations: list[Evaluation], when: datetime | None = None
) -> str:
    """Plain-text report, 72 columns wide."""
    when = when or datetime.now()
    bar, rule = "=" * WIDTH, "-" * WIDTH
    out = [bar, TITLE.upper().center(WIDTH).rstrip(), bar]
    out += _text_rows([
        ("Generated", when.strftime("%Y-%m-%d %H:%M")),
        ("Program", f"antennacalc {__version__}"),
        ("Frequencies evaluated", str(len(evaluations))),
    ], 0)
    out += ["", "STATION", rule] + _text_rows(station_rows(station))

    if len(evaluations) > 1:
        out += ["", "SUMMARY: MINIMUM SAFE DISTANCE (feet)", rule]
        out.append(f"  {'Band':<28}{'MHz':>10}{'Controlled':>15}{'Uncontrolled':>15}")
        for e in evaluations:
            out.append(
                f"  {e.label:<28}{e.freq_mhz:>10g}"
                f"{e.controlled.safe_distance_ft:>12.2f} ft"
                f"{e.uncontrolled.safe_distance_ft:>12.2f} ft"
            )

    for e in evaluations:
        out += ["", bar, f"{'BAND' if e.band else 'FREQUENCY'}: {e.label}", bar]
        out += _text_rows(frequency_rows(station, e), 0)
        for title, _css, minutes, attr in ENVIRONMENTS:
            r = getattr(e, attr)
            out += ["", f"{title.upper()} ({minutes} minute average)", rule]
            out += _text_rows(environment_rows(r) + distance_rows(r))
        if e.too_close:
            out += [""] + textwrap.wrap(f"WARNING: {TOO_CLOSE}", WIDTH,
                                        initial_indent="  ", subsequent_indent="  ")

    out += ["", bar, "NOTES", bar]
    out += textwrap.wrap(DISCLAIMER, WIDTH)
    out.append("")
    return "\n".join(out)


# --- CSV ---------------------------------------------------------------------

def _csv_environment(title: str, minutes: int, r) -> dict[str, str]:
    env = title.split()[0]  # "Controlled" / "Uncontrolled"
    return {
        f"{env} averaging period (min)": str(minutes),
        f"{env} max allowed power density (mW/cm²)": f"{r.limit_mw_cm2:.4g}",
        f"{env} time averaged power (W)": f"{r.avg_power_w:.4g}",
        f"{env} EIRP (W)": f"{r.eirp_w:.4g}",
        f"{env} minimum safe distance (ft)": f"{r.safe_distance_ft:.2f}",
        f"{env} minimum safe distance (m)": f"{r.safe_distance_m:.2f}",
    }


def build_csv_report(
    station: Station, evaluations: list[Evaluation], when: datetime | None = None
) -> str:
    """One header row, then one row per evaluated band or frequency.

    Station inputs repeat on every row so each row stands alone in a spreadsheet.
    Numbers carry no units; the units are in the column names.
    """
    when = when or datetime.now()
    rows = []
    for e in evaluations:
        row = {
            "Generated": when.strftime("%Y-%m-%d %H:%M"),
            "Program": f"antennacalc {__version__}",
            "Band": e.band.name if e.band else "",
            "Band range": e.band.range_text if e.band else "",
            "Frequency evaluated (MHz)": f"{e.freq_mhz:g}",
            "Antenna type": station.antenna,
            "Antenna gain (dBi)": f"{station.gain_dbi:g}",
            "Transmitter power (W)": f"{station.tx_power_w:g}",
            "Feedline": station.feedline_text(),
            "Mode": station.mode,
            "Duty cycle (%)": f"{station.duty_cycle * 100:g}",
            "Transmit minutes": f"{station.tx_minutes:g}",
            "Receive minutes": f"{station.rx_minutes:g}",
            "Ground reflection": "yes" if station.ground else "no",
            "Feedline loss at this frequency (dB)": f"{e.loss_db:.2f}",
            "Power at antenna (W)": f"{e.power_at_antenna_w:.4g}",
        }
        for title, _css, minutes, attr in ENVIRONMENTS:
            row.update(_csv_environment(title, minutes, getattr(e, attr)))
        row["Under 20 cm"] = "yes" if e.too_close else "no"
        rows.append(row)

    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()


# --- format selection --------------------------------------------------------

def format_for_path(path: str, selected: str | None = None) -> tuple[str, str]:
    """Pick the save format for ``path``.

    A known extension decides the format. Otherwise the type chosen in the save
    dialog does (HTML when none was chosen) and its extension is appended.
    """
    ext = os.path.splitext(path)[1].lower()
    if ext in _BY_EXTENSION:
        return _BY_EXTENSION[ext], path
    fmt = selected if selected in FORMATS else "html"
    return fmt, path + FORMATS[fmt][1]


def render_report(
    fmt: str, station: Station, evaluations: list[Evaluation],
    when: datetime | None = None,
) -> bytes:
    """The report in ``fmt`` (a key of FORMATS), ready to write in binary mode."""
    when = when or datetime.now()
    if fmt == "html":
        return build_report(station, evaluations, when).encode("utf-8")
    if fmt == "txt":
        return build_text_report(station, evaluations, when).encode("utf-8")
    if fmt == "csv":
        # The byte-order mark lets Excel read the file as UTF-8 (for "mW/cm²").
        return build_csv_report(station, evaluations, when).encode("utf-8-sig")
    if fmt == "pdf":
        from .pdf_report import build_pdf_report  # imports this module's row helpers

        return build_pdf_report(station, evaluations, when)
    raise ValueError(f"Unknown report format: {fmt!r}")
