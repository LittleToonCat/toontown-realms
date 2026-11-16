from direct.interval.IntervalGlobal import *
from direct.gui.DirectGui import *

from panda3d.toontown import *

from panda3d.core import *

from toontown.episodes import EpisodeLocalizer
from toontown.episodes import DistributedEpisodeZone
from toontown.episodes import EpisodeConfig
from toontown.toonbase import ToontownGlobals


class EP01DistributedDuckburg(DistributedEpisodeZone.DistributedEpisodeZone):

    def __init__(self, cr):
        DistributedEpisodeZone.DistributedEpisodeZone.__init__(self, cr)
        self.episodeZoneId = EpisodeConfig.EP01_THE_MONEYBIN

    def disable(self):
        DistributedEpisodeZone.DistributedEpisodeZone.disable(self)

        self.moneybin.removeNode()
        del self.moneybin

        self.sunchaser.removeNode()
        del self.sunchaser

        if self.nametag:
            self.nametag.unmanage(base.marginManager)
            self.nametagNP.removeNode()
        del self.nametag
        del self.nametagNP

        self.toontown.removeNode()
        del self.toontown

        self.sky.removeNode()
        del self.sky

        self.midSky.removeNode()
        del self.midSky

        self.nightSky.removeNode()
        del self.nightSky

        del self.fog

        self.title.destroy()
        del self.title

        if hasattr(self, 'flythroughMusic'):
            self.flythroughMusic.stop()
            del self.flythroughMusic

        render.setColorScale(1, 1, 1, 1)

    def generateGeom(self):
        self.geom = loader.loadModel('phase_14/models/modules/duckburg')
        self.geom.setScale(3.0)
        self.geom.reparentTo(render)
        self.geom.find('**/grass').setBin('ground', -10)
        self.geom.find('**/street').setBin('ground', -10)

        self.moneybin = loader.loadModel('phase_14/models/modules/moneybin')
        self.moneybin.setZ(11)
        self.moneybin.setH(-90)
        self.moneybin.setScale(3.0)
        self.moneybin.reparentTo(render)

        self.sunchaser = loader.loadModel('phase_14/models/props/sunchaser')
        self.sunchaser.setPosHpr(-20.61, -89.76, 2.8999, 108.0, 0.0, 0.0)
        self.sunchaser.setScale(5.0)
        self.sunchaser.reparentTo(render)

        dropShadow = loader.loadModel('phase_3/models/props/drop_shadow')
        dropShadow.setColor(0, 0, 0, 0.5)
        dropShadow.setPos(0, 0, -0.55)
        dropShadow.setScale(0.78)
        dropShadow.flattenLight()
        dropShadow.reparentTo(self.sunchaser)

        self.nametag = NametagGroup()
        self.nametag.setAvatar(self.sunchaser)
        self.nametag.setFont(ToontownGlobals.getToonFont())
        self.nametag.setName(EpisodeLocalizer.PrologueLaunchpadMcQuack)
        self.nametag.setActive(0)
        self.nametag.manage(base.marginManager)
        self.nametag.getNametag3d().setBillboardOffset(4)
        nametagNode = self.nametag.getNametag3d().upcastToPandaNode()
        self.nametagNP = render.attachNewNode(nametagNode)
        self.nametagNP.setName('sunchaser')
        pos = self.sunchaser.getPos()
        self.nametagNP.setPos(pos + Vec3(0, 0, 5))

        self.toontown = loader.loadModel('phase_14/models/modules/toontown-outskirts')
        self.toontown.reparentTo(render)
        self.toontown.hide()

        self.sky = loader.loadModel('phase_3.5/models/props/TT_sky')
        self.sky.find('**/cloud1').hide()
        self.sky.find('**/cloud2').hide()
        self.sky.setScale(5.0)
        self.sky.reparentTo(render)

        self.midSky = loader.loadModel('phase_6/models/props/MM_sky')
        self.midSky.setScale(5.0)
        self.midSky.setFogOff()
        self.midSky.reparentTo(render)
        self.midSky.hide()

        self.nightSky = loader.loadModel('phase_8/models/props/DL_sky')
        self.nightSky.setScale(5.0)
        self.nightSky.reparentTo(render)
        self.nightSky.hide()

        self.fog = Fog("fog")
        self.fog.setColor(0, 0, 0)
        self.fog.setExpDensity(0.001)

        self.title = DirectLabel(relief=None, text='', pos=(0, 0, 0), scale=0.15,
                                 text_font=ToontownGlobals.getEpisodeFont(), text_fg=(1, 1, 1, 1),
                                 text_shadow=(0.1, 0.1, 0.1, 1), sortOrder=DGG.NO_FADE_SORT_INDEX)

    def playFlythroughMusic(self):
        self.music.stop()
        del self.music
        self.flythroughMusic = base.loader.loadMusic('phase_14/audio/bgm/DB_flythrough.ogg')
        base.playMusic(self.flythroughMusic, looping = 1)

    def generateMovie(self):
        self.toon.setPosHpr(0.3679, -11.94, 11.599, 167.0, 0.0, 0.0)

        gateLeft = self.geom.find('**/gateleft')
        gateRight = self.geom.find('**/gateright')

        propellerTrack = Parallel(LerpHprInterval(self.sunchaser.find('**/prop_right'), 0.5, (0, 0, 360),
                                                  startHpr=(0, 0, 0)),
                                  LerpHprInterval(self.sunchaser.find('**/prop_left'), 0.5, (0, 0, -360),
                                                  startHpr=(0, 0, 0)))
        skyTrack = LerpHprInterval(self.nightSky, 120.0, (-5.0, -62.0, 0.0), startHpr=(-5.0, -18.0, 0.0))

        dialogue = EpisodeLocalizer.PrologueIntroDialogue

        self.music = base.loader.loadMusic('phase_14/audio/bgm/DB_nbrhood.ogg')

        openSfx = base.loader.loadSfx('phase_5/audio/sfx/CHQ_SOS_cage_door.ogg')
        engineSfx = base.loader.loadSfx('phase_6/audio/sfx/KART_Engine_start_1.ogg')
        runSfx = base.loader.loadSfx('phase_6/audio/sfx/KART_Engine_loop_1.ogg')

        self.generateStory()
        self.story.hide()

        self.movie = Sequence(Func(self.lockToon), Func(base.transitions.fadeOut, t=0),
                              Func(base.camera.setPosHpr, -54.94, -107.2, 13.142, -37.0, 10.0, 0.0),
                              Func(self.speakText, self.title, EpisodeLocalizer.PrologueIntro, scale=1, zPos=0, delay=0.2),
                              Wait(6.0), LerpColorScaleInterval(self.title, 2.0, (1, 1, 1, 0)),
                              Func(base.playMusic, self.music, looping=1), Func(base.transitions.fadeIn, 2.0),
                              Func(base.camera.setPosHpr, -54.94, -107.2, 13.142, -37.0, 10.0, 0.0), Wait(0.2),
                              Func(camera.setPosHpr, 84.466, -99.16, 22.964, 39.2, 5.0, 0.0), Wait(0.2),
                              Func(base.camera.setPosHpr, 92.105, 73.659, 23.051, 128.0, 5.0, 0.0), Wait(0.2),
                              Func(base.camera.setPosHpr, -94.87, 63.166, 22.724, -125.0, 6.25, 0.0), Wait(0.2),
                              Func(base.camera.setPosHpr, -0.336, -31.94, 57.038, -1.0, 3.75, 0.0), Wait(0.2),
                              Func(base.camera.setPosHpr, -0.702, -59.88, 30.007, -1.0, 3.75, 0.0), Wait(0.2),
                              Func(base.camera.setPosHpr, -0.388, -35.94, 14.076, -1.0, 3.75, 0.0), Wait(0.2),
                              Func(base.camera.setPosHpr, -1.863, -148.6, 9.1259, -1.0, 6.75, 0.0), Wait(0.2),
                              Func(base.camera.setPosHpr, -7.886, -21.25, 136.12, -25.0, -78.0, 0.0), Wait(0.2),
                              Func(base.camera.setPosHpr, 26.676, -102.9, 8.9605, 34.0, -4.5, 0.0), Wait(0.2),
                              Func(base.camera.setPosHpr, -99.37, -41.93, 5.3811, -14.0, -0.7, 0.0), Wait(0.2),
                              Func(base.camera.setPosHpr, -54.94, -107.2, 13.142, -37.0, 10.0, 0.0),
                              Parallel(LerpPosHprInterval(base.camera, 5.0, (-10.18, -37.81, 14.630), (-27.0, 0.0, 0.0),
                                                          blendType='easeOut'),
                                       Sequence(Func(self.toon.loop, 'walk'), LerpPosInterval(self.toon, 2.0,
                                                                                              (-0.413, -15.46, 11.599)),
                                                Func(self.toon.loop, 'neutral'),
                                                Func(self.toon.displayTalk, dialogue[0]))),
                              Wait(1.0), Func(self.toon.clearChat), Func(self.toon.displayTalk, dialogue[1]),
                              Wait(4.0), Func(base.camera.setPosHpr, 31.541, -105.2, 5.5300, 44.2, 3.75, 0.0),
                              Func(self.toon.setPosHpr, -4.290, -50.15, 7.2990, 184.0, 0.0, 0.0),
                              Parallel(Sequence(Wait(1.5), Parallel(LerpHprInterval(gateLeft, 1.0, (-90, 0, 0),
                                                                                    blendType='easeInOut'),
                                                                    LerpHprInterval(gateRight, 1.0, (90, 0, 0),
                                                                                    blendType='easeInOut'),
                                                                    LerpPosHprInterval(base.camera, 1.0,
                                                                                       (0.0042, -115.0, 5.5300),
                                                                                       (0.0, 3.75, 0.0),
                                                                                       blendType='easeOut'),
                                                                    Func(base.playSfx, openSfx))),
                                       Sequence(Func(self.toon.loop, 'walk'), Func(self.toon.clearChat),
                                                Parallel(LerpPosInterval(self.toon, 5.0, (-2.548, -71.12, 0.3990)),
                                                         Sequence(Wait(2.0), Func(self.toon.displayTalk, dialogue[2]))),
                                                LerpPosInterval(self.toon, 2.0, (-1.844, -79.59, 0.3990)),
                                                Func(self.toon.loop, 'neutral'), Wait(0.5),
                                                Func(self.toon.loop, 'walk'), Func(self.toon.clearChat),
                                                Parallel(LerpHprInterval(self.toon, 0.75, (141.0, 0, 0)),
                                                         LerpHprInterval(base.camera, 0.75, (25.0, -1.2, 0.0))),
                                                Func(self.toon.loop, 'neutral'), Wait(0.5),
                                                Func(self.toon.displayTalk, dialogue[3]))),
                              Wait(3.0), Func(self.toon.clearChat), Wait(1.0),
                              Func(self.nametag.setChat, dialogue[4], CFSpeech), SoundInterval(engineSfx),
                              Func(base.playSfx, runSfx, looping=1, volume=0.25), Wait(3.0),
                              Func(self.nametag.clearChat), Func(base.transitions.irisOut, 3.0),
                              LerpFunctionInterval(self.music.setVolume, fromData=1, toData=0, duration=3.5),
                              Func(runSfx.stop), Wait(1.0),
                              Func(base.camera.setPosHpr, -174.1, -5.095, 52.843, 16.2, 12.1, 0.0),
                              Func(render.setFog, self.fog), Func(self.playFlythroughMusic),
                              Func(self.sky.hide), Func(self.midSky.show), Func(base.transitions.irisIn, 2.0),
                              Func(propellerTrack.loop),
                              Func(self.sunchaser.setPosHpr, -388.0, 213.93, 18.777, 128.0, -22.0, 0.0),
                              LerpPosInterval(self.sunchaser, 5.5, (-23.99, 498.33, 210.11)),
                              Func(base.camera.setPosHpr, -99.77, 124.22, 24.531, 17.5, 17.5, 0.0),
                              Func(self.sunchaser.setPosHpr, -176.2, 135.84, 44.199, 108.0, 0.0, 0.0), Wait(0.5),
                              LerpPosInterval(self.sunchaser, 4.5, (-55.39, 222.10, 44.199)), Wait(0.5),
                              Func(self.geom.hide), Func(self.moneybin.hide), Func(self.midSky.hide),
                              Func(self.toontown.show), Func(render.clearFog),
                              Func(render.setColorScale, 0.5, 0.5, 0.5, 1.0), Func(self.nightSky.show),
                              Func(base.camera.setPosHpr, 4.0147, -52.28, -9.206, -8.6, 7.5, 0.0), Func(skyTrack.start),
                              Func(self.sunchaser.setPosHpr, 211.46, 515.60, 119.81, -19.0, 12.5, 0.0),
                              Parallel(LerpPosInterval(self.sunchaser, 23.0, (-15.84, -126.3, -31.15)),
                                       Sequence(Func(self.enterText, self.story),
                                                Func(self.speakText, self.story, EpisodeLocalizer.PrologueIntroCard[0]),
                                                Wait(9.0), Func(self.speakText, self.story,
                                                                EpisodeLocalizer.PrologueIntroCard[1], scale=0.06,
                                                                zPos=0.11),
                                                Wait(10.0), Func(self.leaveText, self.story))),
                              Func(propellerTrack.finish), Func(skyTrack.finish), Func(self.toon.attachCamera),
                              Func(self.toon.initializeSmartCamera), Func(self.toon.activateCamera),
                              Func(self.teleportToZone, self.zoneConnections[0]))
