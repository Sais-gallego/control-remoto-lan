@echo off
title Cliente de Control Remoto con Audio
cd /d "%~dp0"
python -m pip install --quiet pyaudiowpatch pygame opencv-python numpy >nul 2>&1
python cliente.py
pause
