@echo off
cd /d "%~dp0"
:: Ejecutar sin consola de comandos para que todo quede 100% limpio
start "" pythonw ventana_invisible.py
exit
