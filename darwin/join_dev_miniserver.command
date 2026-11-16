cd `dirname $0`
cd ..

echo "Toontown Realms Developer Mini-Server Launcher"
echo
echo "NOTE: Make sure that \"mini-server\" is enabled in your settings.json!"
echo

read -p "Username (default: dev): " ttoffPlayToken
read -p "Game Server (default: 127.0.0.1): " ttoffGameServer

export TTOFF_PLAY_TOKEN=${ttoffPlayToken}
export TTOFF_GAME_SERVER=${ttoffGameServer}
export TTOFF_GAME_MODE=0

/usr/bin/python3 -m toontown.launcher.ToontownOfflineQuickStartLauncher
