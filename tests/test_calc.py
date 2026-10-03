import math

import pytest

from antennacalc import calc
from antennacalc.limits import mpe_limit_mw_cm2


def test_limits():
    assert mpe_limit_mw_cm2(14.2, False) == pytest.approx(180 / 14.2**2)
    assert mpe_limit_mw_cm2(14.2, True) == pytest.approx(900 / 14.2**2)
    assert mpe_limit_mw_cm2(146.52, False) == 0.2
    assert mpe_limit_mw_cm2(146.52, True) == 1.0
    assert mpe_limit_mw_cm2(446, False) == pytest.approx(446 / 1500)
    assert mpe_limit_mw_cm2(2000, True) == 5.0
    with pytest.raises(ValueError):
        mpe_limit_mw_cm2(0.1, True)


def test_distance_roundtrip():
    r = calc.calculate(146.52, 50, 3, 1.0, 1, 0, False, True)
    s = calc.power_density_mw_cm2(r.eirp_w, r.safe_distance_m, True)
    assert s == pytest.approx(r.limit_mw_cm2)


# Reference values captured from the ARRL web calculator:
# (watts, duty, tx_min, rx_min, gain, MHz, ground,
#  ctrl_limit, ctrl_m, unctrl_limit, unctrl_m)
ARRL_CASES = [
    (100, 0.20, 6, 4, 2.15, 14.2, True, 4.4634, 0.3870, 0.8927, 0.6703),
    (50, 1.0, 5, 10, 3, 146.52, False, 1.0, 0.8134, 0.2, 1.1503),
    (1500, 0.50, 1, 0, 9, 7.1, True, 17.8536, 2.6073, 3.5707, 5.8300),
    (5, 1.0, 7, 13, 0, 446, True, 1.4867, 0.2618, 0.2973, 0.3998),
    (100, 0.40, 10, 20, 12, 1.9, False, 100.0, 0.2246, 49.8615, 0.1836),
    (100, 1.0, 20, 15, 0, 14.2, True, 4.4634, 0.6756, 0.8927, 1.2334),
]


@pytest.mark.parametrize("w,duty,tx,rx,gain,f,gnd,cl,cm,ul,um", ARRL_CASES)
def test_matches_arrl(w, duty, tx, rx, gain, f, gnd, cl, cm, ul, um):
    c = calc.calculate(f, w, gain, duty, tx, rx, True, gnd)
    u = calc.calculate(f, w, gain, duty, tx, rx, False, gnd)
    assert c.limit_mw_cm2 == pytest.approx(cl, abs=1e-4)
    assert c.safe_distance_m == pytest.approx(cm, abs=2e-4)
    assert u.limit_mw_cm2 == pytest.approx(ul, abs=1e-4)
    assert u.safe_distance_m == pytest.approx(um, abs=2e-4)


def test_known_value():
    # 100 W, 0 dBi, 100% duty, no ground, 0.2 mW/cm^2 -> sqrt(1e5/(4*pi*0.2)) cm
    r = calc.calculate(146.52, 100, 0, 1.0, 1, 0, False, False)
    assert r.safe_distance_m * 100 == pytest.approx(math.sqrt(1e5 / (4 * math.pi * 0.2)))


def test_validation():
    with pytest.raises(ValueError):
        calc.tx_fraction(0, 0, 6)
    assert calc.tx_fraction(6, 4, 30) == pytest.approx(0.6)
    assert calc.tx_fraction(40, 0, 30) == 1.0
