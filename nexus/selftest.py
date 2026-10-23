"""NEXUS SYSTEM MONITOR - built-in self-test.

Run with:  python main.py --selftest

Verifies every layer without faking data:
  1. utility formatting
  2. theme registry integrity
  3. settings persistence round-trip + validation clamping
  4. alert engine state machine (streaks + cooldown)
  5. one real psutil collection pass (real hardware numbers)
  6. full GUI smoke test (builds the window, walks every page, applies every
     theme, fires a toast) - skipped gracefully when no display is present.
"""
from __future__ import annotations

import os
import sys
import tempfile
import time
import traceback

import tempfile as _tmp

# Isolate config writes from the user's real profile BEFORE importing nexus.
os.environ.setdefault("NEXUS_CONFIG_DIR",
                      tempfile.mkdtemp(prefix="nexus-selftest-"))

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nexus.monitor.alerts import AlertEngine          # noqa: E402
from nexus.monitor.collector import SystemCollector   # noqa: E402
from nexus.settings import Settings                   # noqa: E402
from nexus.theme import THEMES, get_theme             # noqa: E402
from nexus import utils                               # noqa: E402

RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, fn):
    print(f"  [ .... ] {name}", flush=True)
    try:
        fn()
        RESULTS.append((name, True, ""))
        print(f"\r  [ PASS ] {name}", flush=True)
    except Exception as exc:
        RESULTS.append((name, False, str(exc)))
        print(f"\r  [ FAIL ] {name}: {exc}", flush=True)
        traceback.print_exc()


# ---------------------------------------------------------------------------
def test_utils():
    assert utils.fmt_bytes(1536) == "1.5 KB"
    assert utils.fmt_bytes(None) == "N/A"
    assert utils.fmt_bytes(0) == "0 B"
    assert utils.fmt_speed(2 * 1024 * 1024) == "2.0 MB/s"
    assert utils.fmt_uptime(90061) == "1d 1h 1m"
    assert utils.fmt_uptime(0) == "0m 00s"
    assert utils.clamp(9, 0, 5) == 5


def test_themes():
    assert len(THEMES) >= 8, "need a real theme collection"
    lights = [t for t in THEMES.values() if t.appearance == "Light"]
    assert lights, "need at least one light theme"
    for t in THEMES.values():
        for field in ("bg", "sidebar", "card", "text", "muted", "accent",
                      "accent2", "ok", "warning", "danger", "grid", "track"):
            val = getattr(t, field)
            assert isinstance(val, str) and val.startswith("#") and len(val) == 7, \
                f"{t.key}.{field} invalid: {val}"
    assert get_theme("nope").key == "nexus_dark"
    assert get_theme(None).key == "nexus_dark"


def test_settings():
    s1 = Settings()
    s1.app_name = "MY RIG"
    s1.theme = "matrix"
    s1.refresh_interval = 2.5
    s1.cpu_threshold = 77
    s1.save()
    s2 = Settings.load()
    assert s2.app_name == "MY RIG"
    assert s2.theme == "matrix"
    assert abs(s2.refresh_interval - 2.5) < 1e-6
    assert s2.cpu_threshold == 77
    # clamping of corrupt values
    s3 = Settings()
    s3.refresh_interval = 0.01
    s3.cpu_threshold = 5
    s3.theme = "does-not-exist"
    s3.normalize()
    assert s3.refresh_interval >= 0.5 and s3.cpu_threshold == 50
    assert s3.theme == "nexus_dark"
    Settings().save()      # restore clean defaults for later stages


