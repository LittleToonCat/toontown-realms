####################################################################################
#
# Toontown Realms SOFTWARE
# Copyright (c) The Toontown Realms Team.  All rights reserved.
#
# Use of this software by anyone other than those of the Toontown Realms team
# is strictly prohibited without explicit permission from the Toontown Realms team.
# 
# @file ToontownOfflineLauncher.py
# @author jwcotejr
# @date 2018-08-01
#
####################################################################################

import os
import sys
import time

from toontown.launcher.ToontownOfflineLauncherBase import ToontownOfflineLauncherBase
from toontown.toonbase import TTLocalizer

os.environ['LOGFILE_PREFIX'] = 'ttrealms-'


class ToontownOfflineLauncher(ToontownOfflineLauncherBase):
    GameName = 'Toontown Realms'
    LauncherPhases = [3, 3.5, 4, 5, 5.5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 14.5]
    TmpOverallMap = [0.144, 0.148, 0.131, 0.178, 0.027, 0.097, 0.004, 0.042, 0.023, 0.007, 0.009, 0.02, 0.031, 0.019, 0.12]
    ForegroundSleepTime = 0.01
    Localizer = TTLocalizer
    VerifyFiles = 1
    DecompressMultifiles = True

    def __init__(self):
        self.ttoffPlayTokenKey = 'TTOFF_PLAY_TOKEN'
        self.launcherMessageKey = 'LAUNCHER_MESSAGE'
        self.game1DoneKey = 'GAME1_DONE'
        self.game2DoneKey = 'GAME2_DONE'
        self.tutorialCompleteKey = 'TUTORIAL_DONE'
        ToontownOfflineLauncherBase.__init__(self)

        print('\n\nStarting Toontown Realms...')

        print('Current time: ' + time.asctime(time.localtime(time.time())) + ' ' + time.tzname[0])
        print('sys.path = ', sys.path)
        print('sys.argv = ', sys.argv)

        self.mainLoop()

    def getValue(self, key, default=None):
        try:
            return self.getRegistry(key, default)
        except:
            return self.getRegistry(key)

    def setValue(self, key, value):
        self.setRegistry(key, value)

    def getVerifyFiles(self):
        return 1

    def getTestServerFlag(self):
        return self.testServerFlag

    def getGameServer(self):
        return self.gameServer

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

    def getRegistry(self, name, missingValue=None):
        self.notify.info('getRegistry%s' % ((name, missingValue),))
        if missingValue == None:
            missingValue = ''
        value = os.environ.get(name, missingValue)
        try:
            value = int(value)
        except: pass
        return value

    def getCDDownloadPath(self, origPath, serverFilePath):
        return '%s/%s%s/CD_%d/%s' % (origPath, self.ServerVersion, self.ServerVersionSuffix, self.fromCD, serverFilePath)

    def getDownloadPath(self, origPath, serverFilePath):
        return '%s/%s%s/%s' % (origPath, self.ServerVersion, self.ServerVersionSuffix, serverFilePath)

    def getPercentPatchComplete(self, bytesWritten):
        if self.totalPatchDownload:
            return ToontownOfflineLauncherBase.getPercentPatchComplete(self, bytesWritten)
        else:
            return 0

    def hashIsValid(self, serverHash, hashStr):
        return serverHash.setFromDec(hashStr) or serverHash.setFromHex(hashStr)

    def launcherMessage(self, msg):
        ToontownOfflineLauncherBase.launcherMessage(self, msg)
        self.setRegistry(self.launcherMessageKey, msg)

    def getAccountServer(self):
        return ''

    def setTutorialComplete(self):
        self.setRegistry(self.tutorialCompleteKey, 0)

    def getTutorialComplete(self):
        return self.getRegistry(self.tutorialCompleteKey, 0)

    def getGame2Done(self):
        return self.getRegistry(self.game2DoneKey, 0)

    def startGame(self):
        self.newTaskManager()

        from direct.showbase.EventManagerGlobal import eventMgr
        eventMgr.restart()

        from toontown.toonbase import ToontownStart
