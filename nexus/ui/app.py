"""NEXUS SYSTEM MONITOR - application shell.

Owns the window, sidebar, header, pages, collector thread, alert engine and
toast notifications. The UI refresh loop runs through tk after() callbacks on
the main thread; the collector runs in its own daemon thread, so the
interface never blocks on system queries.
"""
from __future__ import annotations

import customtkinter as ctk

from .. import constants as C
from ..monitor import AlertEngine, SystemCollector
from ..theme import Theme, get_theme
from ..utils import MONO_FONT, UI_FONT
from .cpu_page import CpuPage
from .dashboard import DashboardPage
from .header import HeaderBar
from .memory_page import MemoryPage
from .network_page import NetworkPage
from .settings_page import SettingsPage
from .sidebar import Sidebar
from .storage_page import StoragePage
from .components import Toast

PAGE_CLASSES = {
    "dashboard": DashboardPage,
    "cpu": CpuPage,
    "memory": MemoryPage,
    "storage": StoragePage,
    "network": NetworkPage,
    "settings": SettingsPage,
}

TOAST_COLORS = {"alert": "danger", "info": "accent", "ok": "ok"}


class NexusApp(ctk.CTk):
    def __init__(self, settings):
        self.theme = get_theme(settings.theme)
        ctk.set_appearance_mode(self.theme.appearance)
        super().__init__(fg_color=self.theme.bg)

        self.settings = settings
        self.display_points = C.DISPLAY_POINTS
        self._after_id: str | None = None
        self._toasts: list[Toast] = []
        self._current_page = "dashboard"

        # -- fonts ----------------------------------------------------------
        self.fonts = {
            "h1": ctk.CTkFont(family=UI_FONT, size=24, weight="bold"),
            "h2": ctk.CTkFont(family=MONO_FONT, size=17, weight="bold"),
            "h3": ctk.CTkFont(family=UI_FONT, size=15, weight="bold"),
            "logo": ctk.CTkFont(family=UI_FONT, size=20, weight="bold"),
            "nav": ctk.CTkFont(family=UI_FONT, size=13, weight="bold"),
            "body": ctk.CTkFont(family=UI_FONT, size=14),
            "small": ctk.CTkFont(family=UI_FONT, size=12),
            "small_bold": ctk.CTkFont(family=UI_FONT, size=12, weight="bold"),
            "tiny": ctk.CTkFont(family=UI_FONT, size=11, weight="bold"),
            "value": ctk.CTkFont(family=MONO_FONT, size=26, weight="bold"),
            "mono": ctk.CTkFont(family=MONO_FONT, size=15, weight="bold"),
            "mono_small": ctk.CTkFont(family=MONO_FONT, size=12),
        }

        # -- window ----------------------------------------------------------
        self.title(settings.app_name)
        self.geometry("1280x800")
        self.minsize(1080, 680)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # -- engine ----------------------------------------------------------
        self.collector = SystemCollector(lambda: self.settings)
        self.alert_engine = AlertEngine()

        # -- layout ----------------------------------------------------------
        self.sidebar = Sidebar(self, self.theme, self.fonts,
                               settings.app_name, on_navigate=self.show_page)
        self.sidebar.grid(row=0, column=0, sticky="nsw")

        self.main = ctk.CTkFrame(self, fg_color="transparent")
        self.main.grid(row=0, column=1, sticky="nsew", padx=(6, 18))
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(1, weight=1)

        self.header = HeaderBar(self.main, self.theme, self.fonts,
                                hostname=self._hostname())
        self.header.grid(row=0, column=0, sticky="ew", pady=(8, 10))

        self.pages: dict[str, ctk.CTkFrame] = {}
        container = ctk.CTkFrame(self.main, fg_color="transparent")
        container.grid(row=1, column=0, sticky="nsew")
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)
        for key, cls in PAGE_CLASSES.items():
            page = cls(container, app=self)
            page.grid(row=0, column=0, sticky="nsew", pady=(0, 14))
            self.pages[key] = page

        self.show_page("dashboard")

        # -- run ---------------------------------------------------------------
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.collector.start()
        self.after(350, self._loop)

    # ------------------------------------------------------------------
    def _hostname(self) -> str:
        import platform
        return platform.node() or "localhost"

    # ------------------------------------------------------------------
    # navigation
    # ------------------------------------------------------------------
    def show_page(self, key: str):
        self._current_page = key
        # grid_remove guarantees exactly one mapped page (immune to any
        # stacking-order quirks of scrollable frames).
        for k, page in self.pages.items():
            if k == key:
                page.grid()
            else:
                page.grid_remove()
        self.sidebar.set_active(key)
        self.header.set_title(C.PAGE_TITLES.get(key, key))

    # ------------------------------------------------------------------
    # refresh loop (main thread only)
    # ------------------------------------------------------------------
    def _loop(self):
        self._update_once()
        try:
            interval = max(0.3, float(self.settings.refresh_interval))
        except Exception:
            interval = 1.0
        self._after_id = self.after(int(interval * 1000), self._loop)

    def _update_once(self):
        snap = self.collector.snapshot()
        if not snap:
            self.header.update_clock()
            return
        interval = max(0.3, float(self.settings.refresh_interval))
        hist = {k: self.collector.history(k, C.DISPLAY_POINTS)
                for k in ("cpu", "mem", "swap", "down", "up",
                          "cpu_temp", "gpu_temp")}
        self.header.update_clock()
        self.header.set_alert(self.alert_engine.above_threshold(snap, self.settings))
        page = self.pages.get(self._current_page)
        if page is not None:
            page.refresh(snap, hist, interval)
        for event in self.alert_engine.update(snap, self.settings, snap.get("timestamp", 0)):
            self.show_toast(event["title"], event["message"], "alert")

    # ------------------------------------------------------------------
    # theme / branding
    # ------------------------------------------------------------------
    def apply_theme(self, key: str):
        theme = get_theme(key)
        if theme.key == self.theme.key:
            return
        self.theme = theme
        self.settings.theme = key
        self.settings.save()
        ctk.set_appearance_mode(theme.appearance)
        self.configure(fg_color=theme.bg)
        self.sidebar.apply_theme(theme)
        self.header.apply_theme(theme)
        for page in self.pages.values():
            page.apply_theme(theme)

    def set_app_name(self, name: str):
        name = (name or "").strip() or C.DEFAULT_APP_NAME
        self.settings.app_name = name[:40]
        self.settings.save()
        self.sidebar.set_app_name(self.settings.app_name)
        self.title(self.settings.app_name)

    def reset_all_settings(self):
        old_name = self.settings.app_name
        self.settings.reset()
        self.alert_engine.reset()
        self.apply_theme(self.settings.theme)
        self.set_app_name(self.settings.app_name)
        self.show_toast("SETTINGS RESET", "All preferences were restored "
                        "to defaults.", "ok")

    # ------------------------------------------------------------------
    # toasts
    # ------------------------------------------------------------------
    def show_toast(self, title: str, message: str, kind: str = "info"):
        color = getattr(self.theme, TOAST_COLORS.get(kind, "accent"))
        if len(self._toasts) >= 4:
            self._dismiss_toast(self._toasts[0])
        toast = Toast(self, self.theme, self.fonts, title, message, color,
                      on_dismiss=self._dismiss_toast)
        toast._stack_y = 0
        self._toasts.append(toast)
        self._relayout_toasts()
        self.after(int(C.TOAST_SECONDS * 1000),
                   lambda: self._dismiss_toast(toast))

    def _dismiss_toast(self, toast: Toast):
        if toast in self._toasts:
            self._toasts.remove(toast)
            try:
                toast.destroy()
            except Exception:
                pass
            self._relayout_toasts()

    def _relayout_toasts(self):
        y = 26
        for toast in reversed(self._toasts):       # newest on top
            toast.set_stack_y(y)
            y += 96

    # ------------------------------------------------------------------
    def _on_close(self):
        try:
            if self._after_id is not None:
                self.after_cancel(self._after_id)
        except Exception:
            pass
        try:
            self.collector.stop()
        except Exception:
            pass
        self.destroy()
