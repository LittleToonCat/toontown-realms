import random

from direct.interval.IntervalGlobal import *

from panda3d.toontown import *

from panda3d.core import *

from otp.otpbase.PythonUtil import weightedChoice
from toontown.avatar import ToontownAvatarUtils
from toontown.episodes import DistributedEpisodeZone
from toontown.episodes import EpisodeConfig
from toontown.episodes.EpisodeGlobals import EP03_03_NPCS, EP03_03_COGS
from toontown.makeatoon import NameGenerator
from toontown.suit.BossCog import BossCog
from toontown.suit.SuitDNA import SuitDNA
from toontown.toon.ToonDNA import ToonDNA
from toontown.toonbase import TTLocalizer, ToontownGlobals


class EP03DistributedSellbotTowers(DistributedEpisodeZone.DistributedEpisodeZone):

    def __init__(self, cr):
        DistributedEpisodeZone.DistributedEpisodeZone.__init__(self, cr)
        self.episodeZoneId = EpisodeConfig.EP03_SELLBOT_TOWERS

    def disable(self):
        DistributedEpisodeZone.DistributedEpisodeZone.disable(self)

    def generateGeom(self):
        base.loader.beginBulkLoad('episode', TTLocalizer.HeadingToHood % {
            'to': TTLocalizer.SellbotTowers[0],
            'hood': TTLocalizer.SellbotTowers[2]
        }, 12, 1, TTLocalizer.TIP_OFFLINE_MODE)
        self.movieStatus = 0
        namegen = NameGenerator.NameGenerator()
        self.geom = loader.loadModel('phase_9/models/cogHQ/BossRoomHQ') # type: NodePath
        base.loader.tick()
        self.cage = self.geom.find('**/cage')
        elevatorEntrance = self.geom.find('**/elevatorEntrance')
        elevatorEntrance.getChildren().detach()
        elevatorEntrance.setScale(1)
        elevatorModel = loader.loadModel('phase_9/models/cogHQ/cogHQ_elevator')
        elevatorModel.reparentTo(elevatorEntrance)
        base.loader.tick()
        self.cageDoor = self.geom.find('**/cage_door')
        self.cage.setScale(1)
        self.geom.reparentTo(render)

        for ramp in self.geom.findAllMatches('**/west_ramp*'): # type: NodePath
            ramp.removeNode()

        self.sky = loader.loadModel('phase_9/models/cogHQ/cog_sky')
        self.sky.reparentTo(render)
        skyInner = self.sky.find('**/InnerGroup')
        skyInner.hide()
        skyMiddle = self.sky.find('**/MiddleGroup')
        skyMiddle.hide()
        base.loader.tick()

        self.vp = BossCog()
        vpDNA = SuitDNA()
        vpDNA.newBossCog('s')
        self.vp.setDNA(vpDNA, 0)
        self.vp.setPosHpr(*ToontownGlobals.SellbotBossBattleOnePosHpr)
        self.vp.reparentTo(render)
        self.vp.loop('Bb_neutral')
        base.loader.tick()

        self.cogs = []

        cogs = (
            ()
        )

        for cogPos in EP03_03_COGS:
            if self.movieStatus == 0:
                cogType = random.choice(('tf', 'm', 'mh'))
            else:
                cogType = random.choice(('cc', 'tm', 'nd', 'gh'))
            cog = ToontownAvatarUtils.createCog(cogType, do = self)
            cog.addActive()
            cog.setPosHpr(self.vp, *cogPos)
            base.loader.tick()
            self.cogs.append(cog)

        self.toons = []

        for npc in EP03_03_NPCS:
            dna = ToonDNA(type = 't')
            randName = namegen.randomNameMoreinfo(boy = dna.gender == 'm', girl = dna.gender == 'f')[
                -1]
            # todo: why the hell isnt the nametag style applying?
            nametag = weightedChoice((
                (50, 100), (30, 0), (30, random.randint(1, 13)),
            ))
            toon = ToontownAvatarUtils.createUniqueToon(name = randName, dna = dna, nametagStyle = nametag,
                                                        colorType = NametagGroup.CCSpeedChat)
            toon.addActive()
            toon.setPosHpr(self.vp, *npc[0])
            toon.loop(npc[1])
            toon.setPickable(1)
            base.loader.tick()
            self.toons.append(toon)

        gsg = base.win.getGsg()
        if gsg:
            self.geom.prepareScene(gsg)

        base.loader.endBulkLoad('episode')

    def generateMovie(self):
        if self.movieStatus == 0:
            self.movie = Sequence(
                    Func(self.lockToon),
                    Func(base.camera.reparentTo, render),
                    Func(base.camera.setPosHpr, Point3(-12.41, -10.08, 0.02), Point3(206.47, 0.00, 0.00)),
                    Parallel(
                        LerpPosInterval(base.camera, 3, Point3(-12.41, -10.08, 0.02)),
                    )
            )
