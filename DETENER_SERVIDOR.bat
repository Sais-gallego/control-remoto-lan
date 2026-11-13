@echo off
title Detener Servidor de Control Remoto
cd /d "%~dp0"
echo Deteniendo servidor de control remoto y audio en segundo plano...

for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5555 ^| findstr LISTENING') do (
    taskkill /f /pid %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5556 ^| findstr LISTENING') do (
    taskkill /f /pid %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5558 ^| findstr LISTENING') do (
    taskkill /f /pid %%a >nul 2>&1
)

echo.
echo Servidor y audio detenidos correctamente.
timeout /t 2 >nul
exit
