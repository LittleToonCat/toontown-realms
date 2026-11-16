####################################################################################
#
# Toontown Realms SOFTWARE
# Copyright (c) The Toontown Realms Team.  All rights reserved.
#
# Use of this software by anyone other than those of the Toontown Realms team
# is strictly prohibited without explicit permission from the Toontown Realms team.
#
# @file ToontownOfflineQuickLauncher.py
# @author jwcotejr
# @date 2019-03-14
#
####################################################################################

import os
from direct.showbase.EventManagerGlobal import *
from toontown.launcher.ToontownOfflineLauncherBase import ToontownOfflineLauncherBase
from toontown.toonbase import TTLocalizer


class ToontownOfflineQuickLauncher(ToontownOfflineLauncherBase):
    GameName = 'Toontown Realms'
    LauncherPhases = [3, 3.5, 4, 5, 5.5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 14.5]
    TmpOverallMap = [0.144, 0.148, 0.131, 0.178, 0.027, 0.097, 0.004, 0.042, 0.023, 0.007, 0.009, 0.02, 0.031, 0.019, 0.12]
    ForegroundSleepTime = 0.001
    Localizer = TTLocalizer

    def __init__(self):
        self.notify.info('Running: ToontownOfflineQuickLauncher')
        ToontownOfflineLauncherBase.__init__(self)
        self.useTTOffSpecificLogin = config.GetBool('ttoff-specific-login', 0)
        self.ttoffPlayTokenKey = 'TTOFF_PLAY_TOKEN'
        self.notify.info('useTTOffSpecificLogin=%s' % self.useTTOffSpecificLogin)
        self.showPhase = -1
        self.maybeStartGame()
        self.mainLoop()

    def getValue(self, key, default = None):
        return os.environ.get(key, default)

    def setValue(self, key, value):
        os.environ[key] = str(value)

    def getTestServerFlag(self):
        return self.getValue('IS_TEST_SERVER', 0)

    def getGameServer(self):
        return self.getValue('TTOFF_GAME_SERVER', '127.0.0.1')

    def getGamemode(self):
        return self.getValue('TTOFF_GAME_MODE', 1)

    def getPlayToken(self):
        playToken = self.getValue(self.ttoffPlayTokenKey)
        self.setValue(self.ttoffPlayTokenKey, '')
        if playToken == 'NO PLAYTOKEN':
            playToken = None
        return playToken

    def setRegistry(self, name, value):
        pass

    def getRegistry(self, name, missingValue = None):
        self.notify.info('getRegistry %s' % ((name, missingValue),))
        self.notify.info('checking env' % os.environ)
        if missingValue == None:
            missingValue = ''
        value = os.environ.get(name, missingValue)
        try:
            value = int(value)
        except:
            pass

        return value

    def getVerifyFiles(self):
        return config.GetInt('launcher-verify', 0)

    def getDownloadPath(self, origPath, serverFilePath):
        return '%s/%s' % (origPath, serverFilePath)

    def getAccountServer(self):
        return ''

    def getGame2Done(self):
        return True

    def startGame(self):
        self.newTaskManager()
        eventMgr.restart()
        from toontown.toonbase import ToontownStart
