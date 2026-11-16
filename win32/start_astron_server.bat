@echo off
title Toontown Realms - Astron Server
cd ../astron
astrond --loglevel info config/astrond.yml
pause
