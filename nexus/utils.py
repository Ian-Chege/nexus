"""NEXUS SYSTEM MONITOR - formatting and small platform helpers."""
from __future__ import annotations

import platform
import sys
import time

# ---------------------------------------------------------------------------
# Fonts (Tk substitutes automatically when a family is missing)
# ---------------------------------------------------------------------------
if sys.platform == "win32":
    UI_FONT = "Segoe UI"
    MONO_FONT = "Consolas"
elif sys.platform == "darwin":
    UI_FONT = "Helvetica Neue"
    MONO_FONT = "Menlo"
else:
    UI_FONT = "DejaVu Sans"
    MONO_FONT = "DejaVu Sans Mono"


# ---------------------------------------------------------------------------
# Value formatting
# ---------------------------------------------------------------------------
def fmt_bytes(n, decimals: int = 1) -> str:
    """Human readable byte size, e.g. 12.3 GB. None-safe."""
    if n is None:
        return "N/A"
    try:
        n = float(n)
    except (TypeError, ValueError):
        return "N/A"
    neg = n < 0
    n = abs(n)
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    i = 0
    while n >= 1024.0 and i < len(units) - 1:
        n /= 1024.0
        i += 1
    dec = 0 if i == 0 else decimals
    return f"{'-' if neg else ''}{n:.{dec}f} {units[i]}"


def fmt_speed(bytes_per_sec) -> str:
    """Human readable speed, e.g. 1.4 MB/s."""
    if bytes_per_sec is None:
        return "N/A"
    return f"{fmt_bytes(bytes_per_sec)}/s"


def fmt_uptime(seconds) -> str:
    """Compact uptime, e.g. 3d 4h 12m or 12m 08s."""
    if seconds is None:
        return "N/A"
    seconds = int(max(0, seconds))
    d, rem = divmod(seconds, 86400)
    h, rem = divmod(rem, 3600)
    m, s = divmod(rem, 60)
    if d:
        return f"{d}d {h}h {m}m"
    if h:
        return f"{h}h {m}m {s:02d}s"
    return f"{m}m {s:02d}s"


def severity_color(pct, theme):
    """Map a percentage to a semantic color from the theme."""
    if pct is None:
        return theme.muted
    try:
        pct = float(pct)
    except (TypeError, ValueError):
        return theme.muted
    if pct >= 90:
        return theme.danger
    if pct >= 70:
        return theme.warning
    return theme.ok


def clamp(value, lo, hi):
    return max(lo, min(hi, value))


def clock_str(ts: float | None = None) -> str:
    return time.strftime("%H:%M:%S", time.localtime(ts if ts is not None else time.time()))


def os_pretty_name() -> str:
    """Best-effort pretty OS name on every platform."""
    if sys.platform.startswith("linux"):
        try:
            with open("/etc/os-release", "r", encoding="utf-8") as fh:
                for line in fh:
                    if line.startswith("PRETTY_NAME="):
                        return line.split("=", 1)[1].strip().strip('"')
        except OSError:
            pass
    return f"{platform.system()} {platform.release()}"
