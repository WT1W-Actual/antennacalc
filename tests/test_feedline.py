import pytest

from antennacalc import feedline as fl


def test_interpolation_hits_table_points():
    assert fl.loss_per_100ft("RG-8X", 100) == pytest.approx(3.4)
    assert 3.4 < fl.loss_per_100ft("RG-8X", 146.52) < 4.9


def test_matched_line_no_swr():
    r = fl.power_at_antenna(100, 100, 3.0103)
    assert r.power_at_antenna_w == pytest.approx(50, rel=1e-3)
    assert r.mismatch_loss_db == 0


def test_swr_adds_loss():
    flat = fl.power_at_antenna(100, 80, 3.4, swr=1.0)
    bad = fl.power_at_antenna(100, 80, 3.4, swr=3.0)
    assert bad.total_loss_db > flat.total_loss_db
    assert bad.mismatch_loss_db > 0


def test_arrl_example():
    # ARRL: 100 W, 80 ft RG-8X, SWR 1.4, 146.52 MHz -> about 46 W
    r = fl.power_at_antenna(100, 80, fl.loss_per_100ft("RG-8X", 146.52), swr=1.4)
    assert r.power_at_antenna_w == pytest.approx(46, rel=0.08)


def test_meters_and_connectors():
    ft = fl.power_at_antenna(100, 100, 2.0)
    m = fl.power_at_antenna(100, 100 / fl.FT_PER_M, 2.0, length_in_meters=True)
    assert m.total_loss_db == pytest.approx(ft.total_loss_db)
    assert fl.power_at_antenna(100, 0, 2.0, connector_loss_db=3.0103).power_at_antenna_w == pytest.approx(50, rel=1e-3)


def test_validation():
    with pytest.raises(ValueError):
        fl.power_at_antenna(100, 50, 2.0, swr=0.5)
