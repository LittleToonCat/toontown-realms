####################################################################################
#
# Toontown Realms SOFTWARE
# Copyright (c) The Toontown Realms Team.  All rights reserved.
#
# Use of this software by anyone other than those of the Toontown Realms team
# is strictly prohibited without explicit permission from the Toontown Realms team.
# 
# @file ToontownOfflineDummyLauncher.py
# @author jwcotejr
# @date 2019-03-14
#
####################################################################################

from direct.directnotify import DirectNotifyGlobal
from otp.launcher.DummyLauncherBase import DummyLauncherBase
from toontown.launcher.ToontownOfflineLauncher import ToontownOfflineLauncher


class ToontownOfflineDummyLauncher(DummyLauncherBase, ToontownOfflineLauncher):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToontownOfflineDummyLauncher')

    def __init__(self):
        DummyLauncherBase.__init__(self)
        self.setPhaseComplete(1, 100)
        self.setPhaseComplete(2, 100)
        self.setPhaseComplete(3, 100)
        self.tutorialComplete = 1
        self.frequency = 0.0
        self.windowOpen = 0
        self.firstPhase = 3.5
        self.pandaErrorCodeKey = 'PANDA_ERROR_CODE'
        self.goUserName = ''
        self.periodTimeRemainingKey = 'PERIOD_TIME_REMAINING'
        self.periodNameKey = 'PERIOD_NAME'
        self.swidKey = 'SWID'
        self.reg = {}
        self.startFakeDownload()

    def setTutorialComplete(self, complete):
        self.tutorialComplete = complete

    def getTutorialComplete(self):
        return self.tutorialComplete

    def setFrequency(self, freq):
        self.frequency = freq

    def getFrequency(self):
        return self.frequency

    def getUserName(self):
        return 'dummy'

    def getReferrerCode(self):
        return None

    def setRegistry(self, name, value):
        print('setRegistry[%s] = %s' % (name, value))
        self.reg[name] = value

    def getRegistry(self, name, defaultValue = None):
        if name in self.reg:
            value = self.reg[name]
        else:
            value = defaultValue
        print('getRegistry[%s] = %s' % (name, value))
        return value

    def getGame2Done(self):
        return 1

    def recordPeriodTimeRemaining(self, secondsRemaining):
        self.setRegistry(self.periodTimeRemainingKey, secondsRemaining)

    def recordPeriodName(self, periodName):
        self.setRegistry(self.periodNameKey, periodName)

    def recordSwid(self, swid):
        self.setRegistry(self.swidKey, swid)

    def getGoUserName(self):
        return self.goUserName

    def setGoUserName(self, userName):
        self.goUserName = userName

    def getNeedPwForSecretKey(self):
        return 0

    def getGameServer(self):
        return ''
