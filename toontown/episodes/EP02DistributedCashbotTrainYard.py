from direct.gui.DirectGui import OnscreenText
from direct.interval.IntervalGlobal import *

from panda3d.core import *

from toontown.episodes import EpisodeLocalizer
from toontown.avatar import ToontownAvatarUtils
from toontown.episodes import DistributedEpisodeZone
from toontown.episodes import EpisodeConfig
from toontown.safezone import Train
from toontown.toonbase import TTLocalizer, ToontownGlobals


class EP02DistributedCashbotTrainYard(DistributedEpisodeZone.DistributedEpisodeZone):
    TrackZ = -67
    TrainTracks = [{'start': Point3(-1000, -54.45, TrackZ),
                    'end': Point3(2200, -54.45, TrackZ)},
                   {'start': Point3(1800, -133.45, TrackZ),
                    'end': Point3(-1200, -133.45, TrackZ)},
                   {'start': Point3(-1000, -212.45, TrackZ),
                    'end': Point3(2200, -212.45, TrackZ)},
                   {'start': Point3(1800, -291.45, TrackZ),
                    'end': Point3(-1200, -291.45, TrackZ)}]

    def __init__(self, cr):
        DistributedEpisodeZone.DistributedEpisodeZone.__init__(self, cr)
        self.episodeZoneId = EpisodeConfig.EP02_CASHBOT_HQ_TRAIN_YARD
        self.trains = None
        self.cogs = []

    def disable(self):
        for train in self.trains:
            train.delete()
        self.trains = None

        for cog in self.cogs:
            cog.delete()
        self.cogs = []

        render.clearOccluder()

        base.localAvatar.collisionsOn()

        DistributedEpisodeZone.DistributedEpisodeZone.disable(self)

    def generateGeom(self):
        self.geom = loader.loadModel('phase_10/models/cogHQ/CashBotShippingStation')
        self.geom.reparentTo(render)
        occluders = loader.loadModel('phase_10/models/cogHQ/culling-cashhq-shortwork')
        occluders.reparentTo(self.geom)
        occluders = self.geom.findAllMatches('**/+OccluderNode')
        for occluder in occluders:
            render.setOccluder(occluder)

        elevator = loader.loadModel('phase_10/models/cogHQ/mintElevator.bam')
        elevator.reparentTo(self.geom.find('**/elevator_origin_2'))

        locator = self.geom.find('**/elevator_signorigin_2')
        backgroundGeom = self.geom.find('**/ElevatorFrameFront_2')
        backgroundGeom.node().setEffect(DecalEffect.make())
        signText = OnscreenText(text=TTLocalizer.GlobalStreetNames[12600][-1].upper(),
                                font=ToontownGlobals.getSuitFont(), scale=TTLocalizer.DMEEsignText,
                                fg=(0.87, 0.87, 0.87, 1), mayChange=False, parent=backgroundGeom)
        signText.setPosHpr(locator, 0, 0, 0, 0, 0, 0)
        signText.setDepthWrite(0)

        if not self.trains:
            self.trains = []
            for track in self.TrainTracks:
                train = Train.Train(track['start'], track['end'], self.TrainTracks.index(track), len(self.TrainTracks))
                train.show()
                self.trains.append(train)

    def generateMovie(self):
        self.toon.hide()
        base.camLens.setNearFar(ToontownGlobals.CashbotHQCameraNear, ToontownGlobals.CashbotHQCameraFar)

        self.generateStory()
        self.story.hide()

        # It's possible for the player to get squished
        # by trains in this scene and we don't want that
        base.localAvatar.collisionsOff()

        for cogInfo in ToontownGlobals.ShortWorkTrainYardCogs:
            cog = ToontownAvatarUtils.createCog(cogInfo[0], cogInfo[1], cogInfo[2], cogInfo[3], cogInfo[4], 0, 0,
                                                parent=self.geom, do=self, callback=self.callback)
            if ToontownGlobals.ShortWorkTrainYardCogs.index(cogInfo) != 2:
                cog.loop('walk')
            else:
                cog.loop('sit')
            self.cogs.append(cog)

        # Apply a hardware animation shader for performance
        attr = ShaderAttrib.make(Shader.load(Shader.SLGLSL,
                                             fragment = 'phase_3/shaders/ttoff_sha_av_hw.frag',
                                             vertex = 'phase_3/shaders/ttoff_sha_av_hw.vert'))
        attr = attr.setFlag(ShaderAttrib.F_hardware_skinning, True)
        for cog in self.cogs:
            cog.setAttrib(attr)

        self.movie = Sequence(Func(self.lockToon), Func(base.camera.setPosHpr, 9.6863, 538.98, 28.653, -208, -1.2, 0.0),
                              Parallel(Sequence(Wait(2.0),
                                                LerpPosHprInterval(base.camera, 6.0, pos=(-47.77, 493.02, 35.844),
                                                                   hpr=(-158.0, 0.0, 0.0), blendType='easeInOut'),
                                                Wait(8.0),
                                                Func(base.camera.setPosHpr, 229.93, 213.02, 86.232, -270, 6.25, 0.0),
                                                Func(self.speakText, self.story, EpisodeLocalizer.ShortWorkIntroCard[1])),
                                       Sequence(Wait(7.0), Func(self.enterText, self.story),
                                                Func(self.speakText, self.story, EpisodeLocalizer.ShortWorkIntroCard[0])),
                                       Sequence(Wait(2.0), Parallel(LerpPosInterval(self.cogs[7], 14.0,
                                                                                    pos=(18.914, 253.02, -23.45),
                                                                                    startPos=(-23.96, 187.27, -23.45)),
                                                                    LerpPosInterval(self.cogs[8], 14.0,
                                                                                    pos=(46.739, 269.98, -23.45),
                                                                                    startPos=(120.68, 266.78, -23.45)),
                                                                    LerpPosInterval(self.cogs[9], 14.0,
                                                                                    pos=(109.43, 202.78, -23.45),
                                                                                    startPos=(109.43, 110.41, -23.45)))),
                                       LerpPosInterval(self.cogs[0], 5.0, pos=(-5.209, 532.71, 25.268),
                                                       startPos=(13.111, 515.17, 25.268)),
                                       LerpPosInterval(self.cogs[1], 8.0, pos=(14.976, 527.75, 25.267),
                                                       startPos=(-37.20, 496.70, 25.267))),
                              Wait(8.0), Func(self.leaveText, self.story), Wait(1.0),
                              Func(base.camera.setPosHpr, 254.06, 12.398, -52.93, -134, 0.0, 0.0),
                              LerpPosInterval(base.camera, 6.0, pos=(254.06, 12.398, 12.163), blendType='easeOut'),
                              Wait(3.0), Func(self.story.hide),
                              Func(base.camera.setPosHpr, 134.19, -185.3, -58.39, -80.0, 0.0, 0.0),
                              Func(self.enterText, self.story),
                              Func(self.speakText, self.story, EpisodeLocalizer.ShortWorkIntroCard[2]),
                              Parallel(Sequence(Wait(6.0), Func(self.leaveText, self.story), Wait(1.0),
                                                Func(base.camera.setPosHpr, -23.12, -396.6, -21.66, -193, 32.5, 0.0),
                                                LerpPosInterval(base.camera, 5.0, pos=(2 - 56.80, -534.2, 68.601))),
                                       Sequence(Wait(9.0), Func(base.transitions.fadeOut), Wait(1),
                                                Func(self.toon.attachCamera), Func(self.toon.initializeSmartCamera),
                                                Func(self.toon.activateCamera), Func(self.toon.show),
                                                Func(self.teleportToZone, self.zoneConnections[0])),
                                       LerpPosInterval(self.cogs[6], 7.0, pos=(179.30, -170.3, -63.23),
                                                       startPos=(167.09, -153.6, -63.23)),
                                       LerpPosInterval(self.cogs[5], 7.0, pos=(165.55, -178.6, -63.13),
                                                       startPos=(134.67, -185.4, -63.13)),
                                       LerpPosInterval(self.cogs[4], 7.0, pos=(241.18, -115.7, -63.05),
                                                       startPos=(263.86, -98.31, -63.05)),
                                       LerpPosInterval(self.cogs[3], 8.0, pos=(155.62, -193.1, -63.18),
                                                       startPos=(202.39, -192.1, -63.18))))
