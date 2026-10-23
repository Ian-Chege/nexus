"""NEXUS SYSTEM MONITOR - alert engine (pure logic, fully unit-testable).

Fires an alert event only when a metric stays above its threshold for
ALERT_STREAK_NEEDED consecutive samples, and never more often than
ALERT_COOLDOWN_S seconds per kind. All UI work happens outside this module.
"""
from __future__ import annotations

from .. import constants as C


class AlertEngine:
    def __init__(self, streak_needed: int = C.ALERT_STREAK_NEEDED,
                 cooldown: float = C.ALERT_COOLDOWN_S):
        self.streak_needed = int(streak_needed)
        self.cooldown = float(cooldown)
        self._streaks = {"CPU": 0, "RAM": 0}
        self._last_fired = {"CPU": None, "RAM": None}

    # ------------------------------------------------------------------
    def update(self, snap: dict, settings, now: float) -> list[dict]:
        """Feed one snapshot; return the list of alert events to display."""
        events: list[dict] = []
        if not snap or not getattr(settings, "alerts_enabled", False):
            self._streaks = {"CPU": 0, "RAM": 0}
            return events

        checks = (
            ("CPU", snap.get("cpu_percent"), getattr(settings, "cpu_threshold", 90)),
            ("RAM", snap.get("mem_percent"), getattr(settings, "ram_threshold", 90)),
        )
        for kind, value, threshold in checks:
            above = value is not None and float(value) >= float(threshold)
            self._streaks[kind] = self._streaks[kind] + 1 if above else 0

            last = self._last_fired[kind]
            cooled = last is None or (now - last) >= self.cooldown
            if above and self._streaks[kind] >= self.streak_needed and cooled:
                self._last_fired[kind] = now
                events.append({
                    "kind": kind,
                    "title": f"HIGH {kind} USAGE",
                    "message": (
                        f"{kind} is at {float(value):.0f}% "
                        f"(threshold: {int(threshold)}%)."
                    ),
                    "value": float(value),
                    "threshold": float(threshold),
                })
        return events

    # ------------------------------------------------------------------
    def above_threshold(self, snap: dict, settings) -> bool:
        """True while any monitored metric is currently over its threshold."""
        if not snap or not getattr(settings, "alerts_enabled", False):
            return False
        cpu = snap.get("cpu_percent")
        mem = snap.get("mem_percent")
        return (
            (cpu is not None and cpu >= settings.cpu_threshold)
            or (mem is not None and mem >= settings.ram_threshold)
        )

    def reset(self) -> None:
        self._streaks = {"CPU": 0, "RAM": 0}
        self._last_fired = {"CPU": None, "RAM": None}
