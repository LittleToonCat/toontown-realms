####################################################################################
#
# Toontown Realms SOFTWARE
# Copyright (c) The Toontown Realms Team.  All rights reserved.
#
# Use of this software by anyone other than those of the Toontown Realms team
# is strictly prohibited without explicit permission from the Toontown Realms team.
# 
# @file ToontownOfflineLauncherBase.py
# @author jwcotejr
# @date 2019-03-14
#
####################################################################################

import os

from direct.directnotify.DirectNotifyGlobal import *
from otp.launcher.LauncherBase import LauncherBase


class ToontownOfflineLauncherBase(LauncherBase):
    notify = directNotify.newCategory('ToontownOfflineLauncher')

    def __init__(self):
        if not os.path.exists('logs/'):
            os.makedirs('logs/')
        LauncherBase.__init__(self)

    def getLogFileName(self):
        return 'logs/ttrealms'

    def setupDownload(self):
        if config.GetBool('do-download', False):
            LauncherBase.setupDownload(self)
        else:
            self.phaseComplete = {1: 100,
                                  2: 100,
                                  3: 100,
                                  3.5: 100,
                                  4: 100,
                                  5: 100,
                                  5.5: 100,
                                  6: 100,
                                  7: 100,
                                  8: 100,
                                  9: 100,
                                  10: 100,
                                  11: 100,
                                  12: 100,
                                  13: 100,
                                  14: 100,
                                  14.5: 100}
            self._downloadComplete = True

