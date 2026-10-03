# About antennacalc

antennacalc estimates the minimum distance you should keep from an amateur radio
antenna to stay within the FCC's maximum permissible exposure (MPE) limits for RF
energy. It mirrors the [ARRL RF Exposure Calculator](https://www.arrl.org/rf-exposure-calculator)
and its results were checked against that calculator.

> **Estimate only.** Not valid for antennas within 20 cm (8 in) of a person. It uses
> the far-field model from FCC OET Bulletin 65, evaluates one transmitter at a time,
> and does not model near-field effects, lobes, or nearby reflecting structures.
> You are responsible for your station's compliance.

## Using the app

Fill in the form and press **Calculate**. Results appear for both exposure environments.

| Input | Meaning |
|-------|---------|
| Antenna type | Preset that fills in a typical gain and the ground-reflection default. Choose **Custom** to enter your own. |
| Frequency (MHz) | Operating frequency, 0.3 MHz to 100 GHz. Sets the FCC limit. |
| Transmitter power (W) | Power at the transmitter output. No default. |
| Feedline loss (dB) | Total loss between transmitter and antenna. Use **Estimate…** to compute it, or enter 0 for none. |
| Mode / duty cycle | How much of the time a transmission actually carries power (SSB 20%/50%, CW 40%, FM/AM/digital/carrier 100%). |
| Transmit time | Minutes transmitting, then minutes receiving, repeating. |
| Antenna gain (dBi) | Gain relative to an isotropic radiator. Dipole is 2.15 dBi. |
| Ground reflection | Include signals reflecting off the ground. More conservative; use for low or non-directional antennas. |

### Feedline loss estimator

Choose a cable (RG-58, RG-8X, RG-213, LMR-400, LMR-600, or a custom dB per 100 ft value),
its length, the SWR at the antenna, and any connector loss. Cable loss is interpolated at
your operating frequency from typical published figures; check your cable's data sheet.
**Use this loss** copies the total into the main form.

### Results

Each environment gets its own panel:

| Line | Meaning |
|------|---------|
| Transmitter power | What you entered. |
| Power at antenna | Transmitter power reduced by feedline loss. |
| Max allowed power density | FCC limit in mW/cm² at your frequency. |
| Time averaged power | Power at antenna × mode duty cycle × fraction of time transmitting. |
| EIRP | Time averaged power × antenna gain. |
| Minimum safe distance | Distance (feet and meters) at which exposure equals the limit. |

**Controlled** applies to people who know about the RF exposure and its effects (for
example, you and your household once instructed in RF safety); the averaging period is
6 minutes. **Uncontrolled** applies to everyone else, such as neighbors and the public;
the averaging period is 30 minutes.

## How it calculates

1. Look up the FCC limit for the frequency and environment (47 CFR 1.1310).
2. Time-average the power over the 6 or 30 minute period using your duty cycle and
   transmit/receive pattern. The transmit/receive cycle is repeated across the period,
   counting a partial final cycle, exactly as the ARRL calculator does.
3. EIRP = averaged power × 10^(gain/10).
4. Distance = √(G × EIRP / (π × limit)), where G is 0.64 with ground reflection and 0.25
   without (equivalent to a reflection factor of 2.56 on 1/(4πR²)).

## Source layout

| Path | Purpose |
|------|---------|
| `src/antennacalc/limits.py` | FCC MPE limit table. |
| `src/antennacalc/calc.py` | Exposure math and mode duty cycles (no GUI). |
| `src/antennacalc/feedline.py` | Cable loss, SWR loss, connector loss. |
| `src/antennacalc/antennas.py` | Antenna presets. |
| `src/antennacalc/gui.py` | Tkinter interface. |
| `run_antennacalc.py` | Entry script used when freezing with PyInstaller. |
| `tests/` | pytest suite, including cases captured from the ARRL calculator. |
| `.github/workflows/build.yml` | CI that tests and builds Windows, macOS and Linux apps. |

## References

- [ARRL RF Exposure Calculator](https://www.arrl.org/rf-exposure-calculator) and its [instructions](https://www.arrl.org/rf-exposure-calc-instructions)
- [ARRL: The Station Evaluation](https://www.arrl.org/fcc-rf-exposure-regulations-the-station-evaluation)
- FCC 47 CFR 1.1310 and OET Bulletin 65
