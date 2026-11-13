@echo off
title Desactivar Inicio Automatico con Windows
set SHORTCUT=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\ControlRemotoServidor.lnk

if exist "%SHORTCUT%" (
    del "%SHORTCUT%"
    echo [EXITO] Se ha eliminado el inicio automatico correctamente.
) else (
    echo El inicio automatico no estaba configurado.
)
echo.
pause
