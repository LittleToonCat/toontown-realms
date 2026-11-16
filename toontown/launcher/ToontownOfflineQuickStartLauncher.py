####################################################################################
#
# Toontown Realms SOFTWARE
# Copyright (c) The Toontown Realms Team.  All rights reserved.
#
# Use of this software by anyone other than those of the Toontown Realms team
# is strictly prohibited without explicit permission from the Toontown Realms team.
#
# @file ToontownOfflineQuickStartLauncher.py
# @author jwcotejr
# @date 2019-03-14
#
####################################################################################

from panda3d.core import VirtualFileSystem, ConfigVariableList, Filename
import argparse
import sys

cmd = None
if __debug__:
    from panda3d.core import loadPrcFile
    loadPrcFile('config/general.prc')
    loadPrcFile('config/dev.prc')

    # do this only for dev
    from direct import discord_rpc
    from direct.discord_rpc.util.utils import is_linux, is_windows, get_executable_directory
    cmd = "-m toontown.launcher.ToontownOfflineQuickStartLauncher --discord"
    if is_linux():
        # change this to your terminal name
        cmd = "gnome-terminal -- bash -c \"cd \\\"{}/../..\\\"; python2 {}; exec bash;\"".\
            format(get_executable_directory(), cmd)
    elif is_windows():
        # change this to your liking
        cmd = "cmd.exe /c \"cd /d \"{}\\..\\..\" & python.exe {} --discord\""\
            .format(get_executable_directory(), cmd)
    else:
        # I dunno how the mac one works...
        cmd = "open -a Terminal -- bash -c \"cd \\\"{}/../..\\\"; python {}; exec bash;\"".\
            format(get_executable_directory(), cmd)

    discord_rpc.register_game('461761173814116352', command=cmd)

    parser = argparse.ArgumentParser('TTOffline Quick Launcher')
    parser.add_argument("--discord", help="Start the launcher with a check for a discord join secret",
                        action="store_true")
    args = parser.parse_args()
    if args.discord:
        from os import environ
        import time
        from toontown.toonbase import ToontownSettings


        def readyCallback(current_user):
            print('Our user: {}'.format(current_user))


        def disconnectedCallback(codeno, codemsg):
            print('Disconnected from Discord rich presence RPC. Code {}: {}'.format(
                codeno, codemsg
            ))


        def joinCallback(joinSecret):
            # This is for us to join another game
            if joinSecret is None or joinSecret.split() == '':
                return
            secrets = joinSecret.split('&')
            environ['TTOFF_GAME_SERVER'] = secrets[0]
            environ['DISCORD_JOIN_SECRET'] = secrets[1]
            print("Secrets: {}".format(secrets))


        def errorCallback(errno, errmsg):
            print('An error occurred! Error {}: {}'.format(
                errno, errmsg
            ))


        callbacks = {
            'ready': readyCallback,
            'disconnected': disconnectedCallback,
            'joinGame': joinCallback,
            'spectateGame': None,
            'joinRequest': None,
            'error': errorCallback,
        }
        settings = ToontownSettings.ToontownSettings()
        # set up a temporary rpc connection, just so we can acquire the secrets
        discord_rpc.initialize('461761173814116352', callbacks=callbacks, log=False, auto_update_connection=True,
                               pipe_no=0)
        i = 0
        while not environ.get('DISCORD_JOIN_SECRET') and not environ.get('TTOFF_GAME_SERVER') and i < 20:
            print("Our secrets guarded by the power of 69")
            time.sleep(1.25)
            i += 1
        # shut down the rpc once we either acquire secrets or fail
        discord_rpc.shutdown()
        if not environ.get('DISCORD_JOIN_SECRET') and not environ.get('TTOFF_GAME_SERVER'):
            # either someone thought it would be funny to launch the game with --discord
            # or we legitimately had trouble getting the secret...
            print("Failed to acquire join secret in time; shutting down!")
            sys.exit(128)
else:
    sys.path = ['']


# The VirtualFileSystem, which has already initialized, doesn't see the mount
# directives in the config(s) yet. We have to force it to load those manually:
vfs = VirtualFileSystem.getGlobalPtr()
mounts = ConfigVariableList('vfs-mount')
for mount in mounts:
    mountFile, mountPoint = (mount.split(' ', 2) + [None, None, None])[:2]
    vfs.mount(Filename(mountFile), Filename(mountPoint), 0)

from toontown.launcher.ToontownOfflineQuickLauncher import ToontownOfflineQuickLauncher
launcher = ToontownOfflineQuickLauncher()
launcher.notify.info('Reached end of StartToontownOfflineQuickLauncher.py.')
