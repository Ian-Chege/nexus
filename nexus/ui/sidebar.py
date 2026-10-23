"""NEXUS SYSTEM MONITOR - navigation sidebar."""
from __future__ import annotations

import customtkinter as ctk

from .. import constants as C
from ..theme import Theme


class Sidebar(ctk.CTkFrame):
    def __init__(self, master, theme: Theme, fonts, app_name: str,
                 on_navigate, **kw):
        super().__init__(master, width=232, corner_radius=0,
                         fg_color=theme.sidebar, **kw)
        self._theme = theme
        self._fonts = fonts
        self._on_navigate = on_navigate
        self._buttons: dict[str, ctk.CTkButton] = {}
        self._active = "dashboard"
        self.grid_propagate(False)
        self.grid_rowconfigure(2, weight=1)

        # -- logo ----------------------------------------------------------
        logo = ctk.CTkFrame(self, fg_color="transparent")
        logo.grid(row=0, column=0, sticky="ew", padx=20, pady=(24, 6))
        self.logo_lbl = ctk.CTkLabel(logo, text=app_name.upper(),
                                     font=fonts["logo"], justify="left",
                                     anchor="w", text_color=theme.accent,
                                     wraplength=190)
        self.logo_lbl.pack(anchor="w")
        sub = ctk.CTkFrame(logo, fg_color="transparent")
        sub.pack(anchor="w", pady=(2, 0))
        ctk.CTkLabel(sub, text="SYSTEM MONITOR", font=fonts["tiny"],
                     text_color=theme.muted).pack(side="left")
        ctk.CTkLabel(sub, text=f"  v{C.APP_VERSION}", font=fonts["tiny"],
                     text_color=theme.muted).pack(side="left")
        self.rule = ctk.CTkFrame(self, height=2, corner_radius=1,
                                 fg_color=theme.accent)
        self.rule.grid(row=1, column=0, sticky="ew", padx=20, pady=(4, 10))

        # -- navigation ------------------------------------------------------
        nav = ctk.CTkFrame(self, fg_color="transparent")
        nav.grid(row=2, column=0, sticky="new", padx=12, pady=(6, 0))
        for key, label in C.NAV_ITEMS:
            btn = ctk.CTkButton(
                nav, text=label, anchor="w", height=42, corner_radius=10,
                font=fonts["nav"], fg_color="transparent",
                hover_color=theme.card, text_color=theme.muted,
                command=lambda k=key: self._on_navigate(k),
            )
            btn.pack(fill="x", pady=2)
            self._buttons[key] = btn

        # -- status footer ----------------------------------------------------
        foot = ctk.CTkFrame(self, fg_color="transparent")
        foot.grid(row=3, column=0, sticky="ew", padx=20, pady=18)
        self.dot = ctk.CTkLabel(foot, text="\u25cf", font=fonts["small"],
                                text_color=theme.ok)
        self.dot.pack(side="left")
        ctk.CTkLabel(foot, text="  LIVE FEED", font=fonts["tiny"],
                     text_color=theme.muted).pack(side="left")

        self.set_active(self._active)

    # ------------------------------------------------------------------
    def set_active(self, key: str):
        self._active = key
        t = self._theme
        for k, btn in self._buttons.items():
            if k == key:
                btn.configure(fg_color=t.card, text_color=t.accent,
                              hover_color=t.card)
            else:
                btn.configure(fg_color="transparent", text_color=t.muted,
                              hover_color=t.card)

    def set_app_name(self, name: str):
        self.logo_lbl.configure(text=name.upper())

    def set_online(self, online: bool):
        self.dot.configure(text_color=self._theme.ok if online
                           else self._theme.danger)

    def apply_theme(self, theme: Theme):
        self._theme = theme
        self.configure(fg_color=theme.sidebar)
        self.logo_lbl.configure(text_color=theme.accent)
        self.rule.configure(fg_color=theme.accent)
        self.dot.configure(text_color=theme.ok)
        for child in self.winfo_children():
            if isinstance(child, ctk.CTkFrame):
                for lbl in child.winfo_children():
                    if isinstance(lbl, ctk.CTkLabel) and lbl.cget("font") is not None:
                        pass  # labels recolored below
        # recolor nav buttons + subtitle labels explicitly
        self.set_active(self._active)
        for child in self.winfo_children():
            if isinstance(child, ctk.CTkFrame):
                for widget in child.winfo_children():
                    if isinstance(widget, ctk.CTkFrame):
                        for sub in widget.winfo_children():
                            if isinstance(sub, ctk.CTkLabel):
                                sub.configure(text_color=theme.muted)
