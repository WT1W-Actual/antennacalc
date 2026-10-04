"""Minimal PDF writer: Letter pages, Helvetica text, rules and filled boxes.

Standard library only, so the app keeps no third-party runtime dependencies.
Text uses the PDF base-14 Helvetica fonts (every viewer has them, nothing is
embedded) with WinAnsiEncoding. Characters outside that encoding print as "?".
"""

from __future__ import annotations

import zlib
from datetime import datetime

PAGE_W, PAGE_H = 612.0, 792.0  # US Letter, in points

# Advance widths (1/1000 em) for codes 32-126, from Adobe's Helvetica AFM files.
_REGULAR = (
    278, 278, 355, 556, 556, 889, 667, 191, 333, 333, 389, 584, 278, 333, 278, 278,
    556, 556, 556, 556, 556, 556, 556, 556, 556, 556, 278, 278, 584, 584, 584, 556,
    1015, 667, 667, 722, 722, 667, 611, 778, 722, 278, 500, 667, 556, 833, 722, 778,
    667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611, 278, 278, 278, 469, 556,
    333, 556, 556, 500, 556, 556, 278, 556, 556, 222, 222, 500, 222, 833, 556, 556,
    556, 556, 333, 500, 278, 556, 500, 722, 500, 500, 500, 334, 260, 334, 584,
)
_BOLD = (
    278, 333, 474, 556, 556, 889, 722, 238, 333, 333, 389, 584, 278, 333, 278, 278,
    556, 556, 556, 556, 556, 556, 556, 556, 556, 556, 333, 333, 584, 584, 584, 611,
    975, 722, 722, 722, 722, 667, 611, 778, 722, 278, 556, 722, 611, 833, 722, 778,
    667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611, 333, 278, 333, 584, 556,
    333, 556, 611, 556, 611, 556, 333, 611, 611, 278, 278, 556, 278, 889, 611, 611,
    611, 611, 389, 556, 333, 611, 556, 778, 556, 556, 500, 389, 280, 389, 584,
)
# The few non-ASCII WinAnsi glyphs the report can contain: ² · ° µ ×
_EXTRA = {0xB2: (333, 333), 0xB7: (278, 278), 0xB0: (400, 400),
          0xB5: (556, 611), 0xD7: (584, 584)}
_DEFAULT_WIDTH = 556

Color = tuple[float, float, float]


def _encode(text: str) -> bytes:
    return text.encode("cp1252", errors="replace")


def _glyph_width(code: int, bold: bool) -> int:
    if 32 <= code <= 126:
        return (_BOLD if bold else _REGULAR)[code - 32]
    if code in _EXTRA:
        return _EXTRA[code][1 if bold else 0]
    return _DEFAULT_WIDTH


def string_width(text: str, size: float, bold: bool = False) -> float:
    """Width of ``text`` in points when set in Helvetica at ``size``."""
    return sum(_glyph_width(c, bold) for c in _encode(text)) * size / 1000


def wrap(text: str, width: float, size: float, bold: bool = False) -> list[str]:
    """Greedy word wrap to ``width`` points; an over-long word gets its own line."""
    lines: list[str] = []
    line = ""
    for word in text.split():
        trial = f"{line} {word}" if line else word
        if line and string_width(trial, size, bold) > width:
            lines.append(line)
            line = word
        else:
            line = trial
    lines.append(line)
    return lines


def _num(v: float) -> str:
    return f"{v:.2f}".rstrip("0").rstrip(".") or "0"


def _literal(text: str) -> bytes:
    raw = _encode(text)
    return b"(" + raw.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)") + b")"


def _date(when: datetime) -> bytes:
    return _literal(when.strftime("D:%Y%m%d%H%M%S"))


class Page:
    """Drawing operations for one page. Coordinates are points from the bottom left."""

    def __init__(self) -> None:
        self.ops: list[bytes] = []

    def text(self, x: float, y: float, text: str, size: float, bold: bool = False,
             color: Color = (0, 0, 0)) -> None:
        font = b"/F2" if bold else b"/F1"
        self.ops.append(
            b"BT %s %s Tf %s rg %s %s Td %s Tj ET" % (
                font, _num(size).encode(), " ".join(_num(c) for c in color).encode(),
                _num(x).encode(), _num(y).encode(), _literal(text)))

    def rect(self, x: float, y: float, w: float, h: float, fill: Color | None = None,
             stroke: Color | None = None, line_width: float = 0.5) -> None:
        if fill is None and stroke is None:
            return
        ops = [b"q"]
        if fill is not None:
            ops.append(b"%s rg" % " ".join(_num(c) for c in fill).encode())
        if stroke is not None:
            ops.append(b"%s RG %s w" % (" ".join(_num(c) for c in stroke).encode(),
                                        _num(line_width).encode()))
        paint = b"B" if fill is not None and stroke is not None else (b"f" if fill else b"S")
        ops.append(b"%s %s %s %s re %s Q" % (
            _num(x).encode(), _num(y).encode(), _num(w).encode(), _num(h).encode(), paint))
        self.ops.append(b" ".join(ops))

    def line(self, x1: float, y1: float, x2: float, y2: float, color: Color,
             width: float = 0.5) -> None:
        self.ops.append(b"q %s RG %s w %s %s m %s %s l S Q" % (
            " ".join(_num(c) for c in color).encode(), _num(width).encode(),
            _num(x1).encode(), _num(y1).encode(), _num(x2).encode(), _num(y2).encode()))


class Document:
    def __init__(self) -> None:
        self.pages: list[Page] = []

    def add_page(self) -> Page:
        page = Page()
        self.pages.append(page)
        return page

    def to_bytes(self, title: str, producer: str, created: datetime) -> bytes:
        n = len(self.pages)
        # 1 catalog, 2 page tree, 3-4 fonts, 5 info, then a page and its content per page
        page_ids = [6 + 2 * i for i in range(n)]
        objs: list[bytes] = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [%s] /Count %d >>" % (
                b" ".join(b"%d 0 R" % p for p in page_ids), n),
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica "
            b"/Encoding /WinAnsiEncoding >>",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold "
            b"/Encoding /WinAnsiEncoding >>",
            b"<< /Title %s /Producer %s /CreationDate %s >>" % (
                _literal(title), _literal(producer), _date(created)),
        ]
        for pid, page in zip(page_ids, self.pages):
            stream = zlib.compress(b"\n".join(page.ops))
            objs.append(
                b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %s %s] "
                b"/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents %d 0 R >>"
                % (_num(PAGE_W).encode(), _num(PAGE_H).encode(), pid + 1))
            objs.append(b"<< /Length %d /Filter /FlateDecode >>\nstream\n%s\nendstream"
                        % (len(stream), stream))

        out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = []
        for i, body in enumerate(objs, start=1):
            offsets.append(len(out))
            out += b"%d 0 obj\n%s\nendobj\n" % (i, body)
        xref = len(out)
        out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
        out += b"".join(b"%010d 00000 n \n" % off for off in offsets)
        out += b"trailer\n<< /Size %d /Root 1 0 R /Info 5 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
            len(objs) + 1, xref)
        return bytes(out)
