from direct.actor import Actor
from direct.interval.IntervalGlobal import *

from toontown.building.ServerTimeClockModel import ServerTimeClockModel
from toontown.episodes import EpisodeLocalizer
from toontown.episodes import DistributedEpisodeZone
from toontown.episodes import EpisodeConfig

from toontown.toonbase import ClientSettings


class EP02DistributedShortChangeOffice(DistributedEpisodeZone.DistributedEpisodeZone):

    def __init__(self, cr):
        DistributedEpisodeZone.DistributedEpisodeZone.__init__(self, cr)
        self.episodeZoneId = EpisodeConfig.EP02_SHORT_CHANGE_OFFICE
        self.clockModel = None

    def disable(self):
        if self.clockModel:
            self.clockModel.cleanup()

        DistributedEpisodeZone.DistributedEpisodeZone.disable(self)

    def generateGeom(self):
        self.geom = loader.loadModel('phase_14/models/modules/cog-office')
        self.geom.reparentTo(render)

        clockNode = self.geom.find('**/clock_locator')
        self.clockModel = ServerTimeClockModel()
        self.clockModel.setHpr(180, 90, 0)
        self.clockModel.reparentTo(clockNode)

        vault = loader.loadModel('phase_10/models/cashbotHQ/VaultDoorCover')
        vault.reparentTo(self.geom)
        vault.setScale(0.5)
        vault.setPosHpr(-13.91, -23.86, 0.0, 180.0, 0.0, 0.0)
        cooler = loader.loadModel('phase_5/models/props/watercooler')
        cooler.reparentTo(self.geom)
        cooler.setPosHpr(11.624, -23.22, 0.8629, -174.0, -123.0, 0.0)

    def generateMovie(self):
        episodeStatus = base.cr.episodeManager.getEpisodeStatus(self.episodeZoneId)
        if episodeStatus == 0:
            base.cr.episodeManager.setEpisodeStatus(self.episodeZoneId, 1)

            self.toon.setCogIndex('sc', 1, 1) 
            self.toon.setPlayerType(3)

            dialogue = EpisodeLocalizer.ShortChangeOfficeDialogue
            self.movie = Sequence(Func(self.lockToon), Func(self.toon.setPosHpr, -1, 19, 1, 0, 0, 0),
                                  Func(self.toon.suit.loop, 'sit'), Func(base.camera.setPosHpr, 6, 10, 3, 40, 14, 0),
                                  Wait(3), self.getChatSequence(self.toon, dialogue[0], wait = 4.5),
                                  self.getChatSequence(self.toon, dialogue[1], wait = 5.5, preClear = True),
                                  self.getChatSequence(self.toon, dialogue[2], wait = 6.0, preClear = True),
                                  self.getChatSequence(self.toon, dialogue[3], wait = 4.0, preClear = True,
                                                       postClear = True),
                                  Parallel(self.playLeaveMovie(),
                                           Sequence(
                                                   Func(self.toon.collisionsOff),
                                                   Wait(1.3),
                                                   Func(base.camera.setPosHpr, -9.66, -19.29, 1.1, -20.2, 8, 0),
                                                   Wait(7.7),
                                                   Func(self.toon.attachCamera),
                                                   Func(self.toon.initializeSmartCamera),
                                                   Func(self.toon.activateCamera),
                                                   Func(self.toon.collisionsOn),
                                                   Func(self.toon.enableAvatarControls))))

        elif episodeStatus == 1:
            base.cr.episodeManager.setEpisodeStatus(EpisodeConfig.EP02_HIGH_RISE_HALLWAY, 0)
            self.movie = Func(self.toon.setPosHpr, 0, -5, 0, 0, 0, 0)

    def playLeaveMovie(self):
        propeller = Actor.Actor('phase_4/models/props/propeller-mod', {'spin': 'phase_4/models/props/propeller-chan'})
        propeller.setBlend(frameBlend=ClientSettings.SmoothAnimations.get())
        propeller.reparentTo(hidden)

        startFly = base.loader.loadSfx('phase_5/audio/sfx/ENC_propeller_out.ogg')
        endFly = base.loader.loadSfx('phase_5/audio/sfx/ENC_propeller_in.ogg')
        crash = base.loader.loadSfx('phase_5/audio/sfx/TL_train_cog.ogg')
        land = base.loader.loadSfx('phase_5/audio/sfx/Toon_bodyfall_synergy.ogg')

        cogSuit = self.toon.suit
        suit = base.localAvatar

        cogLeave = Sequence(ActorInterval(cogSuit, 'sit-lose'), Wait(.1), Func(suit.setZ, 2.75),
                            ActorInterval(cogSuit, 'landing', startTime = 2.5, endTime = 0), Wait(1.5),
                            ActorInterval(cogSuit, 'landing'), Func(cogSuit.loop, 'neutral'))
        cogMovement = Sequence(Wait(3), Parallel(Sequence(suit.posInterval(.5, (0, 15, 5)),
                                                          suit.posInterval(.5, (0, 10, 6)),
                                                          suit.posInterval(.5, (0, 5, 5)),
                                                          suit.posInterval(1.5, (0, 0, 0))),
                                                 suit.hprInterval(1, (180, 0, 0))))
        spinTrack = Sequence(ActorInterval(propeller, 'spin', startTime = 0, endTime = .25))
        propellerTrack = Sequence(Wait(1), Func(propeller.reparentTo, suit.find('**/joint_head')),
                                  ActorInterval(propeller, 'spin', startTime = 4, endTime = 2),
                                  Func(spinTrack.loop),
                                  Wait(2.25), Func(spinTrack.finish), ActorInterval(propeller, 'spin'),
                                  Func(propeller.delete))
        soundTrack = Sequence(Wait(1), Parallel(SoundInterval(startFly, duration = 3),
                                                Sequence(Wait(2.5), SoundInterval(endFly))))
        return Parallel(cogLeave, cogMovement, propellerTrack, soundTrack)
