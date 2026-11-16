@echo off
title Toontown Realms - Game Client
cd..

rem Read the contents of PPYTHON_PATH into %PPYTHON_PATH%:
set /P PPYTHON_PATH=<PPYTHON_PATH

set TTOFF_PLAY_TOKEN=dev
set TTOFF_GAME_MODE=0

%PPYTHON_PATH% -m toontown.launcher.ToontownOfflineQuickStartLauncher
pause
