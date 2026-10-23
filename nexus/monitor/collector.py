"""NEXUS SYSTEM MONITOR - background statistics collector.

A daemon thread samples psutil at the configured interval and publishes an
immutable snapshot dict plus rolling history deques under a lock. The UI
thread only ever reads copies of that data through snapshot()/history(),
so it never blocks and never touches widgets from another thread.

Everything is defensive: any sensor that is missing, unsupported or denies
access becomes None / "N/A" upstream instead of an exception.
"""
from __future__ import annotations

import platform
import shutil
import subprocess
import threading
import time
import traceback
from collections import deque

import psutil

from .. import constants as C
from ..utils import os_pretty_name

# Filesystems that add pure noise (virtual/kernel mounts). "overlay" is
# deliberately allowed so container/WSL root filesystems are still shown.
_SKIP_FS = {
    "squashfs", "tmpfs", "devtmpfs", "proc", "sysfs", "iso9660",
    "swap", "ramfs", "cgroup", "cgroup2", "efivarfs", "devfs", "autofs",
    "mqueue", "hugetlbfs", "bpf", "tracefs", "debugfs", "configfs", "fusectl",
    "securityfs", "pstore", "nsfs", "binfmt_misc", "fuse.snapfuse", "devpts",
}


# ---------------------------------------------------------------------------
# Sensor helpers (all best-effort, all exception-safe)
# ---------------------------------------------------------------------------
def _query_nvidia() -> dict | None:
    """Query the first NVIDIA GPU through nvidia-smi. None when unavailable."""
    if shutil.which("nvidia-smi") is None:
        return None
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,temperature.gpu,utilization.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=3,
        )
        line = (out.stdout or "").strip().splitlines()
        if not line:
            return None
        parts = [p.strip() for p in line[0].split(",")]
        if len(parts) < 3:
            return None
        name = parts[0] or "NVIDIA GPU"
        temp = float(parts[1]) if parts[1].replace(".", "", 1).isdigit() else None
        util = float(parts[2]) if parts[2].replace(".", "", 1).isdigit() else None
        return {"name": name, "temp": temp, "util": util}
    except (OSError, subprocess.SubprocessError, ValueError):
        return None


def _psutil_temperatures() -> dict:
    fn = getattr(psutil, "sensors_temperatures", None)
    if fn is None:          # Windows: psutil has no sensor API
        return {}
    try:
        return fn() or {}
    except Exception:
        return {}


def _pick_cpu_temp(temps: dict):
    """Choose the most representative CPU temperature from psutil output."""
    if not temps:
        return None
    priority = ("coretemp", "k10temp", "zenpower", "cpu_thermal",
                "cpu-thermal", "acpitz", "atk0110", "x86_pkg_temp")
    for key in priority:
        entries = temps.get(key)
        if not entries:
            continue
        for e in entries:                       # prefer the package sensor
            if (e.label or "").lower().startswith("package"):
                if e.current and e.current > 0:
                    return e.current
        for e in entries:                       # else any entry of the sensor
            if e.current and e.current > 0:
                return e.current
    for entries in temps.values():              # last resort: first non-zero
        for e in entries or ():
            if e.current and e.current > 0:
                return e.current
    return None


def _wmi_temp() -> float | None:
    """Windows thermal zone via WMI (needs admin on many machines)."""
    try:
        out = subprocess.run(
            ["wmic", "/namespace:\\\\root\\wmi", "PATH",
             "MSAcpi_ThermalZoneTemperature", "get", "CurrentTemperature"],
            capture_output=True, text=True, timeout=3,
        )
        for line in (out.stdout or "").splitlines():
            line = line.strip()
            if line.isdigit():
                celsius = int(line) / 10.0 - 273.15
                if -20 < celsius < 150:
                    return round(celsius, 1)
    except (OSError, subprocess.SubprocessError, ValueError):
        pass
    return None


