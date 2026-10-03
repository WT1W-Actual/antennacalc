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
| Transmitter power (W) | Power at the transmitter output. No default. |
| Feedline loss (dB) | Total loss between transmitter and antenna. Use **Estimate…** to compute it, or enter a number (0 for none). |
| Mode / duty cycle | How much of the time a transmission actually carries power (SSB 20%/50%, CW 40%, FM/AM/digital/carrier 100%). |
| Transmit time | Minutes transmitting, then minutes receiving, repeating. |
| Antenna gain (dBi) | Gain relative to an isotropic radiator. Dipole is 2.15 dBi. |
| Ground reflection | Include signals reflecting off the ground. More conservative; use for low or non-directional antennas. |
| Frequency | One or more US amateur bands, **or** a specific frequency (see below). |

### Choosing frequencies

The **Frequency** box offers two mutually exclusive ways to choose what to evaluate:

- **Bands:** tick any of the US amateur bands (630 m through 4 mm), or use **Select all** /
  **Clear**. Each band is evaluated at its *most conservative* frequency: the band edge
  with the lowest FCC limit (the lower edge when the limit is flat across the band).
- **Specific frequency:** type a frequency in MHz (0.3 MHz to 100 GHz). Typing a frequency
  clears all band selections, and ticking a band clears the frequency.

With several bands selected, use the **Results for** list on the right to switch between
them. The results always show the frequency that was evaluated.

| Band | Range (MHz) | Band | Range (MHz) |
|------|-------------|------|-------------|
| 630 m | 0.472-0.479 | 2 m | 144-148 |
| 160 m | 1.8-2.0 | 1.25 m | 222-225 |
| 80 m | 3.5-4.0 | 70 cm | 420-450 |
| 60 m | 5.3305-5.4035 | 33 cm | 902-928 |
| 40 m | 7.0-7.3 | 23 cm | 1240-1300 |
| 30 m | 10.1-10.15 | 13 cm | 2300-2450 |
| 20 m | 14.0-14.35 | 9 cm | 3300-3500 |
| 17 m | 18.068-18.168 | 5 cm | 5650-5925 |
| 15 m | 21.0-21.45 | 3 cm | 10000-10500 |
| 12 m | 24.89-24.99 | 1.2 cm | 24000-24250 |
| 10 m | 28.0-29.7 | 6 mm | 47000-47200 |
| 6 m | 50-54 | 4 mm | 76000-81000 |

Each band range is the full allocation; individual modes and license classes may have
narrower segments. The 2200 m band is not included because it lies below the 300 kHz
lower limit of the FCC exposure table.

### Feedline loss estimator

Choose a cable (RG-58, RG-8X, RG-213, LMR-400, LMR-600, or a custom dB per 100 ft value),
its length, the SWR at the antenna, and any connector loss. Cable loss is interpolated from
typical published figures; check your cable's data sheet. **Use this feedline** stores the
cable description, and the main form shows "Per band: ...". The loss is then recalculated
**at each band or frequency you evaluate**, because coax loss changes with frequency.
Typing a number into the Feedline loss box instead switches back to one fixed value for
every frequency. The preview in the dialog uses the typed frequency or the first selected
band.

### Results

Each environment gets its own panel:

| Line | Meaning |
|------|---------|
| Transmitter power | What you entered. |
| Feedline loss | Loss at the frequency being shown. |
| Power at antenna | Transmitter power reduced by feedline loss. |
| Max allowed power density | FCC limit in mW/cm² at that frequency. |
| Time averaged power | Power at antenna × mode duty cycle × fraction of time transmitting. |
| EIRP | Time averaged power × antenna gain. |
| Minimum safe distance | Distance (feet and meters) at which exposure equals the limit. |

**Controlled** applies to people who know about the RF exposure and its effects (for
example, you and your household once instructed in RF safety); the averaging period is
6 minutes. **Uncontrolled** applies to everyone else, such as neighbors and the public;
the averaging period is 30 minutes.

### Saving a report

After calculating, press **Save report…** to write a formatted plain-text (`.txt`) file.
The report always covers everything you just calculated:

- **One band or frequency:** a header, the station inputs, and one results section.
- **Several bands:** one consolidated file with the station inputs, a summary table of
  minimum safe distances for every band, then a full section for each band with the
  controlled and uncontrolled results, one value per line.

The report is plain ASCII, so it opens cleanly in any editor. It ends with the
disclaimer, and flags any distance under 20 cm.

Example (abridged):

```
========================================================================
                       ANTENNA RF EXPOSURE REPORT
========================================================================
Generated:                        2026-10-03 15:40
Frequencies evaluated:            3

SUMMARY - MINIMUM SAFE DISTANCE (feet)
  Band                             MHz      Controlled    Uncontrolled
  20 m (14-14.35 MHz)            14.35         1.14 ft         1.98 ft
  2 m (144-148 MHz)                144         1.82 ft         3.14 ft
  70 cm (420-450 MHz)              420         1.11 ft         1.92 ft

BAND: 20 m (14-14.35 MHz)
Frequency evaluated:              14.35 MHz
...
CONTROLLED ENVIRONMENT (6 minute average)
  Max allowed power density:        4.37 mW/cm^2
  Minimum safe distance (feet):     1.14 ft
```

## How it calculates

1. Pick the frequency: the one you typed, or each selected band's most conservative frequency.
2. Look up the FCC limit for that frequency and environment (47 CFR 1.1310).
3. Reduce transmitter power by the feedline loss at that frequency.
4. Time-average the power over the 6 or 30 minute period using your duty cycle and
   transmit/receive pattern. The transmit/receive cycle is repeated across the period,
   counting a partial final cycle, exactly as the ARRL calculator does.
5. EIRP = averaged power × 10^(gain/10).
6. Distance = √(G × EIRP / (π × limit)), where G is 0.64 with ground reflection and 0.25
   without (equivalent to a reflection factor of 2.56 on 1/(4πR²)).

## Source layout

| Path | Purpose |
|------|---------|
| `src/antennacalc/limits.py` | FCC MPE limit table. |
| `src/antennacalc/calc.py` | Exposure math and mode duty cycles (no GUI). |
| `src/antennacalc/bands.py` | US amateur band list and each band's evaluation frequency. |
| `src/antennacalc/evaluate.py` | Evaluates a station at a frequency (loss, power, both environments). |
| `src/antennacalc/report.py` | Builds the plain-text report. |
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
