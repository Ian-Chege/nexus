#!/usr/bin/env bash
# ============================================================
#  NEXUS SYSTEM MONITOR - macOS launcher (Intel & Apple Silicon)
#  Installs dependencies into an isolated venv on first run.
# ============================================================
set -u
cd "$(dirname "$0")"

# CustomTkinter needs Tk 8.6+.  Apple's /usr/bin/python3 ships Tk 8.5,
# which opens a blank window on recent macOS, so prefer Homebrew/python.org.
PY=""
# Homebrew does not always link a plain `python3`, so also look in each keg.
for c in /opt/homebrew/bin/python3 /opt/homebrew/opt/python@3*/libexec/bin/python3 \
         /usr/local/bin/python3 /usr/local/opt/python@3*/libexec/bin/python3 \
         /Library/Frameworks/Python.framework/Versions/Current/bin/python3 python3; do
    if command -v "$c" >/dev/null 2>&1 &&
       "$c" -c "import sys, tkinter; sys.exit(tkinter.TkVersion < 8.6)" >/dev/null 2>&1; then
        PY="$c"
        break
    fi
done

if [ -z "$PY" ]; then
    echo "[X] No Python 3.9+ with Tk 8.6 or newer was found."
    echo "    (Apple's built-in python3 has Tk 8.5, which shows a blank window.)"
    echo "    Homebrew:  brew install python python-tk"
    echo "    Or install Python from https://www.python.org/downloads/"
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
    echo "[!] venv unavailable - falling back to a --user install"
    echo "    (macOS system python3 cannot create venvs without Developer Tools)"
    "$PY" -m pip install --user --quiet -r requirements.txt || {
        echo "[X] Dependency installation failed - check your connection."
        exit 1
    }
    echo "[*] Starting NEXUS SYSTEM MONITOR..."
    exec "$PY" main.py "$@"
fi
