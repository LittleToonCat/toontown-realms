from direct.actor import Actor
from direct.interval.IntervalGlobal import *

from panda3d.toontown import CFSpeech, CFTimeout

from toontown.episodes import EpisodeLocalizer
from otp.otpbase import OTPLocalizer

from panda3d.core import *

from toontown.avatar import ToontownAvatarUtils
from toontown.battle import MovieUtil
from toontown.episodes import DistributedEpisodeZone
from toontown.episodes import EpisodeConfig
from toontown.toonbase import ToontownGlobals
from toontown.toonbase.ToontownTypes import CogQuoteIndex

import random


class EP02DistributedCogBar(DistributedEpisodeZone.DistributedEpisodeZone):

    def __init__(self, cr):
        DistributedEpisodeZone.DistributedEpisodeZone.__init__(self, cr)
        self.episodeZoneId = EpisodeConfig.EP02_HIGH_RISE_BAR

        self.props = []
        self.cogs = []
        self.seatedCogs = []
        self.cooldown = False
        self.__bigCheeseDoneMsg = None

    def disable(self):
        for prop in self.props:
            prop.removeNode()

        self.props = []

        render.clearOccluder()

        for cog in self.cogs + self.seatedCogs:
            cog.disableBattleDetect()
            cog.removeActive()
            cog.delete()

        if hasattr(self, 'bottomFeeder') and self.bottomFeeder:
            self.bottomFeeder.delete()

        taskMgr.remove(self.uniqueName('seatedCogPhrase'))

        self.cogs = []
        self.seatedCogs = []

        DistributedEpisodeZone.DistributedEpisodeZone.disable(self)

    def generateGeom(self):
        self.geom = loader.loadModel('phase_14/models/modules/cog-bar')
        self.geom.reparentTo(render)

        occluders = loader.loadModel('phase_14/models/modules/culling-cog-bar')
        occluders.reparentTo(self.geom)
        occluders = self.geom.findAllMatches('**/+OccluderNode')
        for occluder in occluders:
            render.setOccluder(occluder)

        self.props = []
        for prop in ToontownGlobals.ShortWorkBarProps:
            model = loader.loadModel('phase_%s/models/%s/%s' % (prop[0], prop[1], prop[2]))
            model.reparentTo(self.geom)
            model.setPos(prop[3])
            model.setHpr(prop[4])
            self.props.append(model)

        tableNum = -1
        tableHpr = 0
        for table in self.geom.findAllMatches('**/Table_Banquet'):
            tableNum = tableNum + 1
            tableHpr = tableHpr + 90
            tableNode = table.attachNewNode('table_%s' % (tableNum))
            tableNode.setHpr(tableHpr, 0, 0)
            tableNode.setZ(10)
            for seat in range(0, 5):
                seatNode = table.find('table_%s' % (tableNum)).attachNewNode('seat_%s' % (seat))
                seatNode.setPos(ToontownGlobals.ShortWorkBarSeatPos[seat])
                seatNode.setHpr(ToontownGlobals.ShortWorkBarSeatHpr[seat])

        self.props[0].find('**/left_door').setPos(3.5, 0, 0)
        self.props[0].find('**/right_door').setPos(-3.5, 0, 0)
        self.props[1].find('**/left_door').setPos(3.5, 0, 0)
        self.props[1].find('**/right_door').setPos(-3.5, 0, 0)

        self.bottomFeeder = Actor.Actor('phase_14/models/char/cogcan-mod',
                                        {'neutral': 'phase_14/models/char/cogcan-neutral',
                                         'reveal': 'phase_14/models/char/cogcan-reveal',
                                         'examine': 'phase_14/models/char/cogcan-examine',
                                         'escape': 'phase_14/models/char/cogcan-escape'})
        self.bottomFeeder.reparentTo(self.geom)
        self.bottomFeeder.setPosHpr(-2.88, -59.02, 0, 180, 0, 0)
        self.bottomFeeder.loop('neutral')

        foodLocation = self.geom.attachNewNode('foodLocation')
        foodLocation.setPos(-38.49, -49.28, 4.1)

        serveLocation = self.geom.attachNewNode('serveLocation')
        serveLocation.setPos(-10.25, -55.69, 4.4)

        mingler = ToontownAvatarUtils.createCog('m', 38.386, 101.617, 0.325, 41.519, 0, 0, parent=self.geom, level=7,
                                                do=self, callback=self.speakDialog, extraArgs=[0])
        self.cogs.append(mingler)

        telemarketer = ToontownAvatarUtils.createCog('tm', -42.535, 99.554, 0.325, 44, 0, 0, parent=self.geom,
                                                     level=5, do=self, callback=self.speakDialog, extraArgs=[1])
        self.cogs.append(telemarketer)

        legalEagle = ToontownAvatarUtils.createCog('le', -50.906, 108.119, 0.325, 224, 0, 0, parent=self.geom,
                                                   level=11, do=self, callback=self.speakDialog, extraArgs=[2])
        self.cogs.append(legalEagle)

        bigCheese = ToontownAvatarUtils.createCog('tbc', -14.87, -47.67, -0.225, 174.0, 0.0, 0.0, anim='sit',
                                                  parent=self.geom, level=50, do=self, callback=self.speakDialog,
                                                  extraArgs=[3])
        self.cogs.append(bigCheese)
        bigCheese.nametag3d.setZ(9)

        bigWig = ToontownAvatarUtils.createCog('bw', -38.49, -47.28, -0.224, 174.0, 0.0, 0.0, anim='sit', do=self)
        self.cogs.append(bigWig)

        loanShark = ToontownAvatarUtils.createCog('ls', 52.5, -57.81, 0.1259, 403.0, 0.0, 0.0, isWaiter=True, do=self)
        self.cogs.append(loanShark)

        corporateRaider = ToontownAvatarUtils.createCog('cr', -53.62, 50.942, -2.723, 211.0, 0.0, 0.0, anim='sit',
                                                        do=self, callback=self.speakDialog, extraArgs=[6])
        self.cogs.append(corporateRaider)

        beanCounter = ToontownAvatarUtils.createCog('bc', -42.59, -55.69, -0.224, 0.0, 0.0, 0.0, isWaiter=True, do=self)
        self.cogs.append(beanCounter)

        for cog in self.cogs:
            cog.addActive()

        pencilPusher = ToontownAvatarUtils.createCog('p', 31.649, 205.79, 0.325, -180, 0.0, 0.0, level=2, do=self)
        pencilPusher.hide()
        self.cogs.append(pencilPusher)

        for cog in self.cogs:
            cog.setActiveShadow(0)

        cogs = {'pp': (0.1, -9.5), 'tw': (0.3, -10.5), 'sc': (0.1, -10), 'nc': (0.1, -10), 'rb': (0.15, -10.5),
                'f': (0.01, -10), 'ym': (0.03, -9.5), 'mm': (0.03, -9.5), 'hh': (0.03, -10), 'tbc': (0.04, -10.5),
                'bf': (0.01, -10), 'dt': (0.03, -9.5), 'bs': (0.03, -9.5), 'le': (0.03, -10.5), 'bw': (0.04, -10.5),
                'cc': (0.01, -9.5), 'nd': (0.03, -9.5), 'gh': (0.03, -10.5), 'tf': (0.03, -9.5), 'm': (0.03, -10),
                'mh': (0.04, -10.5)}
        chances = []
        for chance in list(cogs.values()):
            chances.append(chance[0])
        seatNum = -1
        for cog in range(0, 35):
            p = chances[0]
            x = random.random()
            i = 0
            while x > p:
                i = i + 1
                p = p + chances[i]
            randCog = list(cogs.keys())[i]
            z = cogs.get(randCog)[1]
            seatNum = seatNum + 1
            seat = ToontownGlobals.ShortWorkBarSeating[seatNum]
            seatNode = render.find('**/table_%s/**/seat_%s' % (seat[0], seat[1])).attachNewNode('cog_%s' % (seatNum))
            newCog = ToontownAvatarUtils.createCog(randCog, z=z, anim='sit', parent=seatNode)
            newCog.addActive()
            newCog.nametag3d.stash()
            newCog.setActiveShadow(0)
            self.seatedCogs.append(newCog)

        # Apply a hardware animation shader for performance
        attr = ShaderAttrib.make(Shader.load(Shader.SLGLSL,
                                             fragment = 'phase_3/shaders/ttoff_sha_av_hw.frag',
                                             vertex = 'phase_3/shaders/ttoff_sha_av_hw.vert'))
        attr = attr.setFlag(ShaderAttrib.F_hardware_skinning, True)
        for cog in self.cogs + self.seatedCogs:
            cog.setAttrib(attr)

        taskMgr.doMethodLater(1.25, self.generatePhrase, self.uniqueName('seatedCogPhrase'))

    def generatePhrase(self, task):
        cog = random.choice(self.seatedCogs)

        seq = Sequence(Wait(random.randint(2, 8)), Func(cog.nametag3d.unstash),
                       self.getChatSequence(cog, random.choice(
                           EpisodeLocalizer.ShortWorkCogGarble), chatFlags=CFSpeech,
                                            wait=4.5, postClear=True), Func(cog.nametag3d.stash))
        seq.start()
        name = 'phraseIval-%s' % self.seatedCogs.index(cog)
        self.storeInterval(seq, name)

        return task.again

    def generateMovie(self):
        base.cr.episodeManager.setEpisodeStatus(EpisodeConfig.EP02_HIGH_RISE_HALLWAY, 2)

        self.movie = Sequence(Func(self.toon.setPosHpr, -7.67, 185.64, 0, 180, 0, 0))

        episodeStatus = base.cr.episodeManager.getEpisodeStatus(self.episodeZoneId)
        bathroomStatus = base.cr.episodeManager.getEpisodeStatus(EpisodeConfig.EP02_HIGH_RISE_BATHROOM)
        if episodeStatus == 0 and bathroomStatus == 1:
            self.movie.append(Wait(1.0))
            self.movie.append(self.getChatSequence(self.toon,
                                                   EpisodeLocalizer.ShortChangeBarDialogue, preClear=True))
            self.movie.append(Func(self.playChat, self.toon, wait=4.0, postClear=True))     # clear chat after a bit of time
            base.cr.episodeManager.setEpisodeStatus(EpisodeConfig.EP02_HIGH_RISE_BAR, 1)

        def foodAttach(diner, can):
            foodModel = can
            (foodModel.reparentTo(diner.getRightHand()),)
            (foodModel.setHpr(Point3(0, -94, 0)),)
            (foodModel.setPos(Point3(-0.15, -0.7, -0.4)),)
            scaleAdj = 0.8
            (foodModel.setPos(Point3(-0.25, -0.85, -0.34)),)
            oldScale = foodModel.getScale()
            newScale = oldScale * scaleAdj
            foodModel.setScale(newScale)

        def foodDetach(diner):
            foodModel = diner.getRightHand().getChild(0)
            (foodModel.reparentTo(render.find('**/foodLocation')),)
            (foodModel.setPosHpr(0, 0, 0, 0, 0, 0),)
            scaleAdj = 1
            oldScale = foodModel.getScale()
            newScale = oldScale / scaleAdj
            foodModel.setScale(newScale)

        loanShark = self.cogs[5]
        beanCounter = self.cogs[7]
        bigWig = self.cogs[4]
        request = random.choice(EpisodeLocalizer.ShortWorkBarRequestDialogue)
        dialogue = EpisodeLocalizer.ShortWorkBarWaiterDialogue
        foodModel = loader.loadModel('phase_12/models/bossbotHQ/canoffood')
        foodModel.setScale(ToontownGlobals.BossbotFoodModelScale)
        foodModel.setHpr(52.1961, 180.4983, -4.2882)
        loanSharkFood = foodModel.copyTo(loanShark.getRightHand())
        loanSharkFood.hide()
        beanCounterFood = foodModel.copyTo(beanCounter.getRightHand())
        beanCounterFood.hide()
        pickupFoodSfx = loader.loadSfx('phase_6/audio/sfx/SZ_MM_gliss.ogg')
        serveFoodSfx = loader.loadSfx('phase_4/audio/sfx/MG_sfx_travel_game_bell_for_trolley.ogg')
        ivalDuration = 1.5
        foodLocation = self.geom.find('**/foodLocation')
        serveLocation = self.geom.find('**/serveLocation')
        y = self.getRandomPos()
        seq = Sequence(Func(loanShark.setH, 43), Func(loanShark.loop, 'walk'),
                       LerpPosInterval(loanShark, 1.0, (46.03, -51.63, 0)),
                       LerpHprInterval(loanShark, 0.5, (90, 0, 0)), LerpPosInterval(loanShark, 5.0, (-3.15, -51.63, 0)),
                       Func(loanShark.loop, 'neutral'), Wait(0.75),
                       self.getChatSequence(loanShark, dialogue[0] % request, chatFlags=CFSpeech | CFTimeout, wait=3.0, postClear=True),
                       Func(beanCounter.loop, 'walk'), LerpHprInterval(beanCounter, 0.5, (-90, 0, 0)),
                       Func(beanCounter.loop, 'neutral'), Wait(0.5),
                       self.getChatSequence(beanCounter, dialogue[1], chatFlags=CFSpeech | CFTimeout, wait=1.0, postClear=True),
                       Parallel(
                           Sequence(Func(beanCounter.loop, 'walk'),
                                    LerpPosInterval(beanCounter, 1.0, (-38.71, -55.69, -0.224)),
                                    Func(beanCounter.loop, 'neutral'), Wait(0.5), Func(beanCounter.loop, 'walk'),
                                    LerpHprInterval(beanCounter, 0.5, (0, 0, 0)), Func(beanCounter.loop, 'neutral'),
                                    Wait(1.0),
                                    self.getChatSequence(beanCounter, dialogue[2], chatFlags=CFSpeech | CFTimeout,
                                                         wait=4.0, postClear=True),
                                    Wait(1.0),
                                    self.getChatSequence(beanCounter, dialogue[3], chatFlags=CFSpeech | CFTimeout,
                                                         wait=2.0, postClear=True),
                                    Func(beanCounter.loop, 'walk'),
                                    LerpHprInterval(beanCounter, 0.5, (-90, 0, 0)),
                                    LerpPosInterval(beanCounter, 2.5, (-19.42, -55.69, -0.224)),
                                    LerpHprInterval(beanCounter, 0.5, (-180, 0, 0)),
                                    LerpPosInterval(beanCounter, 0.5, (-19.42, -57.46, -0.224)),
                                    Func(base.playSfx, pickupFoodSfx, node=beanCounter.getRightHand()),
                                    Func(beanCounterFood.show), Func(beanCounter.loop, 'tray-walk'), Wait(0.5),
                                    LerpPosInterval(beanCounter, 0.5, (-19.42, -55.69, -0.224)),
                                    LerpHprInterval(beanCounter, 0.5, (-270, 0, 0)),
                                    LerpPosInterval(beanCounter, 2.5, (-38.71, -55.69, -0.224)),
                                    LerpHprInterval(beanCounter, 0.5, (-360, 0, 0)),
                                    self.getChatSequence(beanCounter, dialogue[4], chatFlags=CFSpeech | CFTimeout, wait=2.0, postClear=True), # 19 seconds
                                    Func(beanCounterFood.find('**/tray').hide),
                                    Func(beanCounterFood.wrtReparentTo, foodLocation),
                                    Func(beanCounter.loop, 'neutral'),
                                    Parallel(SoundInterval(serveFoodSfx, node=beanCounterFood),
                                             ProjectileInterval(beanCounterFood,
                                                                duration=ivalDuration,
                                                                startPos=beanCounterFood.getPos(foodLocation),
                                                                endPos=foodLocation.getPos(foodLocation)),
                                             LerpHprInterval(beanCounterFood, ivalDuration, Point3(0, -360, 0))),
                                    Wait(1.0), Func(beanCounter.loop, 'walk'),
                                    LerpHprInterval(beanCounter, 0.5, (-450, 0, 0)),
                                    LerpPosInterval(beanCounter, 2.5, (-19.42, -55.69, -0.224)),
                                    LerpHprInterval(beanCounter, 0.5, (-540, 0, 0)),
                                    Func(base.playSfx, pickupFoodSfx, node=beanCounter.getRightHand()),
                                    Func(loanSharkFood.find('**/tray').show),
                                    Func(loanSharkFood.reparentTo, beanCounter.getRightHand()),
                                    Func(loanSharkFood.setHpr, 52.1961, 180.4983, -4.2882),
                                    Func(beanCounter.loop, 'tray-walk'), Wait(0.5),
                                    LerpPosInterval(beanCounter, 0.5, (-19.42, -55.69, -0.224)),
                                    LerpHprInterval(beanCounter, 0.5, (-450, 0, 0)),
                                    LerpPosInterval(beanCounter, 0.5, (-17.42, -55.69, -0.224)),
                                    Func(beanCounter.loop, 'tray-neutral'), Wait(0.75),
                                    Func(loanSharkFood.reparentTo, serveLocation),
                                    Func(loanSharkFood.setHpr, 0, 0, 0), Func(beanCounter.loop, 'neutral'), Wait(4.0),
                                    self.getChatSequence(beanCounter, dialogue[5], chatFlags=CFSpeech | CFTimeout,
                                                         wait=1.0, postClear=True),
                                    Func(beanCounter.loop, 'walk'),
                                    LerpHprInterval(beanCounter, 1.0, (-270, 0, 0)),
                                    LerpPosInterval(beanCounter, 3.5, (-38.71, -55.69, -0.224)),
                                    LerpHprInterval(beanCounter, 1.0, (-360, 0, 0)), Func(beanCounter.loop, 'neutral'),
                                    Wait(0.5), Func(base.playSfx, pickupFoodSfx, node=beanCounter.getRightHand()),
                                    Func(beanCounter.loop, 'tray-neutral'), Func(beanCounterFood.find('**/tray').show),
                                    Func(beanCounterFood.reparentTo, beanCounter.getRightHand()),
                                    Func(beanCounterFood.setHpr, 52.1961, 180.4983, -4.2882),
                                    Func(beanCounterFood.setPos, 0, 0, 0), Func(beanCounterFood.setScale, 1), Wait(0.5),
                                    Func(beanCounter.loop, 'tray-walk'),
                                    LerpHprInterval(beanCounter, 0.5, (-270, 0, 0)),
                                    LerpPosInterval(beanCounter, 2.5, (-52.59, -55.69, -0.224)),
                                    LerpHprInterval(beanCounter, 0.5, (-360, 0, 0)),
                                    Func(beanCounter.setH, 0), Func(beanCounter.loop, 'tray-neutral'), Wait(0.5),
                                    Func(beanCounterFood.hide), Func(self.geom.find('**/strayCan').show),
                                    Func(beanCounter.loop, 'neutral'), Wait(1.0), Func(beanCounter.loop, 'walk'),
                                    LerpHprInterval(beanCounter, 0.5, (-90, 0, 0)),
                                    LerpPosInterval(beanCounter, 2.5, (-42.59, -55.69, -0.224)),
                                    LerpHprInterval(beanCounter, 0.5, (0, 0, 0)),
                                    Func(beanCounter.loop, 'neutral')),
                           Sequence(Wait(1.0), self.getChatSequence(bigWig, dialogue[6], chatFlags=CFSpeech | CFTimeout,
                                                                    wait=4.5, postClear=True),
                                    self.getChatSequence(bigWig, dialogue[7] % request, chatFlags=CFSpeech | CFTimeout,
                                                         wait=6.0, postClear=True),
                                    self.getChatSequence(bigWig, dialogue[8], chatFlags=CFSpeech | CFTimeout, wait=3.0, postClear=True),
                                    Wait(5.0),
                                    ActorInterval(bigWig, 'sit', duration=5),
                                    ActorInterval(bigWig, 'sit-eat-in', startFrame=0, endFrame=6),
                                    Func(foodAttach, bigWig, beanCounterFood),
                                    ActorInterval(bigWig, 'sit-eat-in', startFrame=6, endFrame=32),
                                    ActorInterval(bigWig, 'sit-eat-loop', duration=10, loop=1),
                                    ActorInterval(bigWig, 'sit-eat-out', startFrame=0, endFrame=12),
                                    Func(foodDetach, bigWig),
                                    ActorInterval(bigWig, 'sit-eat-out', startFrame=12, endFrame=21),
                                    Func(bigWig.loop, 'sit')),
                           Sequence(Wait(0.5), Func(loanShark.loop, 'walk'), LerpHprInterval(loanShark, 0.5, (0, 0, 0)),
                                    LerpPosInterval(loanShark, 2.5, (-3.15, -37.01, 0)),
                                    LerpHprInterval(loanShark, 0.5, (90, 0, 0)),
                                    LerpPosInterval(loanShark, 5.0, (-51.06, -37.01, 0)),
                                    LerpHprInterval(loanShark, 0.5, (180, 0, 0)),
                                    LerpPosInterval(loanShark, 1.5, (-51.06, -44.59, 0)),
                                    Func(self.geom.find('**/strayCan').hide),
                                    Func(base.playSfx, pickupFoodSfx, node=loanShark.getRightHand()),
                                    Func(loanSharkFood.show), Func(loanShark.setPlayRate, -1.0, 'tray-walk'),
                                    Func(loanShark.loop, 'tray-neutral'),
                                    Wait(0.5), Func(loanShark.loop, 'tray-walk'),
                                    LerpPosInterval(loanShark, 1.5, (-51.06, -37.01, 0)),
                                    Func(loanShark.setPlayRate, 1.0, 'tray-walk'),
                                    LerpHprInterval(loanShark, 0.5, (270, 0, 0)),
                                    LerpPosInterval(loanShark, 5.0, (-3.15, -37.01, 0)),
                                    LerpHprInterval(loanShark, 0.5, (180, 0, 0)),
                                    LerpPosInterval(loanShark, 2.5, (-3.15, -53.63, 0)),
                                    Func(loanSharkFood.find('**/tray').hide),
                                    Func(loanSharkFood.wrtReparentTo, self.bottomFeeder),
                                    Func(loanShark.loop, 'neutral'),
                                    Parallel(SoundInterval(serveFoodSfx, node=loanSharkFood),
                                             ProjectileInterval(loanSharkFood,
                                                                duration=ivalDuration,
                                                                endPos=self.bottomFeeder.getPos(self.bottomFeeder)),
                                             LerpHprInterval(loanSharkFood, ivalDuration, Point3(0, -360, 0))),
                                    Wait(1.0), Func(loanShark.loop, 'walk'),
                                    LerpHprInterval(loanShark, 0.5, (90, 0, 0)), Func(loanShark.loop, 'neutral'),
                                    Wait(4.75), Func(loanSharkFood.reparentTo, loanShark.getRightHand()),
                                    Func(loanSharkFood.setHpr, 52.1961, 180.4983, -4.2882),
                                    Func(base.playSfx, pickupFoodSfx, node=loanShark.getRightHand()),
                                    Func(loanShark.loop, 'tray-neutral'), Wait(1.0),
                                    self.getChatSequence(loanShark, dialogue[8], chatFlags=CFSpeech | CFTimeout,
                                                         wait=1.0, postClear=True),
                                    Func(loanShark.loop, 'tray-walk'), LerpHprInterval(loanShark, 0.5, (0, 0, 0)),
                                    LerpPosInterval(loanShark, (abs(loanShark.getY()) - abs(y)) / 5, (-3.15, y, 0)),
                                    LerpHprInterval(loanShark, 0.5, (-90, 0, 0)),
                                    LerpPosInterval(loanShark, 5.0, (52.5, y, 0)),
                                    LerpHprInterval(loanShark, 0.5, (-225, 0, 0)), Func(loanShark.loop, 'tray-neutral'),
                                    Wait(1.0), Func(loanSharkFood.find('**/tray').hide),
                                    Func(loanSharkFood.wrtReparentTo, self.geom),
                                    Func(loanShark.loop, 'neutral'),
                                    Parallel(SoundInterval(serveFoodSfx, node=loanSharkFood),
                                             ProjectileInterval(loanSharkFood, duration=ivalDuration,
                                                                endPos=(42, y - 9, 4)),
                                             LerpHprInterval(loanSharkFood, ivalDuration, Point3(0, -360, 0))),
                                    Wait(0.75), Func(loanShark.loop, 'walk'),
                                    LerpHprInterval(loanShark, 0.5, (-180, 0, 0)),
                                    LerpPosInterval(loanShark, (abs(-57.81) - abs(y)) / 5, (52.5, -57.81, 0)),
                                    LerpHprInterval(loanShark, 0.75, (-317, 0, 0)), Func(loanShark.loop, 'neutral'),
                                    Wait(3.0), LerpScaleInterval(loanSharkFood, 0.5, (0.01, 0.01, 0.01)),
                                    Func(loanSharkFood.hide), Func(loanSharkFood.setScale, 1),
                                    Func(loanSharkFood.find('**/tray').show),
                                    Func(loanSharkFood.setHpr, 52.1961, 180.4983, -4.2882),
                                    Func(loanSharkFood.setPos, 0, 0, 0),
                                    Func(loanSharkFood.reparentTo, loanShark.getRightHand()))
                       )
        )
        seq.loop()
        name = 'loanSharkIval'
        self.storeInterval(seq, name)

    def getRandomPos(self):
        yPositions = (25, 0, -24)
        return random.choice(yPositions)

    def speakDialog(self, type, collEntry):
        if self.getCooldown():
            return
        self.setCooldown(True)

        type = type[0]
        genericTypes = ('m', 'tm', 'le')
        cflags = CFSpeech | CFTimeout
        wait = 4.0
        if type in range(0, 3):
            cog = self.cogs[type]
            phrases = base.cr.dataPackMgr.getCogQuotesByType(genericTypes[type], CogQuoteIndex.FACEOFF_TAUNTS)
            dialogue = random.choice(phrases)
            self.playChat(cog, dialogue, chatFlags=cflags, wait=wait, postClear=True)
        elif type == 3:
            self.handleBigCheeseMovie()
            return
        elif type == 6:
            cog = self.cogs[type]
            phrase = EpisodeLocalizer.ShortWorkRaiderDialogue
            self.playChat(cog, phrase, chatFlags=cflags, wait=wait, postClear=True)

        taskMgr.doMethodLater(4.0, self.setCooldown, self.uniqueName('setCooldown'), extraArgs=[False])

    def setCooldown(self, state):
        self.cooldown = state

    def getCooldown(self):
        return self.cooldown

    def handleBigCheeseMovie(self):
        bigCheese = self.cogs[3]
        dialogue = EpisodeLocalizer.ShortWorkDemotionDialogue
        episodeStatus = base.cr.episodeManager.getEpisodeStatus(EpisodeConfig.EP02_HIGH_RISE_BATHROOM)
        if episodeStatus == 1:
            dialogue = EpisodeLocalizer.ShortWorkPromotionDialogue

        self.lockToon()
        self.toon.suit.loop('neutral')

        self.__bigCheeseDoneMsg = "doneChatPage"
        if hasattr(bigCheese, "uniqueName"):
            self.__bigCheeseDoneMsg = bigCheese.uniqueName(self.__bigCheeseDoneMsg)
        self.notify.debug("Big Cheese - done event: {}".format(self.__bigCheeseDoneMsg))
        self.acceptOnce(self.__bigCheeseDoneMsg, self.__handleBigCheesePageDone)
        base.cr.episodeManager.addActiveAvatar(bigCheese, hideNametag2d=True, hideNametag3d=False)
        base.camera.setPosHpr(Point3(-21, -60, 8.5), Point3(-22, -5, 1.1))
        self.setLocalPageChat(bigCheese, dialogue, False)

    def __handleBigCheesePageDone(self, elapsed=None):
        if self.__bigCheeseDoneMsg is not None:
            self.ignore(self.__bigCheeseDoneMsg)
            self.__bigCheeseDoneMsg = None

            bigCheese = self.cogs[3]
            base.cr.episodeManager.removeActiveAvatar(bigCheese)

            self.playEndingMovie()
        else:
            self.notify.warning("Um, why are we trying to finish an episode right now?")

    def playEndingMovie(self):
        pencilPusher = self.cogs[8]
        pencilPusher.addActive()
        pencilPusher.show()
        bigCheese = self.cogs[3]

        elevator = self.props[1]
        elevatorOpenSfx = base.loader.loadSfx('phase_5/audio/sfx/elevator_door_open.ogg')
        elevatorCloseSfx = base.loader.loadSfx('phase_5/audio/sfx/elevator_door_close.ogg')
        dialogue = EpisodeLocalizer.ShortWorkPromotionSceneDialogue

        episodeStatus = base.cr.episodeManager.getEpisodeStatus(EpisodeConfig.EP02_HIGH_RISE_BATHROOM)
        if episodeStatus == 0:

            if not config.GetBool('cog-bar-short-death', False):
                def removeDeathSuit(suit, deathSuit):
                    if not deathSuit.isEmpty():
                        deathSuit.detachNode()
                        suit.cleanupLoseActor()

                self.generateStory()
                self.story.hide()
                self.story.setPos(-0.8, 0, -0.5)

                deathSuit = self.toon.suit.getLoseActor()
                ival = Sequence(Func(deathSuit.setPos, self.toon.getPos()), Func(deathSuit.setHpr, self.toon.getHpr()),
                                Func(self.toon.hide), Func(deathSuit.wrtReparentTo, render),
                                ActorInterval(deathSuit, 'lose', duration=MovieUtil.SUIT_LOSE_DURATION),
                                Func(removeDeathSuit, self.toon.suit, deathSuit)
                                )
                spinningSound = base.loader.loadSfx('phase_3.5/audio/sfx/Cog_Death.ogg')
                deathSound = base.loader.loadSfx('phase_3.5/audio/sfx/ENC_cogfall_apart.ogg')
                deathSoundTrack = Sequence(Wait(0.8), SoundInterval(spinningSound, duration=1.2, startTime=1.5, volume=0.2,
                                                                    node=deathSuit),
                                           SoundInterval(spinningSound, duration=3.0, startTime=0.6, volume=0.8,
                                                         node=deathSuit),
                                           SoundInterval(deathSound, volume=0.32, node=deathSuit))
                deathIval = Parallel(ival, deathSoundTrack)
                seq = Sequence(deathIval, Wait(1.0), Func(self.enterText, self.story),
                               Func(self.speakText, self.story, EpisodeLocalizer.ShortWorkDemoteCard[0]), Wait(9.0),
                               Func(self.speakText, self.story, EpisodeLocalizer.ShortWorkDemoteCard[1]), Wait(4.5),
                               Func(self.leaveText, self.story), Wait(1.5), Func(base.transitions.irisOut, 2.0), Wait(3.0),
                               Func(self.releaseToon), Func(self.endEpisode))
            else:
                # This is so we can blaze through while testing
                seq = Sequence(Func(base.transitions.irisOut), Func(self.releaseToon), Func(self.endEpisode))
        else:
            seq = Sequence(Func(aspect2d.hide), Func(base.camera.setPosHpr, -53.68, -7.958, 12.353, -167, -4.6, 0.0),
                           LerpPosHprInterval(base.camera, 7.0, (-4.914, -31.29, 3.7207), (-201, 0.64, 0.0),
                                              blendType='easeInOut'),
                           Wait(1.5), Func(base.camera.setPosHpr, -21.21, -67.29, 7.6029, -384, -6.8, 0.0),
                           LerpPosHprInterval(base.camera, 7.0, (-17.09, -58.26, 7.0939), (-382, -4.9, 0.0),
                                              blendType='easeInOut'),
                           Wait(1.5), Func(base.camera.setPosHpr, -13.75, -57.22, 4.3772, -361, 15, 0.0),
                           self.getChatSequence(bigCheese, dialogue[0], chatFlags=CFSpeech | CFTimeout,
                                                wait=5.0),
                           Func(bigCheese.clearChat), Func(base.camera.setPosHpr, 7.7502, 111.45, 13.402, -17.0, -2.2, 0.0),
                           Parallel(Sequence(LerpPosHprInterval(base.camera, 4.0, (20.714, 160.99, 10.284),
                                                                (-16.0, -6.1, 0.0), blendType='easeInOut'),
                                             Wait(1.0), base.camera.posHprInterval(14.0, (-42.29, -81.70, 32), (-14.0, -18.0, 0.0)),
                                             base.camera.posHprInterval(6.5, (-52.87, 28.675, 32), (-135, -22.0, 0.0)),
                                             self.getChatSequence(bigCheese, dialogue[1],
                                                                  chatFlags=CFSpeech | CFTimeout, preClear=True),
                                             base.camera.posHprInterval(6.5, (-17.70, -22.75, 12.041), (-162, -15.0, 0.0)),
                                             Wait(26.0), Func(base.camera.setPosHpr, -16.74, -70, 8.3765, -4.5, -4.3, 0.0),
                                             self.getChatSequence(pencilPusher),
                                             self.getChatSequence(bigCheese, dialogue[7],
                                                                  chatFlags=CFSpeech | CFTimeout, wait=4.0,
                                                                  preClear=True, postClear=True),
                                             self.getChatSequence(bigCheese, dialogue[8],
                                                                  chatFlags=CFSpeech | CFTimeout, wait=5.0,
                                                                  postClear=True),
                                             self.getChatSequence(pencilPusher, dialogue[9],
                                                                  chatFlags=CFSpeech | CFTimeout, preClear=True,
                                                                  wait=2.0),
                                             base.camera.posHprInterval(1, (-15.49, -59.48, 5.9885), (-4.5, 4.7, 0.0)),
                                             Func(aspect2d.show), Func(base.transitions.irisOut, 2.0), Wait(3.0),
                                             Func(self.releaseToon), Func(self.endEpisode)),
                                    Sequence(Parallel(elevator.find('**/left_door').posInterval(2, (0, 0, 0)),
                                                      elevator.find('**/right_door').posInterval(2, (0, 0, 0)),
                                                      Func(elevatorOpenSfx.play)),
                                             Func(pencilPusher.loop, 'walk'),
                                             pencilPusher.posInterval(1.0, (31.649, 200.79, 0.325)),
                                             pencilPusher.hprInterval(0.5, (-201.276, 0.0, 0.0)),
                                             Parallel(pencilPusher.posInterval(12.0, (-6.867, 95.554, 0.325)),
                                                      Sequence(Wait(4.0), Parallel(elevator.find('**/left_door').posInterval(2, (3.5, 0, 0)),
                                                      elevator.find('**/right_door').posInterval(2, (-3.5, 0, 0)),
                                                      Func(elevatorCloseSfx.play)))),
                                             pencilPusher.hprInterval(1.0, (-180, 0.0, 0.0)),
                                             pencilPusher.posInterval(15.0, (-8.807, -42.611, 0.325)),
                                             Func(pencilPusher.loop, 'neutral'),
                                             self.getChatSequence(pencilPusher, dialogue[2],
                                                                  chatFlags=CFSpeech | CFTimeout, wait=3.5),
                                             Func(base.camera.setPosHpr, -13.75, -57.22, 4.3772, -361, 15, 0.0),
                                             Wait(1.0), self.getChatSequence(pencilPusher),
                                             self.getChatSequence(bigCheese, dialogue[3],
                                                                  chatFlags=CFSpeech | CFTimeout, wait=4.0,
                                                                  preClear=True, postClear=True),
                                             self.getChatSequence(pencilPusher, dialogue[4],
                                                                  chatFlags=CFSpeech | CFTimeout, wait=6.0,
                                                                  postClear=True),
                                             self.getChatSequence(pencilPusher, dialogue[5],
                                                                  chatFlags=CFSpeech | CFTimeout, wait=6.0,
                                                                  postClear=True),
                                             self.getChatSequence(pencilPusher, dialogue[6],
                                                                  chatFlags=CFSpeech | CFTimeout))))
        seq.start()
