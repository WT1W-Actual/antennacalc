import pytest

tk = pytest.importorskip("tkinter")

from antennacalc import gui, regions


@pytest.fixture
def app():
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("no display")
    root.withdraw()
    a = gui.App(root)
    yield a
    root.destroy()


def test_default_region_is_us(app):
    assert app.region is regions.US
    assert set(app.band_vars) == {b.name for b in regions.US.bands}


def test_switch_keeps_shared_selection_only(app):
    app._select_all()
    app.region_var.set("Australia")
    app._region_changed()
    assert set(app.band_vars) == {b.name for b in regions.AUSTRALIA.bands}
    chosen = {n for n, v in app.band_vars.items() if v.get()}
    us_names = {b.name for b in regions.US.bands}
    assert chosen == us_names & set(app.band_vars)
    assert "33 cm" not in app.band_vars


def test_switch_clears_results(app):
    app.power.set("100")
    app.band_vars["20 m"].set(True)
    app.calculate()
    assert app.evaluations
    app.region_var.set("Canada")
    app._region_changed()
    assert app.evaluations == [] and app.station is None
    assert "disabled" in app.save_btn.state()


def test_calculate_uses_region(app):
    app.region_var.set("Germany")
    app._region_changed()
    app.power.set("100")
    app.band_vars["2 m"].set(True)
    app.calculate()
    e = app.evaluations[0]
    assert e.region is regions.GERMANY and e.controlled is None
    assert app.panels[True]["ft"].get() == "n/a"
    assert "Not applicable" in app.na_text.get()


def test_feedline_reference_follows_region(app):
    app.region_var.set("Canada")
    app._region_changed()
    app.band_vars["70 cm"].set(True)
    assert app._ref_freq() == regions.CANADA.eval_freq_mhz(regions.CANADA.find("70 cm"))


def test_reset_keeps_region(app):
    app.region_var.set("France")
    app._region_changed()
    app.reset_all()
    assert app.region is regions.FRANCE


def test_out_of_range_frequency_is_an_input_error(app):
    app.power.set("100")
    app.freq.set("150000")
    app.calculate()
    assert app.result.get().startswith("Input error")


def test_region_tooltip_names_limit(app):
    app.region_var.set("Australia")
    app._region_changed()
    assert "ARPANSA" in app.region_tip.text


def test_no_tier_region_panel_explains_before_calculate(app):
    app.region_var.set("Germany")
    app._region_changed()
    assert app.evaluations == []
    assert app.na_text.get() == "Not applicable: Germany sets no controlled tier for amateur stations."
    assert app.panel_na[True].winfo_manager() == "grid"
    assert app.panel_na[False].winfo_manager() == ""
    app.region_var.set("United States")
    app._region_changed()
    assert app.na_text.get() == ""
    assert app.panel_na[True].winfo_manager() == ""


def test_freq_tooltip_is_region_neutral():
    from antennacalc.helptext import HINTS
    assert "100000" not in HINTS["freq"]