# ---------------------------------------------------------------------------
# Collector thread
# ---------------------------------------------------------------------------
class SystemCollector(threading.Thread):
    """Continuously samples system statistics in the background."""

    def __init__(self, settings_getter, history_len: int = C.HISTORY_LEN):
        super().__init__(daemon=True, name="NexusCollector")
        self._settings_getter = settings_getter
        self._stop_evt = threading.Event()
        self._lock = threading.RLock()

        self._hist = {k: deque(maxlen=history_len)
                      for k in ("cpu", "mem", "swap", "down", "up",
                                "cpu_temp", "gpu_temp")}
        self.snap: dict = {}

        # previous samples for delta computation
        self._last_net = None
        self._last_net_t: float | None = None
        self._last_disk = None
        self._last_disk_t: float | None = None
        self._pernic_prev: dict = {}
        self._pernic_t: float | None = None

        # GPU / temperature caches
        self._gpu: dict | None = None
        self._gpu_probe_at = 0.0
        self._temp_fallback: tuple = (None, 0.0)   # (value, timestamp)

        # static host info
        self._host_info = {
            "hostname": platform.node() or "localhost",
            "os_name": f"{platform.system()} {platform.release()}",
            "os_pretty": os_pretty_name(),
            "arch": platform.machine() or "unknown",
            "python": platform.python_version(),
        }
        self._prime()

    # ------------------------------------------------------------------
    def _prime(self) -> None:
        """Warm psutil counters so the very first displayed sample is valid."""
        try:
            psutil.cpu_percent(interval=None)
            psutil.cpu_percent(interval=None, percpu=True)
        except Exception:
            pass
        try:
            self._last_net = psutil.net_io_counters()
            self._last_net_t = time.time()
        except Exception:
            pass
        try:
            self._last_disk = psutil.disk_io_counters()
            self._last_disk_t = time.time()
        except Exception:
            pass
        self._gpu = _query_nvidia()
        self._gpu_probe_at = time.time()

    def stop(self) -> None:
        self._stop_evt.set()

    # ------------------------------------------------------------------
    def run(self) -> None:
        while not self._stop_evt.is_set():
            started = time.time()
            try:
                self._sample()
            except Exception:
                self._log_error("collector._sample failed:\n" + traceback.format_exc())
            try:
                interval = max(0.3, float(self._settings_getter().refresh_interval))
            except Exception:
                interval = 1.0
            elapsed = time.time() - started
            self._stop_evt.wait(max(0.05, interval - elapsed))

    # ------------------------------------------------------------------
    # public read API (UI thread safe)
    # ------------------------------------------------------------------
    def snapshot(self) -> dict:
        with self._lock:
            return dict(self.snap)

    def history(self, key: str, n: int | None = None) -> list:
        with self._lock:
            items = list(self._hist.get(key, ()))
        return items[-n:] if n else items

    # ------------------------------------------------------------------
    # sampling
    # ------------------------------------------------------------------
    def _sample(self) -> None:
        now = time.time()
        self._counter = getattr(self, "_counter", 0) + 1
        s: dict = {"timestamp": now}

        # -- CPU ----------------------------------------------------------
        s["cpu_percent"] = psutil.cpu_percent(interval=None) or 0.0
        s["cpu_per_core"] = psutil.cpu_percent(interval=None, percpu=True) or []
        s["cpu_count"] = psutil.cpu_count(logical=True) or len(s["cpu_per_core"]) or 0
        s["cpu_count_phys"] = psutil.cpu_count(logical=False) or 0
        try:
            f = psutil.cpu_freq()
            s["cpu_freq_mhz"] = float(f.current) if f and f.current else None
            s["cpu_freq_max_mhz"] = float(f.max) if f and f.max else None
        except Exception:
            s["cpu_freq_mhz"] = None
            s["cpu_freq_max_mhz"] = None
        s["cpu_temp"] = self._read_cpu_temp(now)

        # -- GPU (NVIDIA, refreshed every 2nd sample; re-probed if absent) --
        if self._gpu is None and now - self._gpu_probe_at > 30:
            self._gpu = _query_nvidia()
            self._gpu_probe_at = now
        if self._gpu is not None and self._counter % 2 == 0:
            fresh = _query_nvidia()
            if fresh:
                self._gpu = fresh
            else:
                self._gpu = None
                self._gpu_probe_at = now
        s["gpu"] = dict(self._gpu) if self._gpu else None

        # -- memory --------------------------------------------------------
        vm = psutil.virtual_memory()
        s["mem_percent"] = float(vm.percent)
        s["mem_used"] = vm.used
        s["mem_total"] = vm.total
        s["mem_available"] = vm.available
        s["mem_cached"] = getattr(vm, "cached", None)
        s["mem_buffers"] = getattr(vm, "buffers", None)
        try:
            sw = psutil.swap_memory()
            s["swap_percent"] = float(sw.percent)
            s["swap_used"] = sw.used
            s["swap_total"] = sw.total
        except Exception:
            s["swap_percent"] = s["swap_used"] = s["swap_total"] = None

        # -- disks ---------------------------------------------------------
        s["disks"] = self._disks()
        s["disk_read_bps"] = None
        s["disk_write_bps"] = None
        try:
            io = psutil.disk_io_counters()
            if io:
                if self._last_disk and self._last_disk_t and now > self._last_disk_t:
                    dt = now - self._last_disk_t
                    s["disk_read_bps"] = max(0.0, (io.read_bytes - self._last_disk.read_bytes) / dt)
                    s["disk_write_bps"] = max(0.0, (io.write_bytes - self._last_disk.write_bytes) / dt)
                self._last_disk, self._last_disk_t = io, now
        except Exception:
            pass

        # -- network -------------------------------------------------------
        try:
            n = psutil.net_io_counters()
            if self._last_net and self._last_net_t and now > self._last_net_t:
                dt = now - self._last_net_t
                s["net_down_bps"] = max(0.0, (n.bytes_recv - self._last_net.bytes_recv) / dt)
                s["net_up_bps"] = max(0.0, (n.bytes_sent - self._last_net.bytes_sent) / dt)
            else:
                s["net_down_bps"] = 0.0
                s["net_up_bps"] = 0.0
            self._last_net, self._last_net_t = n, now
            s["net_total_recv"] = n.bytes_recv
            s["net_total_sent"] = n.bytes_sent
        except Exception:
            s["net_down_bps"] = s["net_up_bps"] = 0.0
            s["net_total_recv"] = s["net_total_sent"] = None
        s["net_interfaces"] = self._pernic(now)

        # -- system ----------------------------------------------------------
        s["uptime_s"] = max(0.0, now - psutil.boot_time())
        s["boot_time"] = psutil.boot_time()
        s["proc_count"] = len(psutil.pids())
        try:
            s["load_avg"] = tuple(round(x, 2) for x in psutil.getloadavg())
        except Exception:
            s["load_avg"] = None
        if self._counter % 3 == 1 or "top_processes" not in self.snap:
            s["top_processes"] = self._top_processes()
        else:
            with self._lock:
                s["top_processes"] = list(self.snap.get("top_processes", ()))

        s.update(self._host_info)

        # -- publish ---------------------------------------------------------
        with self._lock:
            self.snap = s
            self._hist["cpu"].append((now, s["cpu_percent"]))
            self._hist["mem"].append((now, s["mem_percent"]))
            self._hist["swap"].append((now, s["swap_percent"]))
            self._hist["down"].append((now, s["net_down_bps"]))
            self._hist["up"].append((now, s["net_up_bps"]))
            self._hist["cpu_temp"].append((now, s["cpu_temp"]))
            self._hist["gpu_temp"].append((now, s["gpu"]["temp"] if s["gpu"] else None))

    # ------------------------------------------------------------------
    def _read_cpu_temp(self, now: float):
        temps = _psutil_temperatures()
        value = _pick_cpu_temp(temps)
        if value is not None:
            return value
        # Slow fallback path (Windows WMI) - throttle to one call / 15 s
        cached_value, cached_at = self._temp_fallback
        if now - cached_at < 15:
            return cached_value
        value = _wmi_temp() if platform.system() == "Windows" else None
        self._temp_fallback = (value, now)
        return value

    def _disks(self) -> list[dict]:
        out: list[dict] = []
        try:
            parts = psutil.disk_partitions(all=False)
        except Exception:
            return out
        if not parts:
            # Some container/WSL sandboxes expose nothing with all=False;
            # retry with virtual filesystems included, the filter below
            # strips the noise anyway.
            try:
                parts = psutil.disk_partitions(all=True)
            except Exception:
                return out
        seen = set()
        for p in parts:
            fstype = (p.fstype or "").lower()
            device = (p.device or "").lower()
            if fstype in _SKIP_FS or device.startswith("/dev/loop"):
                continue
            if p.mountpoint in seen:          # dedupe by mountpoint
                continue
            seen.add(p.mountpoint)
            try:
                u = psutil.disk_usage(p.mountpoint)
            except Exception:
                continue
            out.append({
                "device": p.device, "mount": p.mountpoint,
                "fstype": p.fstype or "unknown",
                "total": u.total, "used": u.used, "free": u.free,
                "percent": u.percent,
            })
        # system root first ("/" on Linux, "C:\\" on Windows), then by mount
        out.sort(key=lambda d: (0 if d["mount"] in ("/", "C:\\") else 1,
                                d["mount"]))
        return out

    def _pernic(self, now: float) -> list[dict]:
        try:
            counters = psutil.net_io_counters(pernic=True)
        except Exception:
            return []
        dt = max(1e-6, now - (self._pernic_t or now))
        out: list[dict] = []
        for name, c in counters.items():
            prev = self._pernic_prev.get(name)
            down = (c.bytes_recv - prev.bytes_recv) / dt if prev else 0.0
            up = (c.bytes_sent - prev.bytes_sent) / dt if prev else 0.0
            out.append({"name": name, "recv": c.bytes_recv, "sent": c.bytes_sent,
                        "down_bps": max(0.0, down), "up_bps": max(0.0, up)})
        self._pernic_prev, self._pernic_t = counters, now
        out.sort(key=lambda d: (d["recv"] + d["sent"]), reverse=True)
        return out[:8]

    def _top_processes(self) -> list[dict]:
        procs: list[dict] = []
        for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
            try:
                info = p.info
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
            if info.get("name"):
                procs.append(info)
        procs.sort(key=lambda d: ((d.get("cpu_percent") or 0.0),
                                  (d.get("memory_percent") or 0.0)), reverse=True)
        return procs[:6]

    @staticmethod
    def _log_error(message: str) -> None:
        try:
            C.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            stamp = time.strftime("%Y-%m-%d %H:%M:%S")
            with open(C.ERROR_LOG, "a", encoding="utf-8") as fh:
                fh.write(f"[{stamp}] {message}\n")
        except OSError:
            pass
