@echo off
title Toontown - Fireworks Editor
cd..\

rem Read the contents of PPYTHON_PATH into %PPYTHON_PATH%:
set /P PPYTHON_PATH=<PPYTHON_PATH

%PPYTHON_PATH% -m tools.FireworksEditor
pause