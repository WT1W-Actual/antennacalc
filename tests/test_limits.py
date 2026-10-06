import pytest

from antennacalc import calc, limits


def test_plane_wave_takes_the_tighter_field():
    assert limits.plane_wave_w_m2(e_v_m=27.46) == pytest.approx(2.0, rel=1e-3)
    assert limits.plane_wave_w_m2(h_a_m=0.073) == pytest.approx(2.009, rel=1e-3)
    assert limits.plane_wave_w_m2(28, 0.073) == pytest.approx(377 * 0.073**2)
    with pytest.raises(ValueError):
        limits.plane_wave_w_m2()


def test_fcc_limit_record_matches_function():
    for f in (0.475, 1.9, 14.2, 146.52, 446, 2400, 10368):
        assert limits.FCC.public.limit_mw_cm2(f) == limits.mpe_limit_mw_cm2(f, False)
        assert limits.FCC.operator.limit_mw_cm2(f) == limits.mpe_limit_mw_cm2(f, True)
    assert limits.FCC.public.avg_minutes(14.2) == 30
    assert limits.FCC.operator.avg_minutes(14.2) == 6
    assert limits.FCC.tier(True) is limits.FCC.operator
    assert limits.FCC.tier(False) is limits.FCC.public


def test_limit_check_rejects_out_of_range():
    with pytest.raises(ValueError):
        limits.FCC.check(0.1)
    with pytest.raises(ValueError):
        limits.FCC.check(150_000)
    limits.FCC.check(14.2)


def test_calculate_accepts_a_tier():
    t = limits.Tier("Test", "Test", lambda f: 0.2, lambda f: 30.0)
    a = calc.calculate(146.52, 50, 3, 1.0, 1, 0, False, True)
    b = calc.calculate(146.52, 50, 3, 1.0, 1, 0, False, True, tier=t)
    assert a == b
    half = limits.Tier("Half", "Half", lambda f: 0.1, lambda f: 30.0)
    c = calc.calculate(146.52, 50, 3, 1.0, 1, 0, False, True, tier=half)
    assert c.safe_distance_m == pytest.approx(a.safe_distance_m * 2 ** 0.5)
