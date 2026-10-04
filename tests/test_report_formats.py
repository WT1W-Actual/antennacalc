import re
import zlib
from datetime import datetime

import pytest

from antennacalc import bands
from antennacalc.evaluate import Station, evaluate
from antennacalc.pdf import string_width
from antennacalc.report import (
    FORMATS,
    build_report,
    build_text_report,
    format_for_path,
    render_report,
)

WHEN = datetime(2026, 1, 2, 3, 4)


def station(**kw):
    base = dict(tx_power_w=100, gain_dbi=2.15, mode="Conversational CW", duty_cycle=0.4,
                tx_minutes=6, rx_minutes=4, ground=True, antenna="Dipole")
    base.update(kw)
    return Station(**base)


def all_bands(s):
    return [evaluate(s, b.eval_freq_mhz, b) for b in bands.BANDS]


# --- choosing a format from the save dialog ---------------------------------

@pytest.mark.parametrize("path, fmt", [
    ("r.html", "html"), ("r.htm", "html"), ("R.HTML", "html"),
    ("r.pdf", "pdf"), ("r.PDF", "pdf"),
    ("r.txt", "txt"), ("r.Txt", "txt"),
])
def test_format_follows_extension(path, fmt):
    assert format_for_path(path) == (fmt, path)


def test_extension_wins_over_selected_type():
    assert format_for_path("r.pdf", "txt") == ("pdf", "r.pdf")


def test_missing_extension_uses_selected_type():
    assert format_for_path("/tmp/report", "pdf") == ("pdf", "/tmp/report.pdf")
    assert format_for_path("/tmp/report", "txt") == ("txt", "/tmp/report.txt")


def test_missing_extension_defaults_to_html():
    assert format_for_path("/tmp/report") == ("html", "/tmp/report.html")
    assert format_for_path("/tmp/report", "bogus") == ("html", "/tmp/report.html")


def test_unknown_extension_gets_one_appended():
    assert format_for_path("/tmp/my.report", "pdf") == ("pdf", "/tmp/my.report.pdf")


def test_dot_in_directory_is_not_an_extension():
    assert format_for_path("/tmp/v1.2/report", "txt") == ("txt", "/tmp/v1.2/report.txt")


def test_formats_table():
    assert set(FORMATS) == {"html", "pdf", "txt"}
    for fmt, (label, ext) in FORMATS.items():
        assert ext == "." + fmt and label


# --- render_report dispatch --------------------------------------------------

def test_render_html_matches_build_report():
    s = station()
    evs = [evaluate(s, 14.2)]
    assert render_report("html", s, evs, WHEN) == build_report(s, evs, WHEN).encode("utf-8")


def test_render_txt_matches_build_text_report():
    s = station()
    evs = [evaluate(s, 14.2)]
    assert render_report("txt", s, evs, WHEN) == build_text_report(s, evs, WHEN).encode("utf-8")


def test_render_rejects_unknown_format():
    s = station()
    with pytest.raises(ValueError):
        render_report("docx", s, [evaluate(s, 14.2)], WHEN)


# --- plain text --------------------------------------------------------------

def test_text_report_single():
    s = station()
    out = build_text_report(s, [evaluate(s, 14.2)], WHEN)
    assert "ANTENNA RF EXPOSURE REPORT" in out
    assert "2026-01-02 03:04" in out
    assert "Dipole" in out
    assert "CONTROLLED ENVIRONMENT (6 minute average)" in out
    assert "UNCONTROLLED ENVIRONMENT (30 minute average)" in out
    assert "SUMMARY" not in out
    assert "<" not in out  # no markup leaks into the text format
    assert out.endswith("\n")


def test_text_report_multi_has_summary_and_every_band():
    s = station()
    sel = [bands.by_name(n) for n in ("20 m", "2 m", "70 cm")]
    out = build_text_report(s, [evaluate(s, b.eval_freq_mhz, b) for b in sel], WHEN)
    assert "SUMMARY: MINIMUM SAFE DISTANCE" in out
    for b in sel:
        assert f"BAND: {b.label}" in out
    assert out.count("UNCONTROLLED ENVIRONMENT") == 3


def test_text_report_lines_fit_72_columns():
    s = station()
    for line in build_text_report(s, all_bands(s), WHEN).splitlines():
        assert len(line) <= 72, line


def test_text_report_warns_when_too_close():
    s = station(tx_power_w=0.01, gain_dbi=-10)
    assert "WARNING:" in build_text_report(s, [evaluate(s, 146.0)], WHEN)


# --- PDF ---------------------------------------------------------------------

