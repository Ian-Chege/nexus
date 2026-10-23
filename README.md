# NEXUS SYSTEM MONITOR

A complete, professional desktop system monitor with a futuristic neon UI.

Built with **Python + CustomTkinter + psutil + Matplotlib**. Every number on
screen comes from **real hardware telemetry** — nothing is simulated.

![Dashboard](../screenshots/shot_1_dashboard.png)

---

## Features

| Area | What you get |
|---|---|
| **Dashboard** | Live CPU / RAM / Disk / Network cards, combined history graph, CPU & GPU temps, uptime, hostname, OS info, process count |
| **CPU** | Full usage graph, per-core bars, clock speed, temperature, load average, top-6 processes table |
| **Memory** | RAM + Swap history graph, swap bar, total / used / available / cached / buffers details |
| **Storage** | Every partition with usage bar, used/total/free, aggregate disk read & write speeds |
| **Network** | Live download & upload speed graph, session totals, per-interface traffic table |
| **Alerts** | Configurable CPU/RAM thresholds, fires a non-blocking toast after 3 sustained samples (60 s cooldown), header status dot |
| **Settings** | **9 hand-crafted themes**, custom application name, refresh interval (0.5–5 s), alert thresholds, test-alert button, reset — all saved automatically |

### The theme collection (not the classics)

`Nexus Dark` · `Cyberpunk 2077` · `Matrix` · `Synthwave '84` · `Blood Moon` ·
`Midnight Gold` · `Aurora` · `Frost (Light)` · `Sakura (Light)`

Every theme recolors the entire application instantly — cards, graphs, sidebar,
sliders and even the Matplotlib plots.

---

## Supported platforms

- **Windows 10/11** (x64) — temps may be unavailable on many machines
  (hardware/ACPI restrictions); the app shows `N/A` gracefully. NVIDIA GPUs
  are read through `nvidia-smi`.
- **Kali Linux / Debian / Ubuntu** (and most distros) — CPU temps via
  `psutil.sensors_temperatures()` (coretemp / k10temp / cpu_thermal).
  NVIDIA GPUs via `nvidia-smi`.
- **macOS 12+** (Intel & Apple Silicon) — runs from source with standard
  Python; no installer or `.dmg` needed. macOS does not expose CPU
  temperatures or NVIDIA telemetry to psutil, so those cards show `N/A` —
  an OS limitation, not a bug.
- Unsupported sensors never crash anything — they display **N/A** with an
  explanation.

---

## Installation & launch

### Windows
1. Install Python 3.9+ from <https://www.python.org/downloads/> —
   **check "Add Python to PATH"**.
2. Double-click **`run_windows.bat`**.
   First run installs the dependencies automatically, then starts the app.

Manual alternative:
```bat
python -m pip install -r requirements.txt
python main.py
```

### Kali / Debian / Ubuntu
```bash
# one-time system packages
sudo apt update && sudo apt install -y python3 python3-pip python3-venv python3-tk

# run (creates an isolated .venv and installs deps on first launch)
chmod +x run_linux.sh
./run_linux.sh
```

Manual alternative:
```bash
python3 -m pip install -r requirements.txt
python3 main.py
```

### macOS
```bash
# run (creates an isolated .venv and installs deps on first launch)
chmod +x run_mac.sh
./run_mac.sh
```

If Python is missing, install it from <https://www.python.org/downloads/>
(the installer bundles Tk). Homebrew users: `brew install python-tk`.
Apple's built-in `/usr/bin/python3` ships Tk 8.5, which opens a **blank
window** — `run_mac.sh` skips it and picks a Homebrew/python.org Python instead.

Manual alternative:
```bash
python3 -m pip install -r requirements.txt
python3 main.py
```

<details>
<summary><b>Optional: package a real Mac <code>.app</code> / <code>.dmg</code></b> (must be done ON a Mac)</summary>

