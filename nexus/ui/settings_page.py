"""NEXUS SYSTEM MONITOR - Settings page.

Theme picker (9 hand-crafted palettes), custom application name, refresh
interval and alert configuration. Every change applies live and is saved
to ~/.nexus-monitor/settings.json immediately.

Widgets created through the _card/_muted/_text helpers are registered in
lists so apply_theme() can recolor the whole page reliably.
"""
from __future__ import annotations

import customtkinter as ctk

from .. import constants as C
from ..theme import THEMES, Theme
from ..utils import clamp
from .components import SectionTitle, ThemeCard


class SettingsPage(ctk.CTkScrollableFrame):
    def __init__(self, master, app, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self.app = app
        self._theme = app.theme
        self._fonts = app.fonts
        self._theme_cards: list[ThemeCard] = []
        self._cards: list[ctk.CTkFrame] = []
        self._muted: list[ctk.CTkLabel] = []
        self._texted: list[ctk.CTkLabel] = []
        self._entries: list[ctk.CTkEntry] = []
        self._sliders: list[ctk.CTkSlider] = []
        self._track_widgets: list = []      # entries/track-colored surfaces
        self._accent_buttons: list[ctk.CTkButton] = []
        self._outline_buttons: list[ctk.CTkButton] = []
        self._switches: list[ctk.CTkSwitch] = []
        self._rules: list[ctk.CTkFrame] = []
        self._titles: list[SectionTitle] = []
        self._reset_armed = False

        self.grid_columnconfigure(0, weight=1)

        # =================== APPEARANCE ===================
        self._section("Appearance").pack(fill="x", pady=(6, 10))
        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="x", pady=(0, 18))
        for i in range(3):
            grid.grid_columnconfigure(i, weight=1, uniform="themes")
        for i, theme_def in enumerate(THEMES.values()):
            card = ThemeCard(grid, self._fonts, theme_def,
                             active=(theme_def.key == app.settings.theme),
                             command=lambda k=theme_def.key: app.apply_theme(k))
            card.grid(row=i // 3, column=i % 3, sticky="nsew", padx=5, pady=5)
            self._theme_cards.append(card)

        # =================== INTERFACE ===================
        self._section("Interface").pack(fill="x", pady=(4, 10))
        name_card = self._card(self)
        name_card.pack(fill="x", pady=(0, 18))
        self._muted_lbl(name_card, "Application name").pack(
            anchor="w", padx=16, pady=(12, 4))
        row = ctk.CTkFrame(name_card, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(0, 6))
        self.name_entry = self._entry(row, app.settings.app_name,
                                      placeholder="e.g. NEXUS SYSTEM MONITOR")
        self.name_entry.pack(side="left")
        self.name_btn = self._accent_btn(row, "APPLY NAME", self._apply_name)
        self.name_btn.pack(side="left", padx=10)
        self._muted_lbl(name_card,
                        "Renames the sidebar brand, window title and header. "
                        "Empty input restores the default.").pack(
            anchor="w", padx=16, pady=(0, 12))

        # =================== PERFORMANCE ===================
        self._section("Performance").pack(fill="x", pady=(4, 10))
        perf_card = self._card(self)
        perf_card.pack(fill="x", pady=(0, 18))
        self.interval_lbl = self._text_lbl(
            perf_card, self._interval_text(app.settings.refresh_interval))
        self.interval_lbl.pack(anchor="w", padx=16, pady=(12, 4))
        self.interval_slider = self._slider(
            perf_card, C.MIN_INTERVAL, C.MAX_INTERVAL, 9, self._on_interval,
            accent=True)
        self.interval_slider.set(app.settings.refresh_interval)
        self.interval_slider.pack(fill="x", padx=16, pady=(2, 10))
        self._muted_lbl(perf_card,
                        "How often statistics refresh (graphs, cards, alerts). "
                        "Applies instantly.").pack(anchor="w", padx=16,
                                                   pady=(0, 12))

        # =================== ALERTS ===================
        self._section("Alerts").pack(fill="x", pady=(4, 10))
        alert_card = self._card(self)
        alert_card.pack(fill="x", pady=(0, 18))

        self.alert_switch = ctk.CTkSwitch(
            alert_card, text="Enable high usage alerts", command=self._on_alerts,
            font=self._fonts["body"], text_color=self._theme.text,
            progress_color=self._theme.accent, button_color=self._theme.text,
            onvalue=1, offvalue=0)
        self._switches.append(self.alert_switch)
        (self.alert_switch.select() if app.settings.alerts_enabled
         else self.alert_switch.deselect())
        self.alert_switch.pack(anchor="w", padx=16, pady=(14, 10))

        thr = ctk.CTkFrame(alert_card, fg_color="transparent")
        thr.pack(fill="x", padx=16, pady=(0, 6))
        thr.grid_columnconfigure(0, weight=1)
        thr.grid_columnconfigure(1, weight=1)

        self._muted_lbl(thr, "CPU threshold").grid(row=0, column=0, sticky="w")
        self._muted_lbl(thr, "RAM threshold").grid(row=0, column=1, sticky="w",
                                                   padx=(20, 0))
        self.cpu_thr_lbl = self._accent_lbl(thr, f"{app.settings.cpu_threshold}%")
        self.cpu_thr_lbl.grid(row=1, column=0, sticky="w", pady=(2, 0))
        self.ram_thr_lbl = self._accent_lbl(thr, f"{app.settings.ram_threshold}%")
        self.ram_thr_lbl.grid(row=1, column=1, sticky="w", padx=(20, 0),
                              pady=(2, 0))
        self.cpu_thr = self._slider(thr, 50, 99, 1, self._on_cpu_thr,
                                    color_attr="danger")
        self.cpu_thr.set(app.settings.cpu_threshold)
        self.cpu_thr.grid(row=2, column=0, sticky="ew", pady=(4, 10))
        self.ram_thr = self._slider(thr, 50, 99, 1, self._on_ram_thr,
                                    color_attr="danger")
        self.ram_thr.set(app.settings.ram_threshold)
        self.ram_thr.grid(row=2, column=1, sticky="ew", padx=(20, 0),
                          pady=(4, 10))

        self.test_btn = self._outline_btn(alert_card, "SEND TEST ALERT",
                                          self._test_alert, "danger")
        self.test_btn.pack(anchor="w", padx=16, pady=(0, 8))
        self._muted_lbl(alert_card,
                        "An alert fires after 3 consecutive samples above the "
                        "threshold, with a 60 s cooldown between "
                        "notifications.").pack(anchor="w", padx=16,
                                               pady=(0, 14))

        # =================== ABOUT ===================
        self._section("About & Data").pack(fill="x", pady=(4, 10))
        about_card = self._card(self)
        about_card.pack(fill="x", pady=(0, 10))
        self._muted_lbl(about_card,
                        f"NEXUS SYSTEM MONITOR v{C.APP_VERSION}  \u00b7  "
                        f"CustomTkinter + psutil + Matplotlib\n"
                        f"Config file: {C.CONFIG_FILE}").pack(
            anchor="w", padx=16, pady=(12, 8))
        self.reset_btn = self._outline_btn(about_card, "RESET ALL SETTINGS",
                                           self._reset_settings, "danger")
        self.reset_btn.pack(anchor="w", padx=16, pady=(0, 14))

    # ------------------------------------------------------------------
    # builders (register themed widgets for apply_theme)
    # ------------------------------------------------------------------
    def _section(self, text) -> SectionTitle:
        w = SectionTitle(self, self._theme, self._fonts, text)
        self._titles.append(w)
        return w

    def _card(self, master) -> ctk.CTkFrame:
        f = ctk.CTkFrame(master, fg_color=self._theme.card, corner_radius=14,
                         border_width=1, border_color=self._theme.border)
        self._cards.append(f)
        return f

    def _muted_lbl(self, master, text, **kw) -> ctk.CTkLabel:
        lbl = ctk.CTkLabel(master, text=text, anchor="w", justify="left",
                           font=self._fonts["small"],
                           text_color=self._theme.muted, **kw)
        self._muted.append(lbl)
        return lbl

    def _text_lbl(self, master, text) -> ctk.CTkLabel:
        lbl = ctk.CTkLabel(master, text=text, anchor="w",
                           font=self._fonts["body"],
                           text_color=self._theme.text)
        self._texted.append(lbl)
        return lbl

    def _accent_lbl(self, master, text) -> ctk.CTkLabel:
        lbl = ctk.CTkLabel(master, text=text, anchor="w", width=110,
                           font=self._fonts["mono_small"],
                           text_color=self._theme.accent)
        self._texted.append(lbl)
        lbl.configure(text_color=self._theme.accent)
        lbl._accent = True
        return lbl

    def _entry(self, master, value, placeholder) -> ctk.CTkEntry:
        e = ctk.CTkEntry(master, width=320, height=36,
                         font=self._fonts["body"],
                         text_color=self._theme.text,
                         fg_color=self._theme.track,
                         border_color=self._theme.border,
                         placeholder_text=placeholder)
        e.insert(0, value)
        self._track_widgets.append(e)
        return e

    def _accent_btn(self, master, text, command) -> ctk.CTkButton:
        b = ctk.CTkButton(master, text=text, width=130, height=36,
                          corner_radius=8, font=self._fonts["small_bold"],
                          fg_color=self._theme.accent,
                          hover_color=self._theme.accent2,
                          text_color=self._theme.bg, command=command)
        self._accent_buttons.append(b)
        return b

    def _outline_btn(self, master, text, command, color_attr) -> ctk.CTkButton:
        color = getattr(self._theme, color_attr)
        b = ctk.CTkButton(master, text=text, width=190, height=34,
                          corner_radius=8, font=self._fonts["small_bold"],
                          fg_color=self._theme.track, hover_color=self._theme.border,
                          border_width=1, border_color=color,
                          text_color=color, command=command)
        self._outline_buttons.append(b)
        return b

    def _slider(self, master, lo, hi, steps, command, accent=False,
                color_attr="accent") -> ctk.CTkSlider:
        color = self._theme.accent if accent else getattr(self._theme, color_attr)
        s = ctk.CTkSlider(master, from_=lo, to=hi, number_of_steps=steps,
                          command=command, fg_color=self._theme.track,
                          progress_color=color, button_color=color,
                          button_hover_color=self._theme.accent2)
        s._color_attr = "accent" if accent else color_attr
        self._sliders.append(s)
        return s

    # ------------------------------------------------------------------
    # callbacks
    # ------------------------------------------------------------------
    def _apply_name(self):
        name = self.name_entry.get().strip()
        self.app.set_app_name(name[:40])
        self._flash_saved()

    def _interval_text(self, v):
        return f"Refresh interval:  {float(v):.1f} s"

    def _on_interval(self, value):
        v = round(clamp(float(value), C.MIN_INTERVAL, C.MAX_INTERVAL), 1)
        self.app.settings.refresh_interval = v
        self.app.settings.save()
        self.interval_lbl.configure(text=self._interval_text(v))

    def _on_alerts(self):
        self.app.settings.alerts_enabled = bool(int(self.alert_switch.get()))
        self.app.alert_engine.reset()
        self.app.settings.save()

    def _on_cpu_thr(self, value):
        v = int(float(value))
        self.app.settings.cpu_threshold = v
        self.app.settings.save()
        self.cpu_thr_lbl.configure(text=f"{v}%")

    def _on_ram_thr(self, value):
        v = int(float(value))
        self.app.settings.ram_threshold = v
        self.app.settings.save()
        self.ram_thr_lbl.configure(text=f"{v}%")

    def _test_alert(self):
        self.app.show_toast("TEST ALERT",
                            "If you can read this, notifications are working.",
                            "alert")

    def _reset_settings(self):
        if not self._reset_armed:
            self._reset_armed = True
            self.reset_btn.configure(text="CLICK AGAIN TO CONFIRM")
            self.after(2500, self._disarm_reset)
            return
        self._disarm_reset()
        self.app.reset_all_settings()
        self._sync_from_settings()

    def _disarm_reset(self):
        self._reset_armed = False
        try:
            self.reset_btn.configure(text="RESET ALL SETTINGS")
        except Exception:
            pass

    def _sync_from_settings(self):
        s = self.app.settings
        self.interval_slider.set(s.refresh_interval)
        self.interval_lbl.configure(text=self._interval_text(s.refresh_interval))
        self.cpu_thr.set(s.cpu_threshold)
        self.cpu_thr_lbl.configure(text=f"{s.cpu_threshold}%")
        self.ram_thr.set(s.ram_threshold)
        self.ram_thr_lbl.configure(text=f"{s.ram_threshold}%")
        (self.alert_switch.select() if s.alerts_enabled
         else self.alert_switch.deselect())
        self.name_entry.delete(0, "end")
        self.name_entry.insert(0, s.app_name)

    def _flash_saved(self):
        self.name_btn.configure(text="SAVED")
        self.after(1200, lambda: self.name_btn.configure(text="APPLY NAME"))

    # ------------------------------------------------------------------
    def refresh(self, snap: dict, hist: dict, interval: float):
        """Settings is static - nothing to refresh per tick (no-op)."""

    def apply_theme(self, theme: Theme):
        self._theme = theme
        for w in self._titles:
            w.apply_theme(theme)
        for w in self._theme_cards:
            w.apply_theme(theme)
        for f in self._cards:
            f.configure(fg_color=theme.card, border_color=theme.border)
        for lbl in self._muted:
            lbl.configure(text_color=theme.muted)
        for lbl in self._texted:
            lbl.configure(text_color=getattr(lbl, "_accent", False)
                          and theme.accent or theme.text)
        for e in self._track_widgets:
            e.configure(fg_color=theme.track, border_color=theme.border,
                        text_color=theme.text)
        for s in self._sliders:
            color = getattr(theme, getattr(s, "_color_attr", "accent"), theme.accent)
            s.configure(fg_color=theme.track, progress_color=color,
                        button_color=color)
        for b in self._accent_buttons:
            b.configure(fg_color=theme.accent, hover_color=theme.accent2,
                        text_color=theme.bg)
        for b in self._outline_buttons:
            b.configure(fg_color=theme.track, hover_color=theme.border,
                        border_color=theme.danger, text_color=theme.danger)
        for sw in self._switches:
            sw.configure(text_color=theme.text, progress_color=theme.accent,
                         button_color=theme.text)
