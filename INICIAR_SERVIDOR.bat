@echo off
title Servidor de Control Remoto (PC a manipular)
cd /d "%~dp0"
echo Verificando librerias...
python -m pip install --quiet mss opencv-python pynput pillow numpy
echo.
python servidor.py
pause