def test_alerts():
    eng = AlertEngine(streak_needed=2, cooldown=60)
    s = Settings()
    s.alerts_enabled = True
    s.cpu_threshold = 50
    s.ram_threshold = 90
    hot = {"cpu_percent": 95.0, "mem_percent": 30.0}
    t0 = 1000.0
    assert eng.update(hot, s, t0) == []                      # streak 1
    events = eng.update(hot, s, t0 + 1)                      # streak 2 -> fire
    assert len(events) == 1 and events[0]["kind"] == "CPU"
    assert eng.update(hot, s, t0 + 2) == []                  # cooldown active
    assert eng.update(hot, s, t0 + 100)[0]["kind"] == "CPU"  # cooled down
    assert eng.update({"cpu_percent": 10.0, "mem_percent": 10.0}, s, t0 + 200) == []
    assert not eng.above_threshold({"cpu_percent": 10.0, "mem_percent": 10.0}, s)
    s.alerts_enabled = False
    assert eng.update(hot, s, t0 + 300) == []
    assert not eng.above_threshold(hot, s)


def test_collector():
    s = Settings()
    c = SystemCollector(lambda: s, history_len=10)
    c._sample()
    time.sleep(0.25)
    c._sample()
    snap = c.snapshot()
    required = ("timestamp", "cpu_percent", "cpu_per_core", "mem_percent",
                "mem_total", "swap_percent", "disks", "net_down_bps",
                "net_up_bps", "uptime_s", "hostname", "os_pretty",
                "proc_count")
    for key in required:
        assert key in snap, f"missing snapshot key: {key}"
    assert isinstance(snap["cpu_percent"], (int, float))
    assert snap["mem_total"] > 0
    assert snap["uptime_s"] >= 0
    assert isinstance(snap["disks"], list)
    assert len(c.history("cpu")) == 2
    print(f"           live sample: cpu={snap['cpu_percent']:.1f}% "
          f"mem={snap['mem_percent']:.1f}% disks={len(snap['disks'])} "
          f"host={snap['hostname']}")
    c.stop()


def test_gui():
    try:
        from nexus.ui.app import NexusApp
    except Exception as exc:                     # matplotlib/Tk missing
        raise AssertionError(f"GUI imports failed: {exc}")
    try:
        settings = Settings.load()
        app = NexusApp(settings)
    except Exception as exc:
        if "no display" in str(exc).lower() or "TclError" in type(exc).__name__:
            print("           (no display available - GUI stage skipped)")
            return
        raise
    state = {"step": 0, "error": None}
    pages = ["dashboard", "cpu", "memory", "storage", "network", "settings"]
    themes = list(THEMES.keys())

    def step():
        try:
            i = state["step"]
            if i < len(pages):
                app.show_page(pages[i])
                app._update_once()
            elif i < len(pages) + len(themes):
                app.apply_theme(themes[i - len(pages)])
                app._update_once()
            elif i == len(pages) + len(themes):
                app.set_app_name("NEXUS SELFTEST")
                app.show_toast("SELFTEST", "Toast notification path OK.", "ok")
                app._update_once()
            else:
                app.destroy()
                return
            state["step"] += 1
            app.after(40, step)
        except Exception as exc:
            state["error"] = exc
            traceback.print_exc()
            app.destroy()

    app.after(350, step)
    app.after(60000, app.destroy)     # watchdog
    app.mainloop()
    if state["error"]:
        raise AssertionError(f"GUI step failed: {state['error']}")
    assert state["step"] >= len(pages) + len(themes), "GUI steps did not finish"


# ---------------------------------------------------------------------------
def run() -> int:
    print(f"\nNEXUS SYSTEM MONITOR v-selftest "
          f"(config: {os.environ['NEXUS_CONFIG_DIR']})\n")
    check("utils.formatting", test_utils)
    check("themes.registry", test_themes)
    check("settings.persistence", test_settings)
    check("alerts.engine", test_alerts)
    check("collector.live_sample", test_collector)
    check("gui.smoke_test", test_gui)

    passed = sum(1 for _n, ok, _e in RESULTS if ok)
    total = len(RESULTS)
    print(f"\n  RESULT: {passed}/{total} checks passed")
    if passed == total:
        print("  ALL SYSTEMS NOMINAL \u2713\n")
        return 0
    print("  FAILURES DETECTED \u2717\n")
    return 1


if __name__ == "__main__":
    sys.exit(run())
