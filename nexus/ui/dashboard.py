"""NEXUS SYSTEM MONITOR - Dashboard page (overview of every subsystem)."""
from __future__ import annotations

import customtkinter as ctk

from ..theme import Theme
from ..utils import fmt_bytes, fmt_speed, fmt_uptime, severity_color, clock_str
from .components import InfoCard, StatCard
from .graphs import LineGraph


class DashboardPage(ctk.CTkFrame):
    def __init__(self, master, app, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self.app = app
        self._theme = app.theme
        self._fonts = app.fonts
        self._last = None

        for i in range(4):
            self.grid_columnconfigure(i, weight=1, uniform="dcol")
        self.grid_rowconfigure(1, weight=1)

        # -- top stat cards ---------------------------------------------------
        self.card_cpu = StatCard(self, self._theme, self._fonts, "CPU Usage")
        self.card_mem = StatCard(self, self._theme, self._fonts, "Memory")
        self.card_disk = StatCard(self, self._theme, self._fonts, "Disk (System)")
        self.card_net = StatCard(self, self._theme, self._fonts,
                                 "Network", bar=False)
        for i, card in enumerate((self.card_cpu, self.card_mem,
                                  self.card_disk, self.card_net)):
            card.grid(row=0, column=i, sticky="nsew", padx=(0, 14), pady=(0, 14))

        # -- main graph --------------------------------------------------------
        self.graph = LineGraph(self, self._theme, self._fonts,
                               series=[("CPU", "accent"), ("Memory", "accent2")],
                               height=250, y_range=(0, 100),
                               points=app.display_points)
        self.graph.grid(row=1, column=0, columnspan=4, sticky="nsew",
                        padx=(0, 14), pady=(0, 14))

        # -- info row -----------------------------------------------------------
        self.card_temp = InfoCard(self, self._theme, self._fonts, "CPU Temp")
        self.card_gpu = InfoCard(self, self._theme, self._fonts, "GPU")
        self.card_up = InfoCard(self, self._theme, self._fonts, "Uptime")
        self.card_sys = InfoCard(self, self._theme, self._fonts, "System")
        for i, card in enumerate((self.card_temp, self.card_gpu,
                                  self.card_up, self.card_sys)):
            card.grid(row=2, column=i, sticky="nsew", padx=(0, 14), pady=(0, 2))

    # ------------------------------------------------------------------
    def refresh(self, snap: dict, hist: dict, interval: float):
        self._last = (snap, hist, interval)
        t = self._theme
        if not snap:
            return

        cpu = snap.get("cpu_percent")
        self.card_cpu.set(f"{cpu:.1f}%",
                          f"{snap.get('cpu_count', '?')} threads"
                          + (f" \u00b7 {snap['cpu_freq_mhz']:.0f} MHz"
                             if snap.get("cpu_freq_mhz") else ""),
                          ratio=(cpu or 0) / 100.0,
                          color=severity_color(cpu, t))

        mem = snap.get("mem_percent")
        self.card_mem.set(f"{mem:.1f}%",
                          f"{fmt_bytes(snap.get('mem_used'))} / {fmt_bytes(snap.get('mem_total'))}",
                          ratio=(mem or 0) / 100.0,
                          color=severity_color(mem, t))

        sysdisk = self._system_disk(snap)
        if sysdisk:
            self.card_disk.set(f"{sysdisk['percent']:.0f}%",
                               f"{fmt_bytes(sysdisk['free'])} free of "
                               f"{fmt_bytes(sysdisk['total'])}",
                               ratio=sysdisk["percent"] / 100.0,
                               color=severity_color(sysdisk["percent"], t))
        else:
            self.card_disk.set("N/A", "No partitions detected", 0, t.muted)

        down, up = snap.get("net_down_bps"), snap.get("net_up_bps")
        self.card_net.set(f"{fmt_speed(down)}",
                          f"UP \u00b7 {fmt_speed(up)}  \u00b7  "
                          f"total {fmt_bytes(snap.get('net_total_recv'))}")

        ct, gt = snap.get("cpu_temp"), (snap.get("gpu") or {}).get("temp")
        self.card_temp.set(f"{ct:.0f}\u00b0C" if ct is not None else "N/A",
                           f"GPU: {gt:.0f}\u00b0C" if gt is not None
                           else "No GPU sensor found",
                           color=(t.danger if (ct or 0) >= 85 else
                                  t.warning if (ct or 0) >= 70 else
                                  t.ok if ct is not None else t.muted))

        gpu = snap.get("gpu")
        self.card_gpu.set(
            (gpu["name"][:26] if gpu else "N/A"),
            (f"{gpu['temp']:.0f}\u00b0C \u00b7 {gpu['util']:.0f}% util"
             if gpu and gpu.get("temp") is not None else "No NVIDIA GPU detected"))

        self.card_up.set(fmt_uptime(snap.get("uptime_s")),
                         f"Booted {clock_str(snap.get('boot_time'))}")

        self.card_sys.set(snap.get("hostname", "-"),
                          f"{snap.get('os_pretty', '?')} \u00b7 "
                          f"{snap.get('proc_count', '?')} processes")

        self.graph.update_data({"CPU": hist.get("cpu", []),
                                "Memory": hist.get("mem", [])},
                               snap.get("timestamp", 0), interval)

    # ------------------------------------------------------------------
    @staticmethod
    def _system_disk(snap: dict):
        disks = snap.get("disks") or []
        if not disks:
            return None
        import os
        target = "C:\\" if os.name == "nt" else "/"
        for d in disks:
            if d.get("mount") == target:
                return d
        return disks[0]

    def apply_theme(self, theme: Theme):
        self._theme = theme
        for card in (self.card_cpu, self.card_mem, self.card_disk,
                     self.card_net, self.card_temp, self.card_gpu,
                     self.card_up, self.card_sys):
            card.apply_theme(theme)
        self.graph.apply_theme(theme)
        if self._last:
            self.refresh(*self._last)
