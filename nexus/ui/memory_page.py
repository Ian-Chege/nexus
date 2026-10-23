"""NEXUS SYSTEM MONITOR - Memory page (RAM graph, swap, details)."""
from __future__ import annotations

import customtkinter as ctk

from ..theme import Theme
from ..utils import fmt_bytes, severity_color
from .components import KeyRow
from .graphs import LineGraph


class MemoryPage(ctk.CTkFrame):
    def __init__(self, master, app, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self.app = app
        self._theme = app.theme
        self._fonts = app.fonts
        self._last = None

        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)

        # -- left: graph ------------------------------------------------------
        left = ctk.CTkFrame(self, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        left.grid_rowconfigure(0, weight=1)
        left.grid_columnconfigure(0, weight=1)

        self.graph = LineGraph(left, self._theme, self._fonts,
                               series=[("Memory", "accent2"), ("Swap", "warning")],
                               height=280, y_range=(0, 100),
                               points=app.display_points)
        self.graph.grid(row=0, column=0, sticky="nsew")

        # swap bar card under the graph
        self.swap_card = ctk.CTkFrame(left, fg_color=self._theme.card,
                                      corner_radius=14, border_width=1,
                                      border_color=self._theme.border)
        self.swap_card.grid(row=1, column=0, sticky="ew", pady=(14, 0))
        self.swap_lbl = ctk.CTkLabel(self.swap_card, text="SWAP", anchor="w",
                                     font=self._fonts["tiny"],
                                     text_color=self._theme.muted)
        self.swap_lbl.pack(anchor="w", padx=16, pady=(10, 2))
        self.swap_val = ctk.CTkLabel(self.swap_card, text="-", anchor="w",
                                     font=self._fonts["value"],
                                     text_color=self._theme.text)
        self.swap_val.pack(anchor="w", padx=16)
        self.swap_bar = ctk.CTkProgressBar(self.swap_card, height=8,
                                           corner_radius=4,
                                           fg_color=self._theme.track,
                                           progress_color=self._theme.warning)
        self.swap_bar.pack(fill="x", padx=16, pady=(6, 14))
        self.swap_bar.set(0)

        # -- right: details ----------------------------------------------------
        right = ctk.CTkFrame(self, fg_color=self._theme.card, width=300,
                             corner_radius=14, border_width=1,
                             border_color=self._theme.border)
        self._right = right
        right.grid(row=0, column=1, sticky="ns")
        right.grid_propagate(False)
        right.grid_columnconfigure(0, weight=1)

        self.head = ctk.CTkLabel(right, text="DETAILS", anchor="w",
                                 font=self._fonts["tiny"], text_color=self._theme.muted)
        self.head.pack(anchor="w", padx=16, pady=(14, 6))

        self.rows = {}
        for key, label in (("total", "Total"), ("used", "Used"),
                           ("available", "Available"), ("cached", "Cached"),
                           ("buffers", "Buffers"), ("proc", "Processes")):
            row = KeyRow(right, self._theme, self._fonts, label)
            row.pack(fill="x", padx=16, pady=4)
            self.rows[key] = row

        self.rule = ctk.CTkFrame(right, height=1, fg_color=self._theme.border)
        self.rule.pack(fill="x", padx=16, pady=(8, 8))

        for key, label in (("swap_total", "Swap Total"),
                           ("swap_used", "Swap Used")):
            row = KeyRow(right, self._theme, self._fonts, label)
            row.pack(fill="x", padx=16, pady=4)
            self.rows[key] = row

        self.mem_pct = ctk.CTkLabel(right, text="-", anchor="w",
                                    font=self._fonts["h1"],
                                    text_color=self._theme.text)
        self.mem_pct.pack(anchor="w", padx=16, pady=(10, 16))

    # ------------------------------------------------------------------
    def refresh(self, snap: dict, hist: dict, interval: float):
        self._last = (snap, hist, interval)
        t = self._theme
        if not snap:
            return

        self.graph.update_data({"Memory": hist.get("mem", []),
                                "Swap": hist.get("swap", [])},
                               snap.get("timestamp", 0), interval)

        self.rows["total"].set(fmt_bytes(snap.get("mem_total")))
        self.rows["used"].set(fmt_bytes(snap.get("mem_used")))
        self.rows["available"].set(fmt_bytes(snap.get("mem_available")))
        cached = snap.get("mem_cached")
        buffers = snap.get("mem_buffers")
        self.rows["cached"].set(fmt_bytes(cached) if cached is not None else "N/A")
        self.rows["buffers"].set(fmt_bytes(buffers) if buffers is not None else "N/A")
        self.rows["proc"].set(str(snap.get("proc_count", "-")))
        self.rows["swap_total"].set(fmt_bytes(snap.get("swap_total")))
        self.rows["swap_used"].set(fmt_bytes(snap.get("swap_used")))

        mem = snap.get("mem_percent")
        self.mem_pct.configure(text=f"{mem:.1f}%", text_color=severity_color(mem, t))

        swap_pct = snap.get("swap_percent")
        if swap_pct is None:
            self.swap_val.configure(text="N/A", text_color=t.muted)
            self.swap_bar.set(0)
        else:
            self.swap_val.configure(
                text=f"{swap_pct:.1f}%  \u00b7  {fmt_bytes(snap.get('swap_used'))}",
                text_color=severity_color(swap_pct, t))
            self.swap_bar.set(max(0.0, min(1.0, swap_pct / 100.0)))

    def apply_theme(self, theme: Theme):
        self._theme = theme
        self.graph.apply_theme(theme)
        self.swap_card.configure(fg_color=theme.card, border_color=theme.border)
        self.swap_lbl.configure(text_color=theme.muted)
        self.swap_val.configure(text_color=theme.text)
        self.swap_bar.configure(fg_color=theme.track)
        self.right_panel_recolor(theme)
        if self._last:
            self.refresh(*self._last)

    def right_panel_recolor(self, theme: Theme):
        if getattr(self, "_right", None) is not None:
            self._right.configure(fg_color=theme.card, border_color=theme.border)
            self.head.configure(text_color=theme.muted)
            self.rule.configure(fg_color=theme.border)
            self.mem_pct.configure(text_color=theme.text)
        for row in self.rows.values():
            row.apply_theme(theme)
