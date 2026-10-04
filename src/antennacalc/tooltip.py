"""Small hover tooltip for Tkinter widgets."""

from __future__ import annotations

import tkinter as tk


class Tooltip:
    def __init__(self, widget: tk.Misc, text: str, delay_ms: int = 500, wrap: int = 320) -> None:
        self.widget, self.text, self.delay, self.wrap = widget, text, delay_ms, wrap
        self._after: str | None = None
        self._tip: tk.Toplevel | None = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")
        widget.bind("<Destroy>", self._hide, add="+")

    def _schedule(self, _event: object = None) -> None:
        self._hide()
        self._after = self.widget.after(self.delay, self._show)

    def _show(self) -> None:
        self._after = None
        if self._tip is not None:
            return
        tip = tk.Toplevel(self.widget)
        tip.wm_overrideredirect(True)
        tip.attributes("-topmost", True)
        tk.Label(tip, text=self.text, justify="left", wraplength=self.wrap,
                 background="#ffffe0", foreground="black", relief="solid",
                 borderwidth=1, padx=6, pady=4).pack()
        x = self.widget.winfo_rootx() + 12
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        tip.update_idletasks()
        x = max(0, min(x, tip.winfo_screenwidth() - tip.winfo_reqwidth() - 4))
        if y + tip.winfo_reqheight() > tip.winfo_screenheight():
            y = self.widget.winfo_rooty() - tip.winfo_reqheight() - 4
        tip.wm_geometry(f"+{x}+{y}")
        self._tip = tip

    def _hide(self, _event: object = None) -> None:
        if self._after is not None:
            try:
                self.widget.after_cancel(self._after)
            except tk.TclError:
                pass
            self._after = None
        if self._tip is not None:
            self._tip.destroy()
            self._tip = None
