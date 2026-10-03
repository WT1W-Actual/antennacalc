from datetime import datetime

import pytest

from antennacalc import bands, calc
from antennacalc.evaluate import Station, evaluate
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
        assert b.low_mhz <= b.eval_freq_mhz <= b.high_mhz
    assert len({b.name for b in bands.BANDS}) == len(bands.BANDS)


def test_eval_freq_is_most_conservative():
    assert bands.by_name("20 m").eval_freq_mhz == 14.35   # limit falls with frequency
    assert bands.by_name("2 m").eval_freq_mhz == 144.0    # flat limit -> lower edge
    assert bands.by_name("70 cm").eval_freq_mhz == 420.0  # limit rises with frequency
    for b in bands.BANDS:
        e = mpe_limit_mw_cm2(b.eval_freq_mhz, False)
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
    assert "SUMMARY" not in one
    assert "CONTROLLED ENVIRONMENT (6 minute average)" in one
    assert "UNCONTROLLED ENVIRONMENT (30 minute average)" in one
    assert "2026-01-02 03:04" in one

    sel = [bands.by_name(n) for n in ("20 m", "2 m", "70 cm")]
    evs = [evaluate(s, b.eval_freq_mhz, b) for b in sel]
    multi = build_report(s, evs, datetime(2026, 1, 2))
    assert "SUMMARY" in multi
    for b in sel:
        assert f"BAND: {b.label}" in multi
    assert multi.count("UNCONTROLLED ENVIRONMENT (30 minute average)") == 3
    assert multi.isascii()
    assert all(len(line) <= 90 for line in multi.splitlines())


def test_report_warns_when_too_close():
    s = station(tx_power_w=0.01, gain_dbi=-10)
    assert "WARNING" in build_report(s, [evaluate(s, 146.0)])
