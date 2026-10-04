# antennacalc

Cross-platform (Windows, macOS, Linux) amateur radio RF exposure calculator. It estimates
the minimum safe distance from your antenna under the FCC MPE limits (47 CFR 1.1310,
OET Bulletin 65), for both controlled and uncontrolled environments. Results are checked
against the [ARRL RF Exposure Calculator](https://www.arrl.org/rf-exposure-calculator).

- Choose an antenna type (pre-fills gain and ground reflection) or enter your own gain
- Evaluate one or more US amateur bands (630 m through 4 mm), or a specific frequency
- Enter transmitter power, feedline loss, mode duty cycle and transmit time
- Built-in feedline loss estimator (cable type, length, SWR, connectors), recalculated per band
- Save a report as HTML, PDF, plain text or CSV, consolidated across all selected bands
- Python + Tkinter, no third-party runtime dependencies

## Download

Prebuilt apps for Windows, macOS and Linux are attached to each
[release](../../releases). They are unsigned, so your OS may warn on first launch; see
[docs/BUILDING.md](docs/BUILDING.md) for how to open them.

## Run from source

Requires Python 3.9+ with Tkinter (bundled on Windows and macOS python.org installers;
on Debian/Ubuntu install `python3-tk`).

```
pip install .
antennacalc
```

or without installing: `python -m antennacalc` with `src` on `PYTHONPATH`
(PowerShell: `$env:PYTHONPATH="src"`).

## Documentation

- [docs/ABOUT.md](docs/ABOUT.md): what each input and result means, how it is calculated, code layout
- [docs/BUILDING.md](docs/BUILDING.md): how to build the app from scratch on Windows, macOS and Linux

## Tests

```
pip install -r requirements-<windows|macos|linux>.txt
pip install -e .
pytest
```

## Disclaimer

This is an estimate for planning purposes only. It is not valid for antennas within
20 cm (8 in) of a person, does not model near-field effects, and evaluates one
transmitter at a time. You remain responsible for your station's compliance. See the
ARRL RF exposure resources and FCC OET Bulletin 65.

## License

[MIT](LICENSE)
