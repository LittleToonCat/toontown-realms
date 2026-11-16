#!/bin/sh
cd ..

export TTOFF_PLAY_TOKEN=dev
export TTOFF_GAME_MODE=0

python3 -m toontown.launcher.ToontownOfflineQuickStartLauncher
