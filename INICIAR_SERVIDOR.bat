@echo off
cd /d "%~dp0"
python -m pip install --quiet pyaudiowpatch mss opencv-python pynput pillow numpy >nul 2>&1
start "" pythonw servidor.py
exit
