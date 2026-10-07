# About antennacalc

antennacalc estimates the minimum distance you should keep from an amateur radio
antenna to stay within the maximum permissible exposure (MPE) limits for RF energy in
your region: United States (FCC), Canada, Australia, Germany, France, Italy or Europe
(CEPT). [SOURCES.md](SOURCES.md) lists the document behind each region. For the United
States it mirrors the [ARRL RF Exposure Calculator](https://www.arrl.org/rf-exposure-calculator)
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
| Antenna gain (dBi) | Gain relative to an isotropic radiator. Dipole is 2.15 dBi. Choosing an antenna type fills in a typical gain, which you can overwrite. The multiband vertical preset (about 10 m / 33 ft, DX Commander style) uses 3 dBi as a typical figure. Yagi presets (HF 2-6 elements, 6.5-12 dBi; VHF/UHF 3-15+ elements, 7.5-17 dBi) are typical free-space figures and vary by design; use the manufacturer's number when you have it. |
| Ground reflection | Include signals reflecting off the ground. More conservative; use for low or non-directional antennas. |
| Frequency | One or more amateur bands of the selected region, **or** a specific frequency (see below). |

### Choosing frequencies

The **Frequency** box offers two mutually exclusive ways to choose what to evaluate:

- **Bands:** tick any of the selected region's amateur bands, or use **Select all** /
  **Clear**. Each band is evaluated at its *most conservative* frequency: the band edge
  with the lowest limit (the lower edge when the limit is flat across the band).
- **Specific frequency:** type a frequency in MHz (0.3 MHz to 100 GHz in the United States, 0.1 MHz to 300 GHz in every other region). Typing a frequency
  clears all band selections, and ticking a band clears the frequency.

With several bands selected, use the **Results for** list on the right to switch between
them. The results always show the frequency that was evaluated.

The table lists the United States bands. Each other region has its own band table, which
the app shows when you choose that region.

| Band | Range (MHz) | Band | Range (MHz) |
|------|-------------|------|-------------|
| 630 m | 0.472-0.479 | 2 m | 144-148 |
| 160 m | 1.8-2.0 | 1.25 m | 222-225 |
| 80 m | 3.5-4.0 | 70 cm | 420-450 |
| 60 m | 5.3305-5.4035 | 33 cm | 902-928 |
| 40 m | 7.0-7.3 | 23 cm | 1240-1300 |
| 30 m | 10.1-10.15 | 13 cm | 2300-2310 and 2390-2450 |
| 20 m | 14.0-14.35 | 5 cm | 5650-5925 |
| 17 m | 18.068-18.168 | 3 cm | 10000-10500 |
| 15 m | 21.0-21.45 | 1.2 cm | 24000-24250 |
| 12 m | 24.89-24.99 | 6 mm | 47000-47200 |
| 10 m | 28.0-29.7 | 4 mm | 76000-81000 |
| 6 m | 50-54 | | |

Each band range is the full allocation; individual modes and license classes may have
narrower segments. In the United States the 2200 m band is not included because it lies
below the 300 kHz lower limit of the FCC exposure table.

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
| Max allowed power density | The region's limit in mW/cm² at that frequency. |
| Time averaged power | Power at antenna × mode duty cycle × fraction of time transmitting. |
| EIRP | Time averaged power × antenna gain. |
| Minimum safe distance | Distance (feet and meters) at which exposure equals the limit. |

In the United States and Canada, **Controlled** applies to people who know about the RF
exposure and its effects (for example, you and your household once instructed in RF
safety), and **Uncontrolled** applies to everyone else, such as neighbors and the public.
The other regions set one general-public limit and no controlled tier, so their controlled
panel reads n/a.

The averaging period depends on the region. The United States uses 6 minutes (controlled)
and 30 minutes (uncontrolled). Canada uses 6 minutes up to 15 GHz and a shorter period
above that. Australia uses 30 minutes. Germany uses 6 minutes. France and Europe (CEPT)
use 6 minutes up to 10 GHz and a shorter period above that. Italy uses 24 hours
(1440 minutes). Each report states the period it used.

### Hints and help

Hover over any field label, input, button or result line for a short explanation. The
**Help** button opens a longer guide: how to use the app, controlled vs uncontrolled
limits, and what affects the answer. **Reset all** returns every input and result to
the starting defaults.

### Saving a report

After calculating, press **Save report…** and pick a file type in the save dialog:

- **HTML report** (`.html`): formatted and self-contained; open it in any web browser.
- **PDF document** (`.pdf`): the same content laid out for US Letter paper, with page
  numbers. It is generated by the app itself (no browser or extra software needed).
- **Plain text** (`.txt`): 72 columns wide, for email or a station log.
- **CSV spreadsheet** (`.csv`): one header row, then one row per band or frequency with
  every field: the station inputs (repeated on each row), the frequency details, and the
  limit, averaged power, EIRP and safe distances for both environments, plus a column
  flagging distances under 20 cm. Numbers carry no units; the units are in the column
  names. The file is UTF-8 with a byte-order mark so Excel reads it correctly.

Typing a file name that ends in `.html`, `.pdf`, `.txt` or `.csv` picks that format regardless of
the type selected. The confirmation that follows has a button (Show in Finder, Show in
Explorer, or Open folder on Linux) that opens the folder holding the saved file. The report
always covers everything you just calculated:

- **One band or frequency:** a header, the station inputs, and one results section.
- **Several bands:** one consolidated file with the station inputs, a summary table of
  minimum safe distances for every band (each row links to that band's section), then a
  full section for each band.

Each band section lists the frequency evaluated, power at the antenna, and color-coded
controlled (blue) and uncontrolled (orange) panels with one value per line and the minimum
safe distances in bold. The report ends with the disclaimer and flags any distance under
20 cm. The HTML uses inline styling only (no external files, scripts or network access),
and all text is escaped. The PDF shows the two environments side by side in one table per
band, keeps each band's section on a single page, and uses the standard Helvetica font, so
nothing is embedded; characters outside the Windows Latin-1 set print as `?`.

## How it calculates

1. Pick the frequency: the one you typed, or each selected band's most conservative frequency.
2. Look up the limit for that frequency and environment in the region's table (47 CFR 1.1310 in the US).
3. Reduce transmitter power by the feedline loss at that frequency.
4. Time-average the power over the region's averaging period (see Results) using your duty cycle and
   transmit/receive pattern. The transmit/receive cycle is repeated across the period,
   counting a partial final cycle, exactly as the ARRL calculator does.
5. EIRP = averaged power × 10^(gain/10).
6. Distance = √(G × EIRP / (π × limit)), where G is 0.64 with ground reflection and 0.25
   without (equivalent to a reflection factor of 2.56 on 1/(4πR²)).

## Source layout

| Path | Purpose |
|------|---------|
| `src/antennacalc/limits.py` | Exposure limits for every supported region, starting with the FCC MPE table. |
| `src/antennacalc/calc.py` | Exposure math and mode duty cycles (no GUI). |
| `src/antennacalc/bands.py` | Amateur band lists for every supported region. |
| `src/antennacalc/regions.py` | Binds each region's band list to its limits and picks each band's most conservative evaluation frequency. |
| `src/antennacalc/evaluate.py` | Evaluates a station at a frequency (loss, power, both environments). |
| `src/antennacalc/report.py` | Report content shared by every format; builds the HTML, text and CSV reports and picks the format to save. |
| `src/antennacalc/pdf_report.py` | Lays the report out as PDF pages. |
| `src/antennacalc/pdf.py` | Minimal PDF writer (standard library only). |
| `src/antennacalc/reveal.py` | Shows a saved file in Finder, Explorer, or the Linux file manager. |
| `src/antennacalc/feedline.py` | Cable loss, SWR loss, connector loss. |
| `src/antennacalc/antennas.py` | Antenna presets. |
| `src/antennacalc/gui.py` | Tkinter interface. |
| `src/antennacalc/helptext.py` | Tooltip text for each field and the Help window text. |
| `src/antennacalc/tooltip.py` | Small hover-tooltip helper. |
| `run_antennacalc.py` | Entry script used when freezing with PyInstaller. |
| `tests/` | pytest suite, including cases captured from the ARRL calculator. |
| `.github/workflows/build.yml` | CI that tests and builds Windows, macOS and Linux apps. |

## References

- [ARRL RF Exposure Calculator](https://www.arrl.org/rf-exposure-calculator) and its [instructions](https://www.arrl.org/rf-exposure-calc-instructions)
- [ARRL: The Station Evaluation](https://www.arrl.org/fcc-rf-exposure-regulations-the-station-evaluation)
- FCC 47 CFR 1.1310 and OET Bulletin 65
- [SOURCES.md](SOURCES.md) for the Canadian, Australian and European documents