```bash
python3 -m pip install pyinstaller
pyinstaller --windowed --collect-all customtkinter \
    --name "NEXUS System Monitor" main.py
# the bundle appears at dist/NEXUS System Monitor.app

# wrap it into a .dmg if you really want one:
hdiutil create -volname "NEXUS System Monitor" \
    -srcfolder "dist/NEXUS System Monitor.app" \
    -ov -format UDZO "NEXUS-System-Monitor.dmg"
```
</details>

### Command-line options
```
python main.py --selftest       # run the built-in verification suite
python main.py --reset-config   # wipe saved preferences and exit
python main.py --version        # print version
```

---

## Configuration

Preferences persist in `~/.nexus-monitor/settings.json` (created on first
save). You can override the location with the `NEXUS_CONFIG_DIR` environment
variable.

```json
{
  "app_name": "NEXUS SYSTEM MONITOR",
  "theme": "nexus_dark",
  "refresh_interval": 1.0,
  "alerts_enabled": true,
  "cpu_threshold": 90,
  "ram_threshold": 90
}
```

Crash diagnostics (rare collector errors) are appended to
`~/.nexus-monitor/error.log`.

---

## Architecture (why the UI never freezes)

```
main.py                     entry point, DPI awareness, fatal-error dialog
nexus/
  constants.py              paths, limits, navigation table
  theme.py                  Theme dataclass + 9 palettes
  settings.py               JSON persistence + validation
  utils.py                  byte/uptime formatting, fonts, severity colors
  selftest.py               6-stage verification suite
  monitor/
    collector.py            daemon thread: psutil sampling, GPU/temp probing,
                            history deques, disk/net deltas — lock-guarded
    alerts.py               pure-logic threshold state machine (unit-tested)
  ui/
    app.py                  window shell, page router, toast manager, refresh loop
    sidebar.py / header.py  navigation + title/clock/alert-dot
    graphs.py               Matplotlib Figure embedded in CTkFrame (TkAgg)
    components.py           StatCard, InfoCard, MiniTable, CoreBar, ThemeCard, Toast
    dashboard.py / cpu_page.py / memory_page.py /
    storage_page.py / network_page.py / settings_page.py
```

- **One background thread** samples psutil and publishes snapshots under a
  lock; the UI only reads copies inside `after()` callbacks on the main
  thread, so widget access is always thread-safe.
- **Graphs** update via `set_data()` + `draw_idle()` — no full redraws, no
  flicker, negligible CPU cost.
- **Every component implements `apply_theme()`** — switching themes is an
  instant recolor, not a rebuild.
- **Defensive sampling**: each metric is wrapped; missing sensors, denied
  partitions or absent GPUs degrade to `N/A` instead of exceptions.

---

## Verification (self-test)

Run `python main.py --selftest` — it checks, on YOUR machine:

1. `utils.formatting` — byte/speed/uptime formatting invariants
2. `themes.registry` — all 9 palettes valid, light theme present
3. `settings.persistence` — save/reload round-trip + corrupt-value clamping
4. `alerts.engine` — streak requirement, cooldown, recovery, disable switch
5. `collector.live_sample` — a real psutil pass (CPU/RAM/disk/net keys present)
6. `gui.smoke_test` — boots the real window, walks all 6 pages, applies all
   9 themes, fires a toast (auto-skipped on headless machines)

---

## Troubleshooting

| Symptom | Explanation / fix |
|---|---|
| CPU/GPU temperature shows `N/A` on Windows | Most consumer boards block ACPI temp reads without a kernel driver. Install LibreHardwareMonitor-compatible tooling or accept `N/A` — this is a Windows limitation, not a bug. |
| GPU card shows `N/A` | Only NVIDIA GPUs are queried (via `nvidia-smi`, bundled with the driver). AMD/Intel GPU telemetry is not exposed by psutil. |
| Linux shows no temps | Run `sensors-detect` (lm-sensors) once, or your kernel lacks sensor drivers (common in VMs). |
| `python3-tk` error on Linux | `sudo apt install python3-tk`. |
| Fonts look different | The app uses Segoe UI (Windows) / DejaVu Sans (Linux) with automatic fallback. |
| Reset everything | `python main.py --reset-config`, or the button in Settings → About & Data. |

---

## License

MIT — use it, modify it, ship it.
