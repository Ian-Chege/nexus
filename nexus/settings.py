"""NEXUS SYSTEM MONITOR - settings persistence.

A single Settings dataclass instance is shared across the whole application.
Pages mutate fields and call save(); the monitoring loops read the fields on
every iteration so changes apply live without restarts.
"""
from __future__ import annotations

import dataclasses
import json
from dataclasses import asdict, dataclass

from .constants import (CONFIG_DIR, CONFIG_FILE, DEFAULT_APP_NAME,
                        MAX_INTERVAL, MIN_INTERVAL)
from .theme import DEFAULT_THEME, THEMES
from .utils import clamp


@dataclass
class Settings:
    app_name: str = DEFAULT_APP_NAME
    theme: str = DEFAULT_THEME
    refresh_interval: float = 1.0
    alerts_enabled: bool = True
    cpu_threshold: int = 90
    ram_threshold: int = 90

    # -- persistence --------------------------------------------------------
    def save(self) -> None:
        """Atomically write settings to disk (tmp file + rename)."""
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            tmp = CONFIG_FILE.with_suffix(".tmp")
            tmp.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
            tmp.replace(CONFIG_FILE)
        except OSError:
            pass  # never crash the UI over a failed write

    @classmethod
    def load(cls) -> "Settings":
        s = cls()
        try:
            raw = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return s
        if not isinstance(raw, dict):
            return s
        for f in dataclasses.fields(cls):
            if f.name in raw:
                setattr(s, f.name, raw[f.name])
        s.normalize()
        return s

    # -- validation ---------------------------------------------------------
    def normalize(self) -> None:
        self.app_name = (str(self.app_name or "").strip() or DEFAULT_APP_NAME)[:40]
        if self.theme not in THEMES:
            self.theme = DEFAULT_THEME
        try:
            self.refresh_interval = clamp(float(self.refresh_interval), MIN_INTERVAL, MAX_INTERVAL)
        except (TypeError, ValueError):
            self.refresh_interval = 1.0
        self.alerts_enabled = bool(self.alerts_enabled)
        try:
            self.cpu_threshold = int(clamp(int(self.cpu_threshold), 50, 99))
        except (TypeError, ValueError):
            self.cpu_threshold = 90
        try:
            self.ram_threshold = int(clamp(int(self.ram_threshold), 50, 99))
        except (TypeError, ValueError):
            self.ram_threshold = 90

    def reset(self) -> None:
        fresh = cls()
        for f in dataclasses.fields(cls):
            setattr(self, f.name, getattr(fresh, f.name))
        self.save()
