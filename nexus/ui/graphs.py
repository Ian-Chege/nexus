"""NEXUS SYSTEM MONITOR - live Matplotlib graph widget.

A themed Figure embedded in a CTkFrame. Series colors are given as Theme
attribute names ("accent", "accent2", ...) so the whole graph recolors
itself when the user switches themes. Updates use set_data + draw_idle,
which is fast and flicker-free at 0.5-5 s refresh intervals.
"""
from __future__ import annotations

import time

import numpy as np
import matplotlib
if "AGG" not in matplotlib.get_backend().upper():
    matplotlib.use("TkAgg")                     # embedding target is Tkinter
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter, MaxNLocator

import customtkinter as ctk


def _x_tick(ts, _pos) -> str:
    try:
        return time.strftime("%H:%M:%S", time.localtime(ts))
    except Exception:
        return ""


class LineGraph(ctk.CTkFrame):
    """Multi-series scrolling line graph with a neon glow style."""

    def __init__(self, master, theme, fonts, series: list[tuple[str, str]],
                 height: int = 240, y_range: tuple | None = None,
                 y_formatter=None, points: int = 120, **kw):
        super().__init__(master, fg_color=theme.card, corner_radius=14,
                         border_width=1, border_color=theme.border, **kw)
        self._theme = theme
        self._fonts = fonts
        self._series = list(series)             # [(label, theme_attr), ...]
        self._y_range = y_range
        self._y_fmt = y_formatter or (lambda v, p: f"{v:.0f}%")
        self._points = int(points)

        # legend row (kept above the figure so it never clips)
        legend = ctk.CTkFrame(self, fg_color="transparent")
        legend.pack(fill="x", padx=16, pady=(10, 0))
        self._legend_dots: dict[str, ctk.CTkFrame] = {}
        for label, _attr in self._series:
            dot = ctk.CTkFrame(legend, width=10, height=10, corner_radius=5,
                               fg_color=theme.accent)
            dot.pack(side="left", padx=(0, 5))
            self._legend_dots[label] = dot
            ctk.CTkLabel(legend, text=label, font=fonts["small"],
                         text_color=theme.muted).pack(side="left", padx=(0, 16))

        # figure
        self.figure = Figure(dpi=100, figsize=(4, max(1, height / 100.0)))
        self.ax = self.figure.add_subplot(111)
        self.figure.subplots_adjust(left=0.055, right=0.995, top=0.93, bottom=0.12)
        self._lines: dict[str, tuple] = {}
        for label, _attr in self._series:
            glow, = self.ax.plot([], [], lw=7, alpha=0.16, solid_capstyle="round")
            main, = self.ax.plot([], [], lw=2.0, solid_capstyle="round")
            self._lines[label] = (glow, main)

        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        widget = self.canvas.get_tk_widget()
        widget.configure(highlightthickness=0, bd=0)
        widget.pack(fill="both", expand=True, padx=8, pady=(0, 4))
        self._style_axes()

    # ------------------------------------------------------------------
    def _style_axes(self) -> None:
        t = self._theme
        self.figure.patch.set_facecolor(t.card)
        self.ax.set_facecolor(t.card)
        for side in ("top", "right"):
            self.ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            self.ax.spines[side].set_color(t.border)
        self.ax.grid(True, color=t.grid, lw=0.7, ls="--", alpha=0.6)
        self.ax.set_axisbelow(True)
        self.ax.tick_params(colors=t.muted, labelsize=8)
        for lbl in self.ax.get_xticklabels() + self.ax.get_yticklabels():
            lbl.set_color(t.muted)
        self.ax.xaxis.set_major_locator(MaxNLocator(5))
        self.ax.xaxis.set_major_formatter(FuncFormatter(_x_tick))
        self.ax.yaxis.set_major_locator(MaxNLocator(4))
        self.ax.yaxis.set_major_formatter(FuncFormatter(self._y_fmt))
        for label, attr in self._series:
            color = getattr(t, attr, t.accent)
            glow, main = self._lines[label]
            glow.set_color(color)
            main.set_color(color)
        for label, _attr in self._series:
            self._legend_dots[label].configure(fg_color=getattr(t, _attr, t.accent))
        self.ax.relim()

    # ------------------------------------------------------------------
    def update_data(self, series_data: dict, now: float, interval: float) -> None:
        """series_data: {label: [(timestamp, value_or_None), ...]}"""
        window = self._points * max(0.3, float(interval))
        for label, _attr in self._series:
            data = series_data.get(label) or []
            if data:
                xs = [p[0] for p in data]
                ys = np.array([np.nan if p[1] is None else float(p[1]) for p in data])
                ys = np.ma.masked_invalid(ys)
            else:
                xs, ys = [], np.array([])
            glow, main = self._lines[label]
            glow.set_data(xs, ys)
            main.set_data(xs, ys)

        self.ax.set_xlim(now - window, now + window * 0.02)
        if self._y_range:
            self.ax.set_ylim(*self._y_range)
        else:
            vals = [float(v) for data in series_data.values() for _t, v in data
                    if v is not None]
            top = max(vals) if vals else 1.0
            self.ax.set_ylim(0, max(top * 1.25, 1.0))
        self.canvas.draw_idle()

    # ------------------------------------------------------------------
    def apply_theme(self, theme) -> None:
        self._theme = theme
        self.configure(fg_color=theme.card, border_color=theme.border)
        self._style_axes()
        self.canvas.draw_idle()
