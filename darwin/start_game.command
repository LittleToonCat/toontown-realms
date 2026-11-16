cd `dirname $0`
cd ..

export TTOFF_PLAY_TOKEN="dev"
export TTOFF_GAME_MODE=0

/usr/bin/python3 -m toontown.launcher.ToontownOfflineQuickStartLauncher
