@echo off
cd /d "%~dp0"
:: Iniciar en segundo plano sin consola ni barra de tareas
start "" pythonw servidor.py
exit
