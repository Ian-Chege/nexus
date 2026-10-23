#!/usr/bin/env python3
"""NEXUS SYSTEM MONITOR - entry point.

Usage:
    python main.py                 start the monitor
    python main.py --selftest      run the built-in verification suite
    python main.py --reset-config  wipe saved preferences and exit
    python main.py --version       print the version
"""
from __future__ import annotations

import argparse
import sys
import traceback


def _enable_windows_dpi_awareness():
    if sys.platform == "win32":
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass


def _fatal_dialog(message: str):
    """Last-resort error dialog (and console pause on Windows)."""
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("NEXUS SYSTEM MONITOR - Error", message)
        root.destroy()
    except Exception:
        pass
    if sys.platform == "win32":
        try:
            input("\nPress Enter to exit...")
        except EOFError:
            pass


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="nexus-system-monitor",
        description="NEXUS SYSTEM MONITOR - live hardware dashboard")
    parser.add_argument("--selftest", action="store_true",
                        help="run the built-in verification suite and exit")
    parser.add_argument("--reset-config", action="store_true",
                        help="delete saved preferences and exit")
    parser.add_argument("--version", action="store_true",
                        help="print version and exit")
    args = parser.parse_args()

    if args.version:
        from nexus.constants import APP_VERSION
        print(f"NEXUS SYSTEM MONITOR v{APP_VERSION}")
        return 0

    if args.reset_config:
        from nexus import constants as C
        try:
            C.CONFIG_FILE.unlink(missing_ok=True)
            print(f"[OK] Removed {C.CONFIG_FILE}")
        except FileNotFoundError:
            print("[OK] No config file found")
        return 0

    _enable_windows_dpi_awareness()

    if args.selftest:
        from nexus.selftest import run
        return run()

    try:
        from nexus.settings import Settings
        from nexus.ui.app import NexusApp
        settings = Settings.load()
        app = NexusApp(settings)
        app.mainloop()
        return 0
    except KeyboardInterrupt:
        return 0
    except Exception:
        err = traceback.format_exc()
        traceback.print_exc()
        try:
            from nexus import constants as C
            C.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(C.ERROR_LOG, "a", encoding="utf-8") as fh:
                fh.write(err + "\n")
        except Exception:
            pass
        _fatal_dialog("The application failed to start:\n\n" + err[-1500:])
        return 1


if __name__ == "__main__":
    sys.exit(main())
