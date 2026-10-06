"""PDF layout of the report, mirroring the HTML version's sections and colors."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from . import __version__
from .evaluate import NOT_APPLICABLE, Evaluation, Station, environments
from .pdf import PAGE_H, PAGE_W, Document, Page, string_width, wrap
from .report import (
    TITLE, TOO_CLOSE, Rows, count_text, distance_rows, distance_text, environment_rows,
    frequency_rows, notes_for, region_rows, section_title, station_rows,
)

MARGIN = 54.0
TOP = PAGE_H - MARGIN
BOTTOM = MARGIN + 14  # leaves room for the page number
BODY_W = PAGE_W - 2 * MARGIN
BODY_H = TOP - BOTTOM

SIZE = 9.5   # table text
LEAD = 12.0  # line spacing inside a cell
PAD = 4.5    # cell padding

TEXT = (0.122, 0.137, 0.157)
ACCENT = (0.122, 0.306, 0.475)
MUTED = (0.341, 0.376, 0.416)
LINE = (0.816, 0.843, 0.871)
HEAD_BG = (0.965, 0.973, 0.980)
WHITE = (1.0, 1.0, 1.0)
WARN_BG = (1.0, 0.957, 0.808)
WARN_LINE = (0.890, 0.702, 0.255)
ENV_COLORS = {  # css class -> (background, accent bar)
    "ctrl": ((0.910, 0.945, 0.980), (0.184, 0.435, 0.690)),
    "unctrl": ((0.992, 0.941, 0.890), (0.851, 0.510, 0.169)),
}


@dataclass
class Block:
    """A horizontal slice of the page: its height, and how to draw it from a top edge."""

    height: float
    draw: Callable[[Page, float], None]


def spacer(h: float) -> Block:
    return Block(h, lambda page, top: None)


@dataclass
class Cell:
    text: str
    width: float
    bold: bool = False
    right: bool = False
    fill: tuple[float, float, float] | None = None
    sub: str = ""  # optional muted line under the text
    bar: tuple[float, float, float] | None = None  # optional accent bar along the top


def row(cells: list[Cell], x: float = MARGIN) -> Block:
    """One bordered table row; cell text wraps and the row grows to fit."""
    wrapped = [[(ln, c.bold, TEXT) for ln in wrap(c.text, c.width - 2 * PAD, SIZE, c.bold)]
               + ([(ln, False, MUTED) for ln in wrap(c.sub, c.width - 2 * PAD, SIZE)]
                  if c.sub else [])
               for c in cells]
    height = max(len(w) for w in wrapped) * LEAD + 2 * PAD - (LEAD - SIZE)

    def draw(page: Page, top: float) -> None:
        cx = x
        for c, lines in zip(cells, wrapped):
            page.rect(cx, top - height, c.width, height, fill=c.fill, stroke=LINE)
            if c.bar:
                page.rect(cx, top - 3, c.width, 3, fill=c.bar)
            y = top - PAD - SIZE * 0.78
            for ln, bold, color in lines:
                tx = cx + c.width - PAD - string_width(ln, SIZE, bold) if c.right else cx + PAD
                page.text(tx, y, ln, SIZE, bold, color)
                y -= LEAD
            cx += c.width

    return Block(height, draw)


def kv_rows(rows: Rows, x: float = MARGIN, width: float = BODY_W,
            bold_values: bool = False) -> list[Block]:
    label_w = round(width * 0.42, 2)
    return [row([Cell(k, label_w, True, fill=HEAD_BG),
                 Cell(v, width - label_w, bold_values, fill=WHITE)], x) for k, v in rows]


def text_block(text: str, size: float, bold: bool = False, color=TEXT,
               width: float = BODY_W, x: float = MARGIN, after: float = 0.0) -> Block:
    lines = wrap(text, width, size, bold)
    lead = size * 1.3
    height = len(lines) * lead + after

    def draw(page: Page, top: float) -> None:
        y = top - size
        for ln in lines:
            page.text(x, y, ln, size, bold, color)
            y -= lead

    return Block(height, draw)


def heading(text: str) -> list[Block]:
    size = 14.0

    def draw(page: Page, top: float) -> None:
        page.text(MARGIN, top - 14 - size, text, size, True, ACCENT)
        page.line(MARGIN, top - 14 - size - 5, MARGIN + BODY_W, top - 14 - size - 5, ACCENT, 1.5)

    return [Block(14 + size + 12, draw)]


def results(e: Evaluation) -> list[Block]:
    """Both environments side by side: one column each, color-coded as in the HTML panels.

    Same rows as the HTML report; minimum safe distances in bold.
    """
    label_w = round(BODY_W * 0.42, 2)
    envs = environments(e)
    col_w = (BODY_W - label_w) / len(envs)
    head = row([Cell("", label_w, fill=HEAD_BG)] + [
        Cell(env.title, col_w, True, fill=ENV_COLORS[env.css][0], bar=ENV_COLORS[env.css][1],
             sub="" if env.result is None else f"({env.minutes:g} minute average)")
        for env in envs])
    blocks = [spacer(8), head]
    template = next(env.result for env in envs if env.result is not None)
    for rows_of, bold in ((environment_rows, False), (distance_rows, True)):
        for i, (label, _v) in enumerate(rows_of(template)):
            blocks.append(row([Cell(label, label_w, True, fill=HEAD_BG)] + [
                Cell("n/a" if env.result is None else rows_of(env.result)[i][1],
                     col_w, bold, right=True, fill=WHITE) for env in envs]))
    if any(env.result is None for env in envs):
        blocks.append(text_block(NOT_APPLICABLE.format(region=e.region.name), 9, color=MUTED))
    return blocks


def warning() -> list[Block]:
    size = 9.5
    lead_in = "Warning:"
    rest_x = MARGIN + 10 + string_width(lead_in, size, True) + 3
    lines = wrap(TOO_CLOSE, MARGIN + BODY_W - 10 - rest_x, size)
    height = len(lines) * size * 1.3 + 14

    def draw(page: Page, top: float) -> None:
        page.rect(MARGIN, top - height, BODY_W, height, fill=WARN_BG, stroke=WARN_LINE)
        y = top - 7 - size
        page.text(MARGIN + 10, y, lead_in, size, True, TEXT)
        for ln in lines:
            page.text(rest_x, y, ln, size, False, TEXT)
            y -= size * 1.3

    return [spacer(8), Block(height, draw)]


def summary(evaluations: list[Evaluation]) -> list[list[Block]]:
    """Summary table as groups: the header travels with its first row."""
    widths = [BODY_W * 0.34, BODY_W * 0.18, BODY_W * 0.24, BODY_W * 0.24]
    envs = environments(evaluations[0])
    head = row([Cell("Band", widths[0], True, fill=HEAD_BG),
                Cell("Evaluated at (MHz)", widths[1], True, True, HEAD_BG),
                Cell(envs[0].short, widths[2], True, True, HEAD_BG),
                Cell(envs[1].short, widths[3], True, True, HEAD_BG)])
    rows = [row([Cell(e.label, widths[0]),
                 Cell(f"{e.freq_mhz:g}", widths[1], right=True),
                 Cell(distance_text(e.controlled), widths[2], right=True),
                 Cell(distance_text(e.uncontrolled), widths[3], right=True)])
            for e in evaluations]
    return [heading("Summary: minimum safe distance") + [head, rows[0]]] + [[r] for r in rows[1:]]


class Flow:
    """Places blocks top to bottom, starting a new page when one won't fit."""

    def __init__(self) -> None:
        self.doc = Document()
        self.new_page()

    def new_page(self) -> None:
        self.page = self.doc.add_page()
        self.y = TOP

    def place(self, blocks: list[Block]) -> None:
        """Keep ``blocks`` on one page when they fit on a page at all."""
        total = sum(b.height for b in blocks)
        if total > self.y - BOTTOM and total <= BODY_H:
            self.new_page()
        for b in blocks:
            if b.height > self.y - BOTTOM and self.y < TOP:
                self.new_page()
            b.draw(self.page, self.y)
            self.y -= b.height


