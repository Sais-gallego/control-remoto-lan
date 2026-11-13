@echo off
title Activar Inicio Automatico con Windows
echo Configurando el servidor para que inicie automaticamente con Windows...

pushd "%~dp0.."
set SCRIPT_DIR=%CD%
popd

set TARGET=%SCRIPT_DIR%\INICIAR_SERVIDOR.bat
set SHORTCUT=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\ControlRemotoServidor.lnk

powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT%'); $s.TargetPath = '%TARGET%'; $s.WorkingDirectory = '%SCRIPT_DIR%'; $s.WindowStyle = 7; $s.Save()"

echo.
echo ===================================================================
echo [EXITO] El servidor iniciara automaticamente al encender esta PC.
echo No tendras que abrirlo manualmente nunca mas.
echo Para desactivarlo en cualquier momento usa 'DESACTIVAR_INICIO_AUTOMATICO.bat'.
echo ===================================================================
echo.
pause
