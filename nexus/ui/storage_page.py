"""NEXUS SYSTEM MONITOR - Storage page (partitions + disk I/O speeds)."""
from __future__ import annotations

import customtkinter as ctk

from ..theme import Theme
from ..utils import fmt_bytes, fmt_speed, severity_color
from .components import InfoCard


class _PartitionRow(ctk.CTkFrame):
    def __init__(self, master, theme: Theme, fonts, info: dict, **kw):
        super().__init__(master, fg_color=theme.card, corner_radius=12,
                         border_width=1, border_color=theme.border, **kw)
        self._theme = theme
        self._fonts = fonts
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)

        name = ctk.CTkFrame(self, fg_color="transparent")
        name.grid(row=0, column=0, sticky="w", padx=14, pady=10)
        self.dev_lbl = ctk.CTkLabel(name, text=info["device"], anchor="w",
                                    font=fonts["mono_small"],
                                    text_color=theme.text)
        self.dev_lbl.pack(anchor="w")
        self.mnt_lbl = ctk.CTkLabel(
            name, text=f"{info['mount']}  \u00b7  {info['fstype']}",
            anchor="w", font=fonts["tiny"], text_color=theme.muted)
        self.mnt_lbl.pack(anchor="w")

        mid = ctk.CTkFrame(self, fg_color="transparent")
        mid.grid(row=0, column=1, sticky="ew", padx=14)
        self.bar = ctk.CTkProgressBar(mid, height=8, corner_radius=4,
                                      fg_color=theme.track,
                                      progress_color=theme.accent)
        self.bar.pack(fill="x", pady=4)
        self.bar.set(0)

        self.use_lbl = ctk.CTkLabel(self, text="-", anchor="e", width=150,
                                    font=fonts["mono_small"],
                                    text_color=theme.text)
        self.use_lbl.grid(row=0, column=2, sticky="e", padx=14)

    def update_row(self, info: dict, theme: Theme):
        pct = info.get("percent", 0) or 0
        self.bar.set(max(0.0, min(1.0, pct / 100.0)))
        self.bar.configure(progress_color=severity_color(pct, theme))
        self.use_lbl.configure(
            text=f"{fmt_bytes(info.get('used'))} / {fmt_bytes(info.get('total'))}  "
                 f"({pct:.0f}%)",
            text_color=severity_color(pct, theme))

    def apply_theme(self, theme: Theme):
        self._theme = theme
        self.configure(fg_color=theme.card, border_color=theme.border)
        self.dev_lbl.configure(text_color=theme.text)
        self.mnt_lbl.configure(text_color=theme.muted)
        self.use_lbl.configure(text_color=theme.text)
        self.bar.configure(fg_color=theme.track)


class StoragePage(ctk.CTkFrame):
    def __init__(self, master, app, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self.app = app
        self._theme = app.theme
        self._fonts = app.fonts
        self._last = None
        self._rows: dict[tuple, _PartitionRow] = {}
        self._empty_lbl = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        for i in range(3):
            top.grid_columnconfigure(i, weight=1, uniform="stop")
        self.card_read = InfoCard(top, self._theme, self._fonts, "Disk Read")
        self.card_read.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        self.card_write = InfoCard(top, self._theme, self._fonts, "Disk Write")
        self.card_write.grid(row=0, column=1, sticky="nsew", padx=(0, 14))
        self.card_count = InfoCard(top, self._theme, self._fonts, "Partitions")
        self.card_count.grid(row=0, column=2, sticky="nsew")

        self.list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_frame.grid(row=1, column=0, sticky="nsew")

    # ------------------------------------------------------------------
    def refresh(self, snap: dict, hist: dict, interval: float):
        self._last = (snap, hist, interval)
        t = self._theme
        if not snap:
            return

        self.card_read.set(
            fmt_speed(snap.get("disk_read_bps")),
            "Aggregate read throughput" if snap.get("disk_read_bps") is not None
            else "Disk I/O counters not available")
        self.card_write.set(
            fmt_speed(snap.get("disk_write_bps")),
            "Aggregate write throughput" if snap.get("disk_write_bps") is not None
            else "Disk I/O counters not available")

        disks = snap.get("disks") or []
        self.card_count.set(str(len(disks)),
                            "Real physical / logical volumes")

        keys = {(d.get("device"), d.get("mount")) for d in disks}
        if keys != set(self._rows.keys()):
            for row in self._rows.values():
                row.destroy()
            self._rows.clear()
            for d in disks:
                key = (d.get("device"), d.get("mount"))
                row = _PartitionRow(self.list_frame, t, self._fonts, d)
                row.pack(fill="x", pady=4)
                self._rows[key] = row
        for d in disks:
            key = (d.get("device"), d.get("mount"))
            if key in self._rows:
                self._rows[key].update_row(d, t)

        # empty state
        if not disks:
            if self._empty_lbl is None:
                self._empty_lbl = ctk.CTkLabel(
                    self.list_frame, justify="center",
                    font=self._fonts["small"], text_color=t.muted,
                    text="No storage volumes detected on this system.")
                self._empty_lbl.pack(pady=40)
        elif self._empty_lbl is not None:
            self._empty_lbl.destroy()
            self._empty_lbl = None

    # ------------------------------------------------------------------
    def apply_theme(self, theme: Theme):
        self._theme = theme
        for card in (self.card_read, self.card_write, self.card_count):
            card.apply_theme(theme)
        for row in self._rows.values():
            row.apply_theme(theme)
        if self._last:
            self.refresh(*self._last)
