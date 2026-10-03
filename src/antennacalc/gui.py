"""Tkinter front end."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Callable, Optional

from . import calc, feedline
from .antennas import ANTENNAS, by_name
from .bands import BANDS, Band
from .evaluate import Evaluation, Station, evaluate
from .feedline import FeedlineConfig
from .report import build_report

RESULT_FIELDS = [
    ("tx", "Transmitter power"),
    ("loss", "Feedline loss"),
    ("ant", "Power at antenna"),
    ("limit", "Max allowed power density"),
    ("avg", "Time averaged power"),
    ("eirp", "EIRP"),
    ("ft", "Minimum safe distance (feet)"),
    ("m", "Minimum safe distance (meters)"),
]
BOLD = ("TkDefaultFont", 10, "bold")
BAND_COLUMNS = 4

DISCLAIMER = (
    "Estimate only (FCC OET Bulletin 65 far-field model). Not valid for antennas "
    "within 20 cm (8 in) of a person. Run it for each antenna and consider "
    "all transmitters."
)


class FeedlineDialog(tk.Toplevel):
    """Describe the feedline; loss is then calculated at each frequency evaluated."""

    def __init__(
        self,
        parent: tk.Misc,
        ref_freq: Callable[[], Optional[float]],
        on_use: Callable[[FeedlineConfig], None],
    ) -> None:
        super().__init__(parent)
        self.title("Feedline loss")
        self.resizable(False, False)
        self.ref_freq, self.on_use = ref_freq, on_use
        self.cable = tk.StringVar(value="RG-8X")
        self.custom = tk.StringVar(value="2.0")
        self.length = tk.StringVar(value="50")
        self.unit = tk.StringVar(value="ft")
        self.swr = tk.StringVar(value="1.0")
        self.conn = tk.StringVar(value="0.0")
        self.out = tk.StringVar()
        self._cfg: FeedlineConfig | None = None

        body = ttk.Frame(self, padding=12)
        body.grid()

        def row(r: int, label: str, w: tk.Widget) -> None:
            ttk.Label(body, text=label).grid(row=r, column=0, sticky="w", pady=3)
            w.grid(row=r, column=1, sticky="ew", pady=3, padx=(8, 0))

        row(1, "Cable type", ttk.Combobox(
            body, textvariable=self.cable, state="readonly",
            values=list(feedline.CABLES) + [feedline.CUSTOM]))
        row(2, "Custom loss (dB/100 ft)", ttk.Entry(body, textvariable=self.custom))
        lf = ttk.Frame(body)
        ttk.Entry(lf, textvariable=self.length, width=8).pack(side="left")
        ttk.Radiobutton(lf, text="ft", variable=self.unit, value="ft").pack(side="left", padx=4)
        ttk.Radiobutton(lf, text="m", variable=self.unit, value="m").pack(side="left")
        row(3, "Cable length", lf)
        row(4, "SWR at antenna", ttk.Entry(body, textvariable=self.swr))
        row(5, "Connector/other loss (dB)", ttk.Entry(body, textvariable=self.conn))
        ttk.Button(body, text="Calculate", command=self.calculate).grid(
            row=6, column=0, columnspan=2, pady=6)
        ttk.Label(body, textvariable=self.out, justify="left").grid(
            row=7, column=0, columnspan=2, sticky="w")
        self.use_btn = ttk.Button(body, text="Use this feedline",
                                  command=self.use, state="disabled")
        self.use_btn.grid(row=8, column=0, columnspan=2, pady=(8, 0))
        ttk.Label(body, text="Loss is recalculated at each band or frequency you evaluate. "
                  "Cable losses are typical published values; verify against "
                  "your cable's data sheet.", wraplength=320,
                  foreground="gray40").grid(row=9, column=0, columnspan=2, pady=(8, 0))

    def calculate(self) -> None:
        self.use_btn.state(["disabled"])
        try:
            cfg = FeedlineConfig(
                cable=self.cable.get(),
                length=float(self.length.get()),
                length_in_meters=self.unit.get() == "m",
                swr=float(self.swr.get()),
                connector_loss_db=float(self.conn.get()),
                custom_db_per_100ft=(
                    float(self.custom.get()) if self.cable.get() == feedline.CUSTOM else 0.0
                ),
            )
            f = self.ref_freq()
            if f is None and cfg.cable != feedline.CUSTOM:
                raise ValueError("Enter a frequency or select a band first for the preview")
            r = cfg.evaluate(f or 1.0)
        except ValueError as exc:
            self.out.set(f"Input error: {exc}")
            return
        self._cfg = cfg
        at = f" at {f:g} MHz" if f is not None else ""
        self.out.set(
            f"Preview{at}: {cfg.per_100ft(f or 1.0):.2f} dB/100 ft\n"
            f"Matched {r.matched_loss_db:.2f} dB + SWR {r.mismatch_loss_db:.2f} dB + "
            f"connectors {r.connector_loss_db:.2f} dB\n"
            f"Total loss: {r.total_loss_db:.2f} dB")
        self.use_btn.state(["!disabled"])

    def use(self) -> None:
        if self._cfg is not None:
            self.on_use(self._cfg)
            self.destroy()


class App(ttk.Frame):
    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master, padding=12)
        self.grid(sticky="nsew")
        master.columnconfigure(0, weight=1)
        master.rowconfigure(0, weight=1)

        self.antenna = tk.StringVar(value=ANTENNAS[0].name)
        self.freq = tk.StringVar()
        self.power = tk.StringVar()
        self.loss = tk.StringVar(value="0")
        self.mode = tk.StringVar(value=list(calc.MODE_DUTY_CYCLES)[0])
        self.tx_min = tk.StringVar(value="6")
        self.rx_min = tk.StringVar(value="4")
        self.gain = tk.StringVar(value=str(ANTENNAS[0].gain_dbi))
        self.ground = tk.BooleanVar(value=ANTENNAS[0].ground)
        self.band_vars = {b.name: tk.BooleanVar() for b in BANDS}
        self.shown = tk.StringVar()
        self.note = tk.StringVar()
        self.result = tk.StringVar()

        self.feedline_cfg: FeedlineConfig | None = None
        self._setting_loss = False
        self.station: Station | None = None
        self.evaluations: list[Evaluation] = []

        left = ttk.Frame(self)
        left.grid(row=0, column=0, sticky="n")
        right = ttk.Frame(self)
        right.grid(row=0, column=1, sticky="nsew", padx=(16, 0))
        self.columnconfigure(1, weight=1)
        self._build_inputs(left)
        self._build_results(right)

        self.freq.trace_add("write", self._freq_edited)
        self.loss.trace_add("write", self._loss_edited)
        self.save_btn.state(["disabled"])

    def _build_inputs(self, parent: ttk.Frame) -> None:
        def row(r: int, label: str, widget: tk.Widget) -> None:
            ttk.Label(parent, text=label).grid(row=r, column=0, sticky="w", pady=3)
            widget.grid(row=r, column=1, sticky="ew", pady=3, padx=(8, 0))

        ant = ttk.Combobox(
            parent, textvariable=self.antenna, state="readonly", width=40,
            values=[a.name for a in ANTENNAS],
        )
        ant.bind("<<ComboboxSelected>>", self._antenna_changed)
        row(0, "Antenna type", ant)
        row(1, "Transmitter power (W)", ttk.Entry(parent, textvariable=self.power))

        lf = ttk.Frame(parent)
        ttk.Entry(lf, textvariable=self.loss).pack(side="left", fill="x", expand=True)
        ttk.Button(lf, text="Estimate…", command=self._open_feedline).pack(
            side="left", padx=(6, 0))
        row(2, "Feedline loss (dB)", lf)

        row(3, "Mode / duty cycle", ttk.Combobox(
            parent, textvariable=self.mode, state="readonly",
            values=list(calc.MODE_DUTY_CYCLES)))

        t = ttk.Frame(parent)
        ttk.Entry(t, textvariable=self.tx_min, width=6).pack(side="left")
        ttk.Label(t, text=" min transmit, ").pack(side="left")
        ttk.Entry(t, textvariable=self.rx_min, width=6).pack(side="left")
        ttk.Label(t, text=" min receive").pack(side="left")
        row(4, "Transmit time", t)

        row(5, "Antenna gain (dBi)", ttk.Entry(parent, textvariable=self.gain))
        row(6, "", ttk.Checkbutton(parent, text="Include effect of ground reflection",
                                   variable=self.ground))

        fb = ttk.LabelFrame(parent, text="Frequency", padding=8)
        fb.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(8, 4))
        ttk.Label(fb, text="Select one or more US amateur bands:").grid(
            row=0, column=0, columnspan=BAND_COLUMNS, sticky="w")
        for i, b in enumerate(BANDS):
            ttk.Checkbutton(fb, text=b.name, variable=self.band_vars[b.name],
                            command=self._band_clicked).grid(
                row=1 + i // BAND_COLUMNS, column=i % BAND_COLUMNS, sticky="w", padx=(0, 10))
        last = 1 + (len(BANDS) - 1) // BAND_COLUMNS + 1
        bb = ttk.Frame(fb)
        bb.grid(row=last, column=0, columnspan=BAND_COLUMNS, sticky="w", pady=(4, 6))
        ttk.Button(bb, text="Select all", command=self._select_all).pack(side="left")
        ttk.Button(bb, text="Clear", command=self._clear_bands).pack(side="left", padx=6)
        ef = ttk.Frame(fb)
        ef.grid(row=last + 1, column=0, columnspan=BAND_COLUMNS, sticky="w")
        ttk.Label(ef, text="or a specific frequency (MHz):").pack(side="left")
        ttk.Entry(ef, textvariable=self.freq, width=12).pack(side="left", padx=6)

        ttk.Button(parent, text="Calculate", command=self.calculate).grid(
            row=8, column=0, columnspan=2, pady=8)

    def _build_results(self, parent: ttk.Frame) -> None:
        top = ttk.Frame(parent)
        top.grid(row=0, column=0, sticky="ew")
        ttk.Label(top, text="Results for:").pack(side="left")
        self.picker = ttk.Combobox(top, textvariable=self.shown, state="readonly", width=34)
        self.picker.pack(side="left", padx=6)
        self.picker.bind("<<ComboboxSelected>>", lambda _e: self._show())
        ttk.Label(parent, textvariable=self.note, foreground="gray30",
                  wraplength=400, justify="left").grid(row=1, column=0, sticky="w", pady=(4, 0))
        self.panels = {
            True: self._result_panel(parent, 2, "Controlled environment (6 min average)"),
            False: self._result_panel(parent, 3, "Uncontrolled environment (30 min average)"),
        }
        ttk.Label(parent, textvariable=self.result, foreground="firebrick",
                  wraplength=400).grid(row=4, column=0, sticky="w")
        self.save_btn = ttk.Button(parent, text="Save report…", command=self.save_report)
        self.save_btn.grid(row=5, column=0, pady=8)
        ttk.Label(parent, text=DISCLAIMER, wraplength=400, foreground="gray40").grid(
            row=6, column=0, sticky="w", pady=(6, 0))
        parent.columnconfigure(0, weight=1)

    def _result_panel(self, parent: tk.Misc, grid_row: int, title: str) -> dict[str, tk.StringVar]:
        box = ttk.LabelFrame(parent, text=title, padding=8)
        box.grid(row=grid_row, column=0, sticky="ew", pady=4)
        box.columnconfigure(1, weight=1)
        vars_: dict[str, tk.StringVar] = {}
        for i, (key, label) in enumerate(RESULT_FIELDS):
            vars_[key] = tk.StringVar(value="—")
            ttk.Label(box, text=label + ":").grid(row=i, column=0, sticky="w")
            ttk.Label(box, textvariable=vars_[key], font=BOLD).grid(
                row=i, column=1, sticky="e")
        return vars_

    # --- frequency selection -------------------------------------------------

    def selected_bands(self) -> list[Band]:
        return [b for b in BANDS if self.band_vars[b.name].get()]

    def _band_clicked(self) -> None:
        if self.selected_bands():
            self.freq.set("")

    def _select_all(self) -> None:
        for v in self.band_vars.values():
            v.set(True)
        self._band_clicked()

    def _clear_bands(self) -> None:
        for v in self.band_vars.values():
            v.set(False)

    def _freq_edited(self, *_: object) -> None:
        if self.freq.get().strip():
            self._clear_bands()

    def _ref_freq(self) -> Optional[float]:
        try:
            return float(self.freq.get())
        except ValueError:
            bands = self.selected_bands()
            return bands[0].eval_freq_mhz if bands else None

    # --- feedline ------------------------------------------------------------

    def _open_feedline(self) -> None:
        FeedlineDialog(self, self._ref_freq, self._set_feedline)

    def _set_feedline(self, cfg: FeedlineConfig) -> None:
        self.feedline_cfg = cfg
        self._setting_loss = True
        unit = "m" if cfg.length_in_meters else "ft"
        name = "custom" if cfg.cable == feedline.CUSTOM else cfg.cable
        self.loss.set(f"Per band: {name}, {cfg.length:g} {unit}")
        self._setting_loss = False

    def _loss_edited(self, *_: object) -> None:
        if not self._setting_loss:
            self.feedline_cfg = None

    def _antenna_changed(self, _event: object = None) -> None:
        a = by_name(self.antenna.get())
        if a.name != "Custom":
            self.gain.set(str(a.gain_dbi))
            self.ground.set(a.ground)

    # --- calculation ---------------------------------------------------------

    @staticmethod
    def _number(var: tk.StringVar, name: str) -> float:
        try:
            return float(var.get())
        except ValueError:
            raise ValueError(f"{name} must be a number") from None

    def _targets(self) -> list[tuple[float, Optional[Band]]]:
        if self.freq.get().strip():
            return [(self._number(self.freq, "Frequency"), None)]
        bands = self.selected_bands()
        if not bands:
            raise ValueError("Select at least one band or enter a frequency")
        return [(b.eval_freq_mhz, b) for b in bands]

    def _build_station(self) -> Station:
        if self.feedline_cfg is None:
            fixed = self._number(self.loss, "Feedline loss (dB)")
        else:
            fixed = 0.0
        return Station(
            tx_power_w=self._number(self.power, "Transmitter power"),
            gain_dbi=self._number(self.gain, "Antenna gain"),
            mode=self.mode.get(),
            duty_cycle=calc.MODE_DUTY_CYCLES[self.mode.get()],
            tx_minutes=self._number(self.tx_min, "Transmit minutes"),
            rx_minutes=self._number(self.rx_min, "Receive minutes"),
            ground=self.ground.get(),
            antenna=self.antenna.get(),
            fixed_loss_db=fixed,
            feedline=self.feedline_cfg,
        )

    def calculate(self) -> None:
        try:
            station = self._build_station()
            evals = [evaluate(station, f, band) for f, band in self._targets()]
        except ValueError as exc:
            self.station, self.evaluations = None, []
            self.picker["values"] = []
            self.shown.set("")
            self.note.set("")
            self._clear_panels()
            self.save_btn.state(["disabled"])
            self.result.set(f"Input error: {exc}")
            return
        self.station, self.evaluations = station, evals
        self.picker["values"] = [e.label for e in evals]
        self.shown.set(evals[0].label)
        self.save_btn.state(["!disabled"])
        self._show()

    def _clear_panels(self) -> None:
        for panel in self.panels.values():
            for v in panel.values():
                v.set("—")

    def _show(self) -> None:
        e = next((x for x in self.evaluations if x.label == self.shown.get()), None)
        if e is None or self.station is None:
            return
        for ctrl, r in ((True, e.controlled), (False, e.uncontrolled)):
            p = self.panels[ctrl]
            p["tx"].set(f"{self.station.tx_power_w:.4g} W")
            p["loss"].set(f"{e.loss_db:.2f} dB")
            p["ant"].set(f"{e.power_at_antenna_w:.4g} W")
            p["limit"].set(f"{r.limit_mw_cm2:.4g} mW/cm²")
            p["avg"].set(f"{r.avg_power_w:.4g} W")
            p["eirp"].set(f"{r.eirp_w:.4g} W")
            p["ft"].set(f"{r.safe_distance_ft:.2f} ft")
            p["m"].set(f"{r.safe_distance_m:.2f} m")
        if e.band:
            self.note.set(f"Evaluated at {e.freq_mhz:g} MHz, the most conservative "
                          f"frequency in the {e.band.range_text} band.")
        else:
            self.note.set(f"Evaluated at {e.freq_mhz:g} MHz.")
        self.result.set(
            "Distance is under 20 cm; results are not reliable that close."
            if e.too_close else ""
        )

    def save_report(self) -> None:
        if self.station is None or not self.evaluations:
            return
        path = filedialog.asksaveasfilename(
            parent=self, title="Save report", defaultextension=".txt",
            initialfile="antennacalc-report.txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(build_report(self.station, self.evaluations))
        except OSError as exc:
            messagebox.showerror("Save report", f"Could not save the report:\n{exc}", parent=self)
            return
        messagebox.showinfo("Save report", f"Report saved to:\n{path}", parent=self)


def main() -> None:
    root = tk.Tk()
    root.title("Antenna RF Exposure Calculator")
    App(root)
    root.mainloop()
