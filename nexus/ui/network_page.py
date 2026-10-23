"""NEXUS SYSTEM MONITOR - Network page (speeds, graph, per-interface table)."""
from __future__ import annotations

import customtkinter as ctk

from ..theme import Theme
from ..utils import fmt_bytes, fmt_speed
from .components import InfoCard, MiniTable
from .graphs import LineGraph


class NetworkPage(ctk.CTkFrame):
    def __init__(self, master, app, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self.app = app
        self._theme = app.theme
        self._fonts = app.fonts
        self._last = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # -- speed cards -------------------------------------------------------
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        for i in range(4):
            top.grid_columnconfigure(i, weight=1, uniform="ncol")
        self.card_down = InfoCard(top, self._theme, self._fonts, "Download")
        self.card_down.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        self.card_up = InfoCard(top, self._theme, self._fonts, "Upload")
        self.card_up.grid(row=0, column=1, sticky="nsew", padx=(0, 14))
        self.card_recv = InfoCard(top, self._theme, self._fonts, "Total Received")
        self.card_recv.grid(row=0, column=2, sticky="nsew", padx=(0, 14))
        self.card_sent = InfoCard(top, self._theme, self._fonts, "Total Sent")
        self.card_sent.grid(row=0, column=3, sticky="nsew")

        # -- graph ---------------------------------------------------------------
        self.graph = LineGraph(self, self._theme, self._fonts,
                               series=[("Download", "accent"), ("Upload", "accent2")],
                               height=240, y_formatter=lambda v, p: fmt_speed(v),
                               points=app.display_points)
        self.graph.grid(row=1, column=0, sticky="nsew", pady=(0, 14))

        # -- interfaces table ------------------------------------------------------
        self.if_panel = ctk.CTkFrame(self, fg_color=self._theme.card,
                                     corner_radius=14, border_width=1,
                                     border_color=self._theme.border)
        self.if_panel.grid(row=2, column=0, sticky="ew")
        self.if_title = ctk.CTkLabel(self.if_panel, text="INTERFACES (BY TRAFFIC)",
                                     anchor="w", font=self._fonts["tiny"],
                                     text_color=self._theme.muted)
        self.if_title.pack(anchor="w", padx=14, pady=(10, 2))
        self.if_table = MiniTable(self.if_panel, self._theme, self._fonts,
                                  columns=[("Interface", "w"), ("Down", "e"),
                                           ("Up", "e"), ("Total", "e")])
        self.if_table.pack(fill="x", padx=14, pady=(0, 12))

    # ------------------------------------------------------------------
    def refresh(self, snap: dict, hist: dict, interval: float):
        self._last = (snap, hist, interval)
        if not snap:
            return

        down, up = snap.get("net_down_bps"), snap.get("net_up_bps")
        self.card_down.set(fmt_speed(down), "Live download speed")
        self.card_up.set(fmt_speed(up), "Live upload speed")
        self.card_recv.set(fmt_bytes(snap.get("net_total_recv")), "Since system boot")
        self.card_sent.set(fmt_bytes(snap.get("net_total_sent")), "Since system boot")

        self.graph.update_data({"Download": hist.get("down", []),
                                "Upload": hist.get("up", [])},
                               snap.get("timestamp", 0), interval)

        rows = []
        for iface in (snap.get("net_interfaces") or [])[:6]:
            rows.append((str(iface.get("name", "-"))[:16],
                         fmt_speed(iface.get("down_bps")),
                         fmt_speed(iface.get("up_bps")),
                         fmt_bytes((iface.get("recv") or 0)
                                   + (iface.get("sent") or 0))))
        self.if_table.set_rows(rows or [("-", "-", "-", "-")] * 6)

    # ------------------------------------------------------------------
    def apply_theme(self, theme: Theme):
        self._theme = theme
        for card in (self.card_down, self.card_up, self.card_recv, self.card_sent):
            card.apply_theme(theme)
        self.graph.apply_theme(theme)
        self.if_panel.configure(fg_color=theme.card, border_color=theme.border)
        self.if_title.configure(text_color=theme.muted)
        self.if_table.apply_theme(theme)
        if self._last:
            self.refresh(*self._last)
