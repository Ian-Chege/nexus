"""NEXUS SYSTEM MONITOR - top header bar (title, alert dot, clock)."""
from __future__ import annotations

import customtkinter as ctk

from ..theme import Theme
from ..utils import clock_str


class HeaderBar(ctk.CTkFrame):
    def __init__(self, master, theme: Theme, fonts, hostname: str, **kw):
        super().__init__(master, fg_color="transparent", height=58, **kw)
        self._theme = theme
        self._fonts = fonts
        self.grid_columnconfigure(0, weight=1)

        self.title_lbl = ctk.CTkLabel(self, text="DASHBOARD", anchor="w",
                                      font=fonts["h1"], text_color=theme.text)
        self.title_lbl.grid(row=0, column=0, sticky="w", pady=(10, 0))

        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=0, column=1, sticky="e", pady=(10, 0))

        self.alert_dot = ctk.CTkLabel(right, text="\u25cf", font=fonts["h3"],
                                      text_color=theme.ok)
        self.alert_dot.pack(side="left", padx=(0, 12))

        chip = ctk.CTkFrame(right, corner_radius=16, fg_color=theme.card,
                            border_width=1, border_color=theme.border)
        chip.pack(side="left")
        self.host_lbl = ctk.CTkLabel(chip, text=hostname, font=fonts["small"],
                                     text_color=theme.muted)
        self.host_lbl.pack(side="left", padx=12, pady=4)

        self.clock_lbl = ctk.CTkLabel(right, text=clock_str(), width=88,
                                      anchor="e", font=fonts["mono_small"],
                                      text_color=theme.muted)
        self.clock_lbl.pack(side="left", padx=(14, 0))

    # ------------------------------------------------------------------
    def set_title(self, text: str):
        self.title_lbl.configure(text=text.upper())

    def set_alert(self, active: bool):
        self.alert_dot.configure(
            text_color=self._theme.danger if active else self._theme.ok)

    def update_clock(self):
        self.clock_lbl.configure(text=clock_str())

    def apply_theme(self, theme: Theme):
        self._theme = theme
        self.title_lbl.configure(text_color=theme.text)
        self.host_lbl.configure(text_color=theme.muted)
        self.clock_lbl.configure(text_color=theme.muted)
        self.alert_dot.configure(text_color=theme.ok)
        for child in self.winfo_children():
            if isinstance(child, ctk.CTkFrame) and child.cget("corner_radius") == 16:
                child.configure(fg_color=theme.card, border_color=theme.border)
