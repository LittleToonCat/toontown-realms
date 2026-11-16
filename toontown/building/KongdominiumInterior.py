from panda3d.core import TextNode, Point3
from direct.showbase.PythonUtil import invertDict
from .ToonInterior import ToonInterior
from toontown.toonbase import ToontownGlobals
import random

songPath2NameDict = invertDict(ToontownGlobals.KongdominiumSongs)


class KongdominiumInterior(ToonInterior):
    def enter(self, requestStatus):
        ToonInterior.enter(self, requestStatus)

        volume = requestStatus.get('musicVolume', 0.7)

        songNamePath = 'phase_14.5/audio/bgm/' + self.activityMusicOverride.getName()
        songName = songPath2NameDict.get(songNamePath)
        if not songName:
            songName = ''
        self.customizeSign(songName)

        taskMgr.doMethodLater(self.activityMusicOverride.length(), self.customMusicTask, 'custom-music-task',
                              extraArgs=[volume], appendTask=True)

    def customMusicTask(self, volume, task):
        music = self.getCustomSong()
        songName = songPath2NameDict.get(music)
        if not songName:
            songName = ''
        self.customizeSign(songName)

        self.activityMusicOverride = loader.loadMusic(music)
        base.playMusic(self.activityMusicOverride, looping=0, volume=volume)

        task.delayTime = self.activityMusicOverride.length() + 2.0
        return task.again

    def customizeSign(self, songName):
        signOrigin = render.find('**/sign_origin;+s')
        if not signOrigin.isEmpty():
            songNameNP = render.find('**/songName')
            if not songNameNP.isEmpty():
                songNameNP.removeNode()

            songNameNP = signOrigin.attachNewNode(TextNode('songName'))
            songNameNP.node().setFont(ToontownGlobals.getSignFont())
            songNameNP.node().setText(songName)
            songNameNP.setDepthWrite(1, 1)
            songNameNP.flattenLight()
            ll = Point3()
            ur = Point3()
            songNameNP.calcTightBounds(ll, ur)
            width = ur[0] - ll[0]
            height = ur[2] - ll[2]
            if width != 0 and height != 0:
                xScale = (4 + 4) / width
                zScale = (1.5 + 3.5) / height
                scale = min(xScale, zScale)
                if len(songName) < 15:
                    scale = scale - 0.85
                xCenter = (ur[0] + ll[0]) / 2.0
                songNameNP.setPos(0 - xCenter * scale, songNameNP.getY() - 0.01, songNameNP.getZ() - 2.5)
                songNameNP.setScale(scale)

    def getCustomSong(self):
        return random.choice(list(ToontownGlobals.KongdominiumSongs.values()))

    def exit(self):
        ToonInterior.exit(self)

        if hasattr(self, 'activityMusicOverride') and self.activityMusicOverride:
            taskMgr.remove('custom-music-task')
