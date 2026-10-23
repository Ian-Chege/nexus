#!/usr/bin/env bash
# ============================================================
#  NEXUS SYSTEM MONITOR - Linux launcher (Kali/Ubuntu/Debian)
#  Installs dependencies into an isolated venv on first run.
# ============================================================
set -u
cd "$(dirname "$0")"

PY=python3
if ! command -v "$PY" >/dev/null 2>&1; then
    echo "[X] python3 not found.  Install it with:"
    echo "    sudo apt install python3 python3-pip python3-venv python3-tk"
    exit 1
fi

# CustomTkinter needs the Tk GUI toolkit
if ! "$PY" -c "import tkinter" >/dev/null 2>&1; then
    echo "[X] The Tk toolkit is missing (python3-tk).  Install it with:"
    echo "    sudo apt install python3-tk"
    exit 1
fi

if "$PY" -c "import customtkinter, psutil, matplotlib" >/dev/null 2>&1; then
    exec "$PY" main.py "$@"
fi

echo "[*] First run - creating isolated environment and installing dependencies..."
if "$PY" -m venv .venv >/dev/null 2>&1; then
    ./.venv/bin/pip install --quiet --upgrade pip
    if ! ./.venv/bin/pip install --quiet -r requirements.txt; then
        echo "[X] Dependency installation failed - check your connection."
        exit 1
    fi
    echo "[*] Starting NEXUS SYSTEM MONITOR..."
    exec ./.venv/bin/python main.py "$@"
else
    echo "[!] python3-venv unavailable - falling back to a --user install"
    echo "    (recommended: sudo apt install python3-venv)"
    "$PY" -m pip install --user --quiet -r requirements.txt || {
        echo "[X] Dependency installation failed - check your connection."
        exit 1
    }
    echo "[*] Starting NEXUS SYSTEM MONITOR..."
    exec "$PY" main.py "$@"
fi
