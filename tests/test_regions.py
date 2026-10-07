import pytest

from antennacalc import bands, regions


def test_dropdown_order_and_default():
    assert [r.name for r in regions.REGIONS] == [
        "United States", "Canada", "Australia", "Germany", "France", "Italy", "Europe (CEPT)"]
    assert regions.DEFAULT is regions.US
    assert regions.by_name("Canada") is regions.CANADA
    with pytest.raises(KeyError):
        regions.by_name("Atlantis")


@pytest.mark.parametrize("region", regions.REGIONS, ids=lambda r: r.name)
def test_every_band_fits_its_limit(region):
    names = [b.name for b in region.bands]
    assert len(names) == len(set(names))
    for b in region.bands:
        assert region.limit.min_mhz <= b.low_mhz and b.high_mhz <= region.limit.max_mhz
        f = region.eval_freq_mhz(b)
        assert any(lo <= f <= hi for lo, hi in b.segments)


@pytest.mark.parametrize("region", regions.REGIONS, ids=lambda r: r.name)
def test_eval_freq_is_the_minimum_over_candidates(region):
    lim = region.limit.public.limit_mw_cm2
    for b in region.bands:
        e = lim(region.eval_freq_mhz(b))
        for lo, hi in b.segments:
            assert e <= lim(lo) + 1e-12 and e <= lim(hi) + 1e-12


def test_eval_freq_uses_a_breakpoint_inside_the_band():
    # Canada uncontrolled falls from 20 to 48 MHz, then is flat to 300 MHz:
    # 48 MHz is the lowest-frequency minimum of a 40-60 MHz band.
    r = regions.Region("t", (bands.band("t", 40, 60),), regions.CANADA.limit)
    assert r.eval_freq_mhz(r.bands[0]) == 48.0


def test_us_eval_freqs_unchanged():
    us = regions.US
    assert us.eval_freq_mhz(us.find("20 m")) == 14.35
    assert us.eval_freq_mhz(us.find("2 m")) == 144.0
    assert us.eval_freq_mhz(us.find("70 cm")) == 420.0


def test_spot_rows():
    assert regions.CANADA.find("1.25 m").segments == ((219.0, 220.0), (222.0, 225.0))
    assert regions.CANADA.find("70 cm").low_mhz == 430.0
    assert regions.AUSTRALIA.find("80 m").segments == ((3.5, 3.7), (3.776, 3.8))
    assert regions.AUSTRALIA.find("160 m").high_mhz == 1.875
    for name in ("60 m", "1.25 m", "33 cm"):
        with pytest.raises(KeyError):
            regions.AUSTRALIA.find(name)
    assert regions.CEPT.find("4 m").segments == ((69.9, 70.5),)
    assert regions.CEPT.find("2 m").high_mhz == 146.0
    assert regions.GERMANY.find("160 m").high_mhz == 2.0
    assert regions.GERMANY.find("9 cm").segments == ((3400.0, 3475.0),)
    assert regions.ITALY.find("160 m").segments == ((1.83, 1.85),)
    with pytest.raises(KeyError):
        regions.FRANCE.find("9 cm")


def test_in_bands():
    assert regions.US.in_bands(14.2)
    assert not regions.US.in_bands(3400.0)        # US 9 cm is gone
    assert regions.CANADA.in_bands(3400.0)
    assert not regions.AUSTRALIA.in_bands(5.36)    # no 60 m
