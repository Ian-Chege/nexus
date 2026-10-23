@echo off
REM ============================================================
REM  NEXUS SYSTEM MONITOR - Windows launcher
REM  Finds Python, installs dependencies on first run, starts UI.
REM ============================================================
setlocal EnableExtensions
title NEXUS SYSTEM MONITOR - Launcher
cd /d "%~dp0"

set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY (
    where python >nul 2>nul && set "PY=python"
)
if not defined PY (
    echo [X] Python 3 was not found on this computer.
    echo     Install it from https://www.python.org/downloads/
    echo     and CHECK "Add Python to PATH" during setup.
    pause
    exit /b 1
)

echo [*] Using: %PY%
%PY% -c "import customtkinter, psutil, matplotlib" >nul 2>nul
if errorlevel 1 (
    echo [*] First run - installing dependencies, please wait...
    %PY% -m pip install --upgrade pip
    %PY% -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [X] Failed to install dependencies.
        echo     Check your internet connection and try again.
        pause
        exit /b 1
    )
)

echo [*] Starting NEXUS SYSTEM MONITOR...
%PY% main.py %*
if errorlevel 1 (
    echo.
    echo [X] The application exited with an error - see message above.
    pause
)
endlocal
