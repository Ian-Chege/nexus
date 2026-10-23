"""NEXUS SYSTEM MONITOR - CPU page (graph, per-core bars, details)."""
from __future__ import annotations

import customtkinter as ctk

from ..theme import Theme
from ..utils import fmt_uptime, severity_color
from .components import CoreBar, InfoCard, MiniTable
from .graphs import LineGraph


class CpuPage(ctk.CTkFrame):
    def __init__(self, master, app, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self.app = app
        self._theme = app.theme
        self._fonts = app.fonts
        self._last = None
        self._core_bars: list[CoreBar] = []
        self._cores_built_for = -1

        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)

        # -- left: graph + per-core grid ------------------------------------
        left = ctk.CTkFrame(self, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        left.grid_rowconfigure(0, weight=1)
        left.grid_columnconfigure(0, weight=1)

        self.graph = LineGraph(left, self._theme, self._fonts,
                               series=[("CPU", "accent")],
                               height=260, y_range=(0, 100),
                               points=app.display_points)
        self.graph.grid(row=0, column=0, sticky="nsew", pady=(0, 14))

        self.cores_panel = ctk.CTkFrame(left, fg_color=self._theme.card,
                                        corner_radius=14, border_width=1,
                                        border_color=self._theme.border)
        self.cores_panel.grid(row=1, column=0, sticky="ew")
        self.cores_title = ctk.CTkLabel(
            self.cores_panel, text="PER-CORE USAGE", anchor="w",
            font=self._fonts["tiny"], text_color=self._theme.muted)
        self.cores_title.pack(anchor="w", padx=16, pady=(10, 4))
        self.cores_inner = ctk.CTkFrame(self.cores_panel, fg_color="transparent",
                                        height=118)
        self.cores_inner.pack(fill="x", padx=10, pady=(0, 10))
        self.cores_inner.grid_propagate(False)

        # -- right: info column ----------------------------------------------
        right = ctk.CTkFrame(self, fg_color="transparent", width=300)
        right.grid(row=0, column=1, sticky="ns")
        right.grid_propagate(False)
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(3, weight=1)

        self.card_clock = InfoCard(right, self._theme, self._fonts, "Clock Speed")
        self.card_clock.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        self.card_temp = InfoCard(right, self._theme, self._fonts, "Temperature")
        self.card_temp.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        self.card_load = InfoCard(right, self._theme, self._fonts, "Load Average")
        self.card_load.grid(row=2, column=0, sticky="ew", pady=(0, 12))

        self.proc_panel = ctk.CTkFrame(right, fg_color=self._theme.card,
                                       corner_radius=14, border_width=1,
                                       border_color=self._theme.border)
        self.proc_panel.grid(row=3, column=0, sticky="nsew")
        self.proc_title = ctk.CTkLabel(self.proc_panel, text="TOP PROCESSES",
                                       anchor="w", font=self._fonts["tiny"],
                                       text_color=self._theme.muted)
        self.proc_title.pack(anchor="w", padx=14, pady=(10, 2))
        self.proc_table = MiniTable(
            self.proc_panel, self._theme, self._fonts,
            columns=[("PID", "w"), ("Name", "w"), ("CPU", "e"), ("MEM", "e")])
        self.proc_table.pack(fill="x", padx=14, pady=(0, 10))

    # ------------------------------------------------------------------
    def refresh(self, snap: dict, hist: dict, interval: float):
        self._last = (snap, hist, interval)
        t = self._theme
        if not snap:
            return

        cpu = snap.get("cpu_percent") or 0.0
        self.graph.update_data({"CPU": hist.get("cpu", [])},
                               snap.get("timestamp", 0), interval)

        self._build_core_rows(snap.get("cpu_count", 0) or len(snap.get("cpu_per_core", [])))
        per_core = snap.get("cpu_per_core") or []
        for i, bar in enumerate(self._core_bars):
            if i < len(per_core):
                bar.set(per_core[i], severity_color(per_core[i], t))
            else:
                bar.set(0.0, t.track)

        freq, fmax = snap.get("cpu_freq_mhz"), snap.get("cpu_freq_max_mhz")
        if freq:
            sub = f"Base peak: {fmax:.0f} MHz" if fmax else "Current average clock"
            self.card_clock.set(f"{freq:.0f} MHz", sub)
        else:
            self.card_clock.set("N/A", "Frequency not exposed by this system")

        temp = snap.get("cpu_temp")
        if temp is not None:
            color = t.danger if temp >= 85 else t.warning if temp >= 70 else t.ok
            self.card_temp.set(f"{temp:.0f}\u00b0C", "CPU package sensor", color=color)
        else:
            self.card_temp.set("N/A", "No temperature sensor detected "
                                      "(normal on many Windows/VM systems)",
                               color=t.muted)

        load = snap.get("load_avg")
        if load:
            self.card_load.set(f"{load[0]:.2f}", f"1m: {load[0]:.2f}  \u00b7  "
                               f"5m: {load[1]:.2f}  \u00b7  15m: {load[2]:.2f}")
        else:
            self.card_load.set("N/A", "Load average not available")

        rows = []
        for p in snap.get("top_processes", []):
            rows.append((str(p.get("pid", "-")),
                         str(p.get("name", "-"))[:18],
                         f"{p.get('cpu_percent') or 0:.1f}%",
                         f"{p.get('memory_percent') or 0:.1f}%"))
        self.proc_table.set_rows(rows or [("-", "-", "-", "-")] * 6)

    # ------------------------------------------------------------------
    def _build_core_rows(self, n_cores: int):
        if n_cores == self._cores_built_for:
            return
        self._cores_built_for = n_cores
        for bar in self._core_bars:
            bar.destroy()
        self._core_bars.clear()
        per_row = 8 if n_cores > 6 else max(1, n_cores)
        rows = (n_cores + per_row - 1) // per_row
        if rows > 2:            # keep panel compact on very high core counts
            rows = 2
            n_cores = per_row * 2
        for i in range(n_cores):
            r, c = divmod(i, per_row)
            bar = CoreBar(self.cores_inner, self._theme, self._fonts, i)
            bar.grid(row=r, column=c, sticky="ew", padx=4, pady=4)
            self._core_bars.append(bar)
        for c in range(per_row):
            self.cores_inner.grid_columnconfigure(c, weight=1, uniform="core")

    # ------------------------------------------------------------------
    def apply_theme(self, theme: Theme):
        self._theme = theme
        self.graph.apply_theme(theme)
        self.cores_panel.configure(fg_color=theme.card, border_color=theme.border)
        self.cores_title.configure(text_color=theme.muted)
        self.proc_panel.configure(fg_color=theme.card, border_color=theme.border)
        self.proc_title.configure(text_color=theme.muted)
        for card in (self.card_clock, self.card_temp, self.card_load):
            card.apply_theme(theme)
        self.proc_table.apply_theme(theme)
        for bar in self._core_bars:
            bar.apply_theme(theme)
        if self._last:
            self.refresh(*self._last)
