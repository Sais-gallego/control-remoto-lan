@echo off
title Cliente de Control Remoto (PC que manipula)
cd /d "%~dp0"
echo Verificando librerias...
python -m pip install --quiet pygame opencv-python numpy
echo.
python cliente.py
pause