def build_pdf_report(
    station: Station, evaluations: list[Evaluation], when: datetime | None = None
) -> bytes:
    when = when or datetime.now()
    flow = Flow()
    flow.place([
        text_block(TITLE, 20, True, ACCENT, after=4),
        text_block(f"Generated {when.strftime('%Y-%m-%d %H:%M')} by antennacalc "
                   f"{__version__} · {count_text(evaluations)}", 9.5, color=MUTED),
    ])
    flow.place(heading("Station") + kv_rows(station_rows(station) + region_rows(evaluations[0])))

    if len(evaluations) > 1:
        for group in summary(evaluations):
            flow.place(group)

    for e in evaluations:
        section = heading(section_title(e)) + kv_rows(frequency_rows(station, e)) + results(e)
        if e.too_close:
            section += warning()
        flow.place(section)

    flow.place(heading("Notes") + [text_block(n, 9, color=MUTED, after=4)
                                   for n in notes_for(evaluations)])

    pages = flow.doc.pages
    for n, page in enumerate(pages, start=1):
        label = f"Page {n} of {len(pages)}"
        page.text(PAGE_W - MARGIN - string_width(label, 8), MARGIN - 4, label, 8, False, MUTED)
    return flow.doc.to_bytes(TITLE, f"antennacalc {__version__}", when)
