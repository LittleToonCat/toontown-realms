@echo off
title Toontown Realms - AI (District) Server
cd..

rem Read the contents of PPYTHON_PATH into %PPYTHON_PATH%:
set /P PPYTHON_PATH=<PPYTHON_PATH

set TTOFF_GAME_MODE=0

:main
%PPYTHON_PATH% -m toontown.ai.AIStart
pause
