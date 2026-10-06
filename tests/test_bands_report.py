from datetime import datetime

import pytest

from antennacalc import bands, calc, regions
from antennacalc.evaluate import Station, environments, evaluate
from antennacalc.feedline import CUSTOM, FeedlineConfig
from antennacalc.limits import MAX_FREQ_MHZ, MIN_FREQ_MHZ, mpe_limit_mw_cm2
from antennacalc.report import build_report


def station(**kw):
    base = dict(tx_power_w=100, gain_dbi=2.15, mode="Conversational CW", duty_cycle=0.4,
                tx_minutes=6, rx_minutes=4, ground=True, antenna="Dipole")
    base.update(kw)
    return Station(**base)


def test_all_bands_valid_and_ordered():
    for b in bands.BANDS:
        assert b.low_mhz < b.high_mhz
        assert MIN_FREQ_MHZ <= b.low_mhz and b.high_mhz <= MAX_FREQ_MHZ
        assert b.low_mhz <= regions.US.eval_freq_mhz(b) <= b.high_mhz
    assert len({b.name for b in bands.BANDS}) == len(bands.BANDS)


def test_eval_freq_is_most_conservative():
    assert regions.US.eval_freq_mhz(bands.by_name("20 m")) == 14.35   # limit falls with frequency
    assert regions.US.eval_freq_mhz(bands.by_name("2 m")) == 144.0    # flat limit -> lower edge
    assert regions.US.eval_freq_mhz(bands.by_name("70 cm")) == 420.0  # limit rises with frequency
    for b in bands.BANDS:
        e = mpe_limit_mw_cm2(regions.US.eval_freq_mhz(b), False)
        assert e <= mpe_limit_mw_cm2(b.low_mhz, False) + 1e-12
        assert e <= mpe_limit_mw_cm2(b.high_mhz, False) + 1e-12


def test_band_labels():
    assert bands.by_name("20 m").label == "20 m (14-14.35 MHz)"
    assert bands.by_name("3 cm").range_text == "10-10.5 GHz"


def test_evaluate_matches_calc():
    s = station(fixed_loss_db=3.0103)
    e = evaluate(s, 14.2)
    direct = calc.calculate(14.2, 50, 2.15, 0.4, 6, 4, False, True)
    assert e.power_at_antenna_w == pytest.approx(50, rel=1e-3)
    assert e.uncontrolled.safe_distance_m == pytest.approx(direct.safe_distance_m, rel=1e-3)
    assert e.label == "14.2 MHz"


def test_feedline_config_varies_by_frequency():
    cfg = FeedlineConfig("RG-8X", 80, swr=1.4)
    s = station(feedline=cfg)
    assert evaluate(s, 7.1).loss_db < evaluate(s, 146.0).loss_db


def test_custom_cable_config_is_frequency_independent():
    cfg = FeedlineConfig(CUSTOM, 100, custom_db_per_100ft=2.0)
    assert cfg.evaluate(7).total_loss_db == pytest.approx(cfg.evaluate(440).total_loss_db)


def test_evaluate_validation():
    with pytest.raises(ValueError):
        evaluate(station(tx_power_w=0), 14.2)
    with pytest.raises(ValueError):
        evaluate(station(fixed_loss_db=-1), 14.2)


def test_report_single_and_multi():
    s = station()
    one = build_report(s, [evaluate(s, 14.2)], datetime(2026, 1, 2, 3, 4))
    assert one.startswith("<!DOCTYPE html>")
    assert "Summary" not in one
    assert "Controlled environment" in one and "Uncontrolled environment" in one
    assert "(6 minute average)" in one and "(30 minute average)" in one
    assert "2026-01-02 03:04" in one
    assert "http://" not in one and "https://" not in one  # fully self-contained

    sel = [bands.by_name(n) for n in ("20 m", "2 m", "70 cm")]
    evs = [evaluate(s, regions.US.eval_freq_mhz(b), b) for b in sel]
    multi = build_report(s, evs, datetime(2026, 1, 2))
    assert "Summary: minimum safe distance" in multi
    for b in sel:
        assert f"Band: {b.label}" in multi
    assert multi.count("Uncontrolled environment") == 3
    assert multi.count('<div class="band">') == 3


def test_report_is_well_formed_html():
    from html.parser import HTMLParser

    s = station()
    evs = [evaluate(s, regions.US.eval_freq_mhz(b), b) for b in bands.BANDS]
    stack = []
    void = {"meta"}

    class P(HTMLParser):
        def handle_starttag(self, tag, attrs):
            if tag not in void:
                stack.append(tag)

        def handle_endtag(self, tag):
            assert stack and stack.pop() == tag, tag

    P().feed(build_report(s, evs))
    assert stack == []


def test_report_escapes_user_text():
    s = station(antenna="<script>alert(1)</script>")
    out = build_report(s, [evaluate(s, 14.2)])
    assert "<script>" not in out
    assert "&lt;script&gt;" in out


def test_report_warns_when_too_close():
    s = station(tx_power_w=0.01, gain_dbi=-10)
    assert "Warning:" in build_report(s, [evaluate(s, 146.0)])


def test_us_13cm_is_two_segments():
    b = bands.by_name("13 cm")
    assert b.segments == ((2300.0, 2310.0), (2390.0, 2450.0))
    assert b.range_text == "2.3-2.31 GHz, 2.39-2.45 GHz"


def test_us_9cm_removed():
    with pytest.raises(KeyError):
        bands.by_name("9 cm")


def test_segments_must_ascend_without_overlap():
    with pytest.raises(ValueError):
        bands.seg("x", (5, 6), (5.5, 7))
    with pytest.raises(ValueError):
        bands.seg("x", (6, 5))
    with pytest.raises(ValueError):
        bands.seg("x")


def test_evaluate_defaults_to_us():
    e = evaluate(station(), 14.2)
    assert e.region is regions.US
    assert e.controlled is not None


def test_region_without_operator_tier():
    e = evaluate(station(), 14.2, None, regions.GERMANY)
    assert e.controlled is None
    envs = environments(e)
    assert [x.role for x in envs] == ["controlled", "uncontrolled"]
    assert envs[0].result is None and envs[0].minutes is None
    assert envs[0].title == "Controlled environment"
    assert envs[1].title == "General public" and envs[1].minutes == 6
    assert not e.too_close


def test_region_limit_is_used():
    s = station()
    us = evaluate(s, 146.0)
    it = evaluate(s, 146.0, None, regions.ITALY)
    assert it.uncontrolled.limit_mw_cm2 < us.uncontrolled.limit_mw_cm2


def test_typed_frequency_outside_region_bands_is_labelled():
    e = evaluate(station(), 5.36, None, regions.AUSTRALIA)
    assert e.label == "5.36 MHz (outside Australia amateur bands)"
    assert evaluate(station(), 14.2, None, regions.AUSTRALIA).label == "14.2 MHz"


def test_frequency_outside_limit_range_is_a_value_error():
    with pytest.raises(ValueError):
        evaluate(station(), 0.05, None, regions.CANADA)
    with pytest.raises(ValueError):
        evaluate(station(), 150_000, None, regions.US)


def test_plane_wave_flag():
    assert evaluate(station(), 7.1, None, regions.CANADA).plane_wave
    assert not evaluate(station(), 14.2, None, regions.CANADA).plane_wave
    assert not evaluate(station(), 7.1).plane_wave


def test_help_text_is_region_neutral():
    from antennacalc.helptext import HELP_TEXT
    assert "REGION" in HELP_TEXT
    assert "within FCC limits" not in HELP_TEXT
