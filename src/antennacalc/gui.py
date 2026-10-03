"""Tkinter front end."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from . import calc, feedline
from .antennas import ANTENNAS, by_name

RESULT_FIELDS = [
    ("tx", "Transmitter power"),
    ("ant", "Power at antenna"),
    ("limit", "Max allowed power density"),
    ("avg", "Time averaged power"),
    ("eirp", "EIRP"),
    ("ft", "Minimum safe distance (feet)"),
    ("m", "Minimum safe distance (meters)"),
]
BOLD = ("TkDefaultFont", 10, "bold")

DISCLAIMER = (
    "Estimate only (FCC OET Bulletin 65 far-field model). Not valid for antennas "
    "within 20 cm (8 in) of a person. Run it for each band/antenna and consider "
    "all transmitters."
)


class FeedlineDialog(tk.Toplevel):
    """Estimate total feedline loss (dB) from cable, length, SWR and connectors."""

    def __init__(self, parent: tk.Misc, freq: tk.StringVar, loss_out: tk.StringVar) -> None:
        super().__init__(parent)
        self.title("Feedline loss")
        self.resizable(False, False)
        self.freq, self.loss_out = freq, loss_out
        self.cable = tk.StringVar(value="RG-8X")
        self.custom = tk.StringVar(value="2.0")
        self.length = tk.StringVar(value="50")
        self.unit = tk.StringVar(value="ft")
        self.swr = tk.StringVar(value="1.0")
        self.conn = tk.StringVar(value="0.0")
        self.out = tk.StringVar()
        self._loss_db: float | None = None

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
        self.use_btn = ttk.Button(body, text="Use this loss",
                                  command=self.use, state="disabled")
        self.use_btn.grid(row=8, column=0, columnspan=2, pady=(8, 0))
        ttk.Label(body, text="Cable losses are typical published values; verify against "
                  "your cable's data sheet.", wraplength=320,
                  foreground="gray40").grid(row=9, column=0, columnspan=2, pady=(8, 0))

    def calculate(self) -> None:
        self.use_btn.state(["disabled"])
        try:
            f = float(self.freq.get())
            if self.cable.get() == feedline.CUSTOM:
                per100 = float(self.custom.get())
            else:
                per100 = feedline.loss_per_100ft(self.cable.get(), f)
            r = feedline.power_at_antenna(
                1.0, float(self.length.get()), per100,
                float(self.swr.get()), float(self.conn.get()),
                length_in_meters=self.unit.get() == "m")
        except ValueError as exc:
            self.out.set(f"Input error: {exc}")
            return
        self._loss_db = r.total_loss_db
        self.out.set(
            f"Cable loss at {f:g} MHz: {per100:.2f} dB/100 ft\n"
            f"Matched {r.matched_loss_db:.2f} dB + SWR {r.mismatch_loss_db:.2f} dB + "
            f"connectors {r.connector_loss_db:.2f} dB\n"
            f"Total loss: {r.total_loss_db:.2f} dB")
        self.use_btn.state(["!disabled"])

    def use(self) -> None:
        if self._loss_db is not None:
            self.loss_out.set(f"{self._loss_db:.2f}")
            self.destroy()


class App(ttk.Frame):
    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master, padding=12)
        self.grid(sticky="nsew")
        master.columnconfigure(0, weight=1)
        master.rowconfigure(0, weight=1)

        self.antenna = tk.StringVar(value=ANTENNAS[0].name)
        self.freq = tk.StringVar(value="14.2")
        self.power = tk.StringVar()
        self.loss = tk.StringVar(value="0")
        self.mode = tk.StringVar(value=list(calc.MODE_DUTY_CYCLES)[0])
        self.tx_min = tk.StringVar(value="6")
        self.rx_min = tk.StringVar(value="4")
        self.gain = tk.StringVar(value=str(ANTENNAS[0].gain_dbi))
        self.ground = tk.BooleanVar(value=ANTENNAS[0].ground)
        self.result = tk.StringVar()

        def row(r: int, label: str, widget: tk.Widget) -> None:
            ttk.Label(self, text=label).grid(row=r, column=0, sticky="w", pady=3)
            widget.grid(row=r, column=1, sticky="ew", pady=3, padx=(8, 0))

        ant = ttk.Combobox(
            self, textvariable=self.antenna, state="readonly", width=44,
            values=[a.name for a in ANTENNAS],
        )
        ant.bind("<<ComboboxSelected>>", self._antenna_changed)
        row(0, "Antenna type", ant)
        row(1, "Frequency (MHz)", ttk.Entry(self, textvariable=self.freq))
        row(2, "Transmitter power (W)", ttk.Entry(self, textvariable=self.power))
        row(3, "Feedline loss (dB)", self._loss_row())
        row(4, "Mode / duty cycle", ttk.Combobox(
            self, textvariable=self.mode, state="readonly",
            values=list(calc.MODE_DUTY_CYCLES)))

        t = ttk.Frame(self)
        ttk.Entry(t, textvariable=self.tx_min, width=6).pack(side="left")
        ttk.Label(t, text=" min transmit, ").pack(side="left")
        ttk.Entry(t, textvariable=self.rx_min, width=6).pack(side="left")
        ttk.Label(t, text=" min receive").pack(side="left")
        row(5, "Transmit time", t)

        row(6, "Antenna gain (dBi)", ttk.Entry(self, textvariable=self.gain))

        row(7, "", ttk.Checkbutton(self, text="Include effect of ground reflection",
                                   variable=self.ground))
        ttk.Button(self, text="Calculate", command=self.calculate).grid(
            row=8, column=0, columnspan=2, pady=8)
        self.panels = {
            True: self._result_panel(9, "Controlled environment (6 min average)"),
            False: self._result_panel(10, "Uncontrolled environment (30 min average)"),
        }
        ttk.Label(self, textvariable=self.result, foreground="firebrick",
                  wraplength=420).grid(row=11, column=0, columnspan=2, sticky="w")
        ttk.Label(self, text=DISCLAIMER, wraplength=420, foreground="gray40").grid(
            row=12, column=0, columnspan=2, sticky="w", pady=(10, 0))
        self.columnconfigure(1, weight=1)

    def _result_panel(self, grid_row: int, title: str) -> dict[str, tk.StringVar]:
        box = ttk.LabelFrame(self, text=title, padding=8)
        box.grid(row=grid_row, column=0, columnspan=2, sticky="ew", pady=4)
        box.columnconfigure(1, weight=1)
        vars_: dict[str, tk.StringVar] = {}
        for i, (key, label) in enumerate(RESULT_FIELDS):
            vars_[key] = tk.StringVar(value="—")
            ttk.Label(box, text=label + ":").grid(row=i, column=0, sticky="w")
            ttk.Label(box, textvariable=vars_[key], font=BOLD).grid(
                row=i, column=1, sticky="e")
        return vars_

    def _loss_row(self) -> ttk.Frame:
        f = ttk.Frame(self)
        ttk.Entry(f, textvariable=self.loss).pack(side="left", fill="x", expand=True)
        ttk.Button(f, text="Estimate…", command=self._open_feedline).pack(
            side="left", padx=(6, 0))
        return f

    def _open_feedline(self) -> None:
        FeedlineDialog(self, self.freq, self.loss)

    def _antenna_changed(self, _event: object = None) -> None:
        a = by_name(self.antenna.get())
        if a.name != "Custom":
            self.gain.set(str(a.gain_dbi))
            self.ground.set(a.ground)

    @staticmethod
    def _number(var: tk.StringVar, name: str) -> float:
        try:
            return float(var.get())
        except ValueError:
            raise ValueError(f"{name} must be a number") from None

    def calculate(self) -> None:
        results = {}
        try:
            tx_w = self._number(self.power, "Transmitter power")
            loss_db = self._number(self.loss, "Feedline loss")
            if tx_w <= 0:
                raise ValueError("Transmitter power must be greater than zero")
            if loss_db < 0:
                raise ValueError("Feedline loss cannot be negative")
            ant_w = tx_w / 10 ** (loss_db / 10)
            freq = self._number(self.freq, "Frequency")
            gain = self._number(self.gain, "Antenna gain")
            tx_min = self._number(self.tx_min, "Transmit minutes")
            rx_min = self._number(self.rx_min, "Receive minutes")
            for ctrl in (True, False):
                results[ctrl] = calc.calculate(
                    freq_mhz=freq,
                    power_w=ant_w,
                    gain_dbi=gain,
                    duty_cycle=calc.MODE_DUTY_CYCLES[self.mode.get()],
                    tx_minutes=tx_min,
                    rx_minutes=rx_min,
                    controlled=ctrl,
                    ground=self.ground.get(),
                )
        except ValueError as exc:
            for panel in self.panels.values():
                for v in panel.values():
                    v.set("—")
            self.result.set(f"Input error: {exc}")
            return
        close = False
        for ctrl, r in results.items():
            p = self.panels[ctrl]
            p["tx"].set(f"{tx_w:.4g} W")
            p["ant"].set(f"{ant_w:.4g} W")
            p["limit"].set(f"{r.limit_mw_cm2:.4g} mW/cm²")
            p["avg"].set(f"{r.avg_power_w:.4g} W")
            p["eirp"].set(f"{r.eirp_w:.4g} W")
            p["ft"].set(f"{r.safe_distance_ft:.2f} ft")
            p["m"].set(f"{r.safe_distance_m:.2f} m")
            close = close or r.safe_distance_m * 100 < calc.MIN_DISTANCE_CM
        self.result.set(
            "Distance is under 20 cm; results are not reliable that close." if close else ""
        )


def main() -> None:
    root = tk.Tk()
    root.title("Antenna RF Exposure Calculator")
    App(root)
    root.mainloop()
