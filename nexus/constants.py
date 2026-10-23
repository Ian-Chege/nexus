"""NEXUS SYSTEM MONITOR - global constants and paths."""
from __future__ import annotations

import os
from pathlib import Path

APP_NAME = "NEXUS SYSTEM MONITOR"
APP_VERSION = "1.0.0"
DEFAULT_APP_NAME = APP_NAME  # fallback when the user clears the custom name

# ---------------------------------------------------------------------------
# Paths (override the config directory with the NEXUS_CONFIG_DIR env var)
# ---------------------------------------------------------------------------
CONFIG_DIR = Path(os.environ.get("NEXUS_CONFIG_DIR", str(Path.home() / ".nexus-monitor")))
CONFIG_FILE = CONFIG_DIR / "settings.json"
ERROR_LOG = CONFIG_DIR / "error.log"

# ---------------------------------------------------------------------------
# Monitoring behaviour
# ---------------------------------------------------------------------------
HISTORY_LEN = 240          # samples kept per metric (240 x 1s = 4 minutes)
DISPLAY_POINTS = 120       # samples drawn in the big graphs (2 min @ 1s)

ALERT_STREAK_NEEDED = 3    # consecutive samples above threshold before firing
ALERT_COOLDOWN_S = 60      # minimum seconds between two alerts of the same kind
TOAST_SECONDS = 6.5        # toast lifetime

MIN_INTERVAL = 0.5         # refresh interval bounds (seconds)
MAX_INTERVAL = 5.0

# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------
NAV_ITEMS = [
    ("dashboard", "DASHBOARD"),
    ("cpu", "CPU"),
    ("memory", "MEMORY"),
    ("storage", "STORAGE"),
    ("network", "NETWORK"),
    ("settings", "SETTINGS"),
]

PAGE_TITLES = {
    "dashboard": "DASHBOARD",
    "cpu": "CPU PERFORMANCE",
    "memory": "MEMORY",
    "storage": "STORAGE",
    "network": "NETWORK",
    "settings": "SETTINGS",
}
