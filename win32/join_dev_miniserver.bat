@echo off
title Toontown Realms - Developer Mini-Server Launcher
cd..

rem Read the contents of PPYTHON_PATH into %PPYTHON_PATH%:
set /P PPYTHON_PATH=<PPYTHON_PATH

echo Toontown Realms Developer Mini-Server Launcher
echo.

set /P TTOFF_PLAY_TOKEN="Username (default: dev): " || ^
set TTOFF_PLAY_TOKEN=dev

set /P TTOFF_GAME_SERVER="Game Server (default: 127.0.0.1): " || ^
set TTOFF_GAME_SERVER=127.0.0.1

set TTOFF_GAME_MODE=0

%PPYTHON_PATH% -m toontown.launcher.ToontownOfflineQuickStartLauncher
pause
