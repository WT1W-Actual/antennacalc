import math

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


SC6_U = [  # (MHz, W/m^2) one point per Table 5 row, values worked from the table
    (14.2, 2.0),
    (28.0, 8.944 / math.sqrt(28.0)),
    (146.0, 1.291),
    (446.0, 0.02619 * 446.0 ** 0.6834),
    (10368.0, 10.0),
    (200000.0, 6.67e-5 * 200000.0),
]
SC6_C = [  # Table 6
    (14.2, 10.0),
    (28.0, 44.72 / math.sqrt(28.0)),
    (52.0, 6.455),
    (146.0, 0.6455 * math.sqrt(146.0)),
    (10368.0, 50.0),
    (200000.0, 3.33e-4 * 200000.0),
]


@pytest.mark.parametrize("f,s", SC6_U)
def test_sc6_uncontrolled_rows(f, s):
    assert limits.sc6_uncontrolled_w_m2(f) == pytest.approx(s, rel=1e-6)
    assert limits.SC6.public.limit_mw_cm2(f) == pytest.approx(s / 10, rel=1e-6)


@pytest.mark.parametrize("f,s", SC6_C)
def test_sc6_controlled_rows(f, s):
    assert limits.sc6_controlled_w_m2(f) == pytest.approx(s, rel=1e-6)


def test_sc6_below_10_mhz_uses_tighter_of_e_and_h():
    # 7.1 MHz uncontrolled: E = 87/sqrt(f) -> 2.8277 W/m^2; H = 0.73/f -> 3.985 W/m^2
    assert limits.sc6_uncontrolled_w_m2(7.1) == pytest.approx((87 / math.sqrt(7.1)) ** 2 / 377)
    # 0.475 MHz: E capped at 83 V/m -> 18.273 W/m^2
    assert limits.sc6_uncontrolled_w_m2(0.475) == pytest.approx(83 ** 2 / 377)
    # 7.1 MHz controlled: E = 193/sqrt(f) -> 13.915 W/m^2
    assert limits.sc6_controlled_w_m2(7.1) == pytest.approx((193 / math.sqrt(7.1)) ** 2 / 377)


@pytest.mark.parametrize("f", [20.0, 48.0, 300.0, 6000.0, 150000.0])
def test_sc6_uncontrolled_continuous_at_breakpoints(f):
    lo = limits.sc6_uncontrolled_w_m2(f * (1 - 1e-9))
    assert limits.sc6_uncontrolled_w_m2(f) == pytest.approx(lo, rel=2e-3)


def test_sc6_averaging():
    assert limits.sc6_avg_minutes(1000) == 6
    assert limits.sc6_avg_minutes(15000) == pytest.approx(6, rel=1e-2)
    assert limits.sc6_avg_minutes(24000) == pytest.approx(616000 / 24000 ** 1.2)


def test_sc6_range_and_tiers():
    assert limits.SC6.operator is not None
    with pytest.raises(ValueError):
        limits.sc6_uncontrolled_w_m2(0.05)
    with pytest.raises(ValueError):
        limits.sc6_uncontrolled_w_m2(300001)


ARPANSA = [
    (146.0, 2.0),
    (446.0, 446.0 / 200),
    (3000.0, 10.0),
    (14.2, min((300 / 14.2 ** 0.7) ** 2 / 377, 377 * (2.2 / 14.2) ** 2)),
    (3.6, min(83 ** 2 / 377, 377 * (2.2 / 3.6) ** 2)),
]


@pytest.mark.parametrize("f,s", ARPANSA)
def test_arpansa_rows(f, s):
    assert limits.arpansa_public_w_m2(f) == pytest.approx(s, rel=1e-6)


def test_arpansa_has_no_operator_tier_and_30_min_average():
    assert limits.ARPANSA.operator is None
    assert limits.ARPANSA.public.avg_minutes(146) == 30
    assert limits.ARPANSA.plane_wave_below_mhz == 30.0
    assert limits.ARPANSA.public.label == "General public"


EU = [
    (0.1365, 87 ** 2 / 377),
    (1.9, (87 / math.sqrt(1.9)) ** 2 / 377),
    (14.2, 2.0),
    (446.0, 446.0 / 200),
    (5760.0, 10.0),
]


@pytest.mark.parametrize("f,s", EU)
def test_eu_rows(f, s):
    assert limits.eu_public_w_m2(f) == pytest.approx(s, rel=1e-6)


def test_eu_averaging():
    assert limits.eu_avg_minutes(5760) == 6
    assert limits.eu_avg_minutes(24000) == pytest.approx(68 / 24 ** 1.05)


def test_france_uses_eu_curve_with_its_own_citation():
    for f, _ in EU:
        assert limits.FRANCE.public.limit_mw_cm2(f) == limits.EU.public.limit_mw_cm2(f)
    assert "2002-775" in limits.FRANCE.citation


GERMANY = [  # tighter of E and H from Anhang 1b at every frequency
    (1.9, min((87 / math.sqrt(1.9)) ** 2 / 377, 377 * (0.73 / 1.9) ** 2)),
    (14.2, min(28 ** 2 / 377, 377 * 0.073 ** 2)),
    (1296.0, min(1.375 ** 2 * 1296 / 377, 377 * 0.0037 ** 2 * 1296)),
    (10368.0, min(61 ** 2 / 377, 377 * 0.16 ** 2)),
]


@pytest.mark.parametrize("f,s", GERMANY)
def test_germany_rows(f, s):
    assert limits.bimschv_w_m2(f) == pytest.approx(s, rel=1e-6)


def test_germany_flags_the_implant_gap():
    assert any("50527" in n for n in limits.GERMANY.notes)
    assert limits.GERMANY.public.avg_minutes(24000) == 6


def test_no_operator_tier_in_europe():
    for lim in (limits.EU, limits.FRANCE, limits.GERMANY, limits.ITALY):
        assert lim.operator is None


def test_italy_6_v_per_m():
    assert limits.italy_w_m2(0.1365) == pytest.approx(36 / 377)
    assert limits.ITALY.public.limit_mw_cm2(0.1365) == pytest.approx(36 / 377 / 10)
    for f in (14.2, 146.0, 10368.0):
        assert limits.italy_w_m2(f) == pytest.approx(0.10)
        assert limits.ITALY.public.limit_mw_cm2(f) == pytest.approx(0.010)
    assert limits.ITALY.public.avg_minutes(146) == 1440
    assert any("6 minutes" in n for n in limits.ITALY.notes)
