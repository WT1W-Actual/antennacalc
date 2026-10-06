"""User-facing hint text: short tooltips per field and the longer Help window."""

from __future__ import annotations

HINTS = {
    "region": (
        "Where the station is. Sets the amateur bands you can pick and the exposure "
        "limits the distances are calculated against."
    ),
    "bands": (
        "Tick one or more US amateur bands. Each band is evaluated at its most "
        "conservative frequency (the edge with the lowest allowed power density)."
    ),
    "freq": (
        "Evaluate one specific frequency in MHz (0.3 to 100000). Typing here "
        "clears the band selection, and ticking a band clears this."
    ),
    "antenna": (
        "Pick your antenna type. This fills in a typical gain and the ground "
        "reflection setting, which you can still change."
    ),
    "power": (
        "Transmitter output power in watts, measured at the radio. Enter the "
        "peak (PEP) power you actually run; there is no default."
    ),
    "loss": (
        "Total feedline loss in dB between the radio and the antenna. Use "
        "Estimate... to calculate it per band from cable type and length."
    ),
    "estimate": (
        "Estimate loss from the cable type, length, SWR and connectors. The "
        "loss is recalculated for every band you select."
    ),
    "mode": (
        "The mode sets the duty cycle: the fraction of the time you are really "
        "putting out full power. Speech on SSB averages far below peak; "
        "FM and digital modes are 100%."
    ),
    "tx": (
        "Your transmit/receive pattern over the averaging period. Exposure is "
        "averaged over 6 minutes (controlled) and 30 minutes (uncontrolled)."
    ),
    "gain": (
        "Antenna gain in dBi (relative to an isotropic radiator). A dipole is "
        "2.15 dBi. Use the manufacturer's figure if you have one."
    ),
    "ground": (
        "Adds the field from the beam reflecting off the ground (factor 0.64 "
        "instead of 0.25). Tick it if people can be in the beam path, such as "
        "low, rooftop or balcony antennas. Leave it off for a high tower."
    ),
    "calculate": "Calculate the minimum safe distances for the selected bands or frequency.",
    "reset": "Clear all inputs and results and return to the starting defaults.",
    "picker": "Choose which band or frequency to display when you calculated several.",
    "avg": (
        "Time Averaged Power: power at the antenna x mode duty cycle x the "
        "fraction of the averaging period spent transmitting."
    ),
    "eirp": (
        "Effective Isotropic Radiated Power: time averaged power x antenna gain."
    ),
    "dist": (
        "Stay at least this far from the antenna in the direction of its main "
        "beam. Estimate only; not valid within 20 cm (8 in) of the antenna."
    ),
    "save": "Save a report of every band or frequency you calculated (HTML, PDF, text or CSV).",
}

HELP_TITLE = "antennacalc help"

HELP_TEXT = """\
WHAT THIS DOES
Estimates the minimum safe distance from your antenna so that RF exposure stays \
within FCC limits (47 CFR 1.1310, OET Bulletin 65), the same method as the ARRL \
RF Exposure Calculator.

HOW TO USE IT
1. Choose one or more amateur bands, or type a specific frequency.
2. Pick your antenna type. Check the gain and ground reflection setting.
3. Enter your transmitter power, feedline loss, mode and transmit time.
4. Press Calculate. Use the "Results for" list to view each band, and Save \
report to keep them all.

CONTROLLED vs UNCONTROLLED
Controlled limits apply to people who know about and can control their exposure, \
such as licensees and their families on the property. They are averaged over \
6 minutes. Uncontrolled limits apply to the general public, such as neighbors, \
and are stricter, averaged over 30 minutes.

WHAT AFFECTS THE ANSWER
- Duty cycle: SSB speech averages well below peak power. FM, RTTY and digital \
modes are 100%.
- Transmit time: only the fraction of time you transmit counts toward the average.
- Gain: a high-gain beam concentrates power in one direction, so the distance \
in front of it is longer.
- Ground reflection: tick it when people can stand in the beam, as with low or \
rooftop antennas.

LIMITS OF THE ESTIMATE
This is a far-field estimate. It is not valid within 20 cm (8 in) of a person, \
nor for antennas very close to the area being evaluated. Run it for each antenna \
and consider all your transmitters. Verify cable loss and antenna gain against \
manufacturer data.
"""