def pdf_objects(data: bytes) -> dict[int, bytes]:
    return {int(m.group(1)): m.group(2) for m in
            re.finditer(rb"(\d+) 0 obj\n(.*?)\nendobj", data, re.S)}


def page_texts(data: bytes) -> list[str]:
    """Decompressed content stream of each page, in page order."""
    out = []
    for m in re.finditer(rb"stream\n(.*?)\nendstream", data, re.S):
        out.append(zlib.decompress(m.group(1)).decode("latin-1"))
    return out


def test_pdf_is_well_formed():
    s = station()
    data = render_report("pdf", s, all_bands(s), WHEN)
    assert data.startswith(b"%PDF-1.4\n")
    assert data.endswith(b"%%EOF\n")

    # xref offsets point at each object's header
    xref_at = int(re.search(rb"startxref\n(\d+)\n%%EOF", data).group(1))
    assert data[xref_at:].startswith(b"xref\n")
    objs = pdf_objects(data)
    entries = re.findall(rb"(\d{10}) 00000 n \n", data[xref_at:])
    assert len(entries) == len(objs)
    for i, off in enumerate(entries, start=1):
        assert data[int(off):].startswith(f"{i} 0 obj\n".encode())

    # declared stream lengths match
    for body in objs.values():
        m = re.match(rb"<<.*?/Length (\d+).*?>>\nstream\n", body, re.S)
        if m:
            start = m.end()
            assert body[start + int(m.group(1)):].startswith(b"\nendstream")


def test_pdf_page_count_matches_tree():
    s = station()
    one = render_report("pdf", s, [evaluate(s, 14.2)], WHEN)
    many = render_report("pdf", s, all_bands(s), WHEN)
    assert re.search(rb"/Count 1\b", one)
    pages = len(page_texts(many))
    assert pages > 1
    assert re.search(rb"/Count %d\b" % pages, many)
    assert len(re.findall(rb"/Type /Page(?!s)", many)) == pages


def test_pdf_contains_report_text():
    s = station()
    sel = [bands.by_name(n) for n in ("20 m", "2 m")]
    data = render_report("pdf", s, [evaluate(s, b.eval_freq_mhz, b) for b in sel], WHEN)
    text = "".join(page_texts(data))
    for needle in ("(Antenna RF Exposure Report)", "(Summary: minimum safe distance)",
                   "(Controlled environment)", "(Uncontrolled environment)",
                   "(Band: 20 m \\(14-14.35 MHz\\))", "(Dipole)", "2026-01-02 03:04"):
        assert needle in text, needle
    assert "mW/cm\xb2" in text  # superscript two survives via WinAnsiEncoding


def test_pdf_pages_are_numbered():
    s = station()
    texts = page_texts(render_report("pdf", s, all_bands(s), WHEN))
    for n, t in enumerate(texts, start=1):
        assert f"(Page {n} of {len(texts)})" in t


def test_pdf_band_heading_never_ends_a_page():
    s = station()
    for t in page_texts(render_report("pdf", s, all_bands(s), WHEN)):
        shown = re.findall(r"\((.*?)\) Tj", t)
        body = [x for x in shown if not x.startswith("Page ")]
        assert not body[-1].startswith("Band:"), body[-1]


def test_pdf_escapes_and_replaces_text():
    s = station(antenna="Yagi (3 el) \\ test 天线")
    text = "".join(page_texts(render_report("pdf", s, [evaluate(s, 14.2)], WHEN)))
    assert "(Yagi \\(3 el\\) \\\\ test ??)" in text


def test_pdf_metadata_and_determinism():
    s = station()
    a = render_report("pdf", s, [evaluate(s, 14.2)], WHEN)
    assert a == render_report("pdf", s, [evaluate(s, 14.2)], WHEN)
    assert b"/Title (Antenna RF Exposure Report)" in a
    assert b"/CreationDate (D:20260102030400)" in a
    assert b"http://" not in a and b"https://" not in a


def test_pdf_warns_when_too_close():
    s = station(tx_power_w=0.01, gain_dbi=-10)
    text = "".join(page_texts(render_report("pdf", s, [evaluate(s, 146.0)], WHEN)))
    assert "(Warning:)" in text


def test_string_width_uses_helvetica_metrics():
    assert string_width("Hello", 10) == pytest.approx((722 + 556 + 222 + 222 + 556) / 100)
    assert string_width("Hello", 10, bold=True) == pytest.approx(
        (722 + 556 + 278 + 278 + 611) / 100)
    assert string_width("", 12) == 0
