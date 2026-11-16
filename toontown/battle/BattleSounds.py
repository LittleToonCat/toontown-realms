from panda3d.core import *
from direct.directnotify import DirectNotifyGlobal

from toontown.toonbase import ClientSettings


class BattleSounds:
    notify = DirectNotifyGlobal.directNotify.newCategory('BattleSounds')

    def __init__(self):
        self.setupSearchPath()

    def setupSearchPath(self):
        self.sfxSearchPath = DSearchPath()
        self.sfxSearchPath.appendDirectory(Filename('/phase_3/audio/sfx'))
        self.sfxSearchPath.appendDirectory(Filename('/phase_3.5/audio/sfx'))
        self.sfxSearchPath.appendDirectory(Filename('/phase_4/audio/sfx'))
        self.sfxSearchPath.appendDirectory(Filename('/phase_5/audio/sfx'))

    def clear(self):
        base.sfxMgrBattle.clearCache()

    def getSound(self, name):
        if ClientSettings.MickeyModeEasterEgg.get():
            return base.sfxMgrBattle.getSound("phase_3/audio/dial/mickey.ogg")
        filename = Filename(name)
        found = vfs.resolveFilename(filename, self.sfxSearchPath)
        if not found:
            self.setupSearchPath()
            found = vfs.resolveFilename(filename, self.sfxSearchPath)
        if not found:
            self.notify.warning('%s not found on:' % name)
            print(self.sfxSearchPath)
        else:
            return base.sfxMgrBattle.getSound(filename.getFullpath())
        return sbase.sfxMgrBattle.getNullSound()


globalBattleSoundCache = BattleSounds()
