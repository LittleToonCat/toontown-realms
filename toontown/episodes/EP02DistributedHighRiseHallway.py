from direct.interval.IntervalGlobal import *

from toontown.episodes import DistributedEpisodeZone
from toontown.episodes import EpisodeConfig


class EP02DistributedHighRiseHallway(DistributedEpisodeZone.DistributedEpisodeZone):

    def __init__(self, cr):
        DistributedEpisodeZone.DistributedEpisodeZone.__init__(self, cr)
        self.episodeZoneId = EpisodeConfig.EP02_HIGH_RISE_HALLWAY

    def disable(self):
        self.gearsSfx.stop()
        del self.gearsSfx

        DistributedEpisodeZone.DistributedEpisodeZone.disable(self)

    def generateGeom(self):
        self.geom = loader.loadModel('phase_14/models/modules/office-hallway')
        self.geom.reparentTo(render)
        self.geom.find('**/hallway_floor').setBin('ground', -10)

        gearsNode = self.geom.find('**/vents')
        self.gearsSfx = loader.loadSfx('phase_9/audio/sfx/CHQ_FACT_gears_turning.ogg')
        base.playSfx(self.gearsSfx, looping=1, volume=1, node=gearsNode)

        doors = loader.loadModel('phase_14/models/props/bathroom-doors')
        doors.reparentTo(self.geom.find('**/door_node'))

        leftDoor = doors.find('**/L_door')
        rightDoor = doors.find('**/R_door')
        leftDoor.setY(4.10)
        rightDoor.setY(-4.10)

        self.acceptOnce('enterdoor_collision', self.handleDoorOpen, extraArgs=[leftDoor, rightDoor])

    def handleDoorOpen(self, leftDoor, rightDoor, collEntry):
        self.toon.b_setAnimState('neutral')
        self.toon.wrtReparentTo(self.geom.find('**/door_node'))

        doorSfx = base.loader.loadSfx('phase_9/audio/sfx/CHQ_door_open.ogg')

        # Sometimes the play rate is -1 so let's make it look good
        self.toon.suit.setPlayRate(1, 'walk')

        seq = Parallel(Sequence(Func(base.camera.wrtReparentTo, render), Func(self.toon.disableAvatarControls),
                                Func(self.toon.deactivateCamera), Func(self.toon.collisionsOff),
                                Parallel(Sequence(Func(self.toon.suit.loop, 'walk'),
                                                  self.toon.posHprInterval(0.5, (-7.0, 0.0, 0.0), (-90.0, 0.0, 0.0)),
                                                  Func(self.toon.suit.loop, 'neutral')),
                                         base.camera.posHprInterval(1.7, (-5.0, -20.0, 6.0), (-120.0, -7.0, 0.0),
                                                                    blendType='easeInOut')),
                                Parallel(Sequence(Func(self.toon.suit.loop, 'walk'),
                                                  self.toon.posInterval(2.0, (7.0, 0.0, 0.0)),
                                                  Func(self.toon.wrtReparentTo, render)),
                                         Sequence(Wait(3.5), Func(base.transitions.fadeOut), Wait(1),
                                                  Func(self.toon.attachCamera), Func(self.toon.initializeSmartCamera),
                                                  Func(self.toon.activateCamera), Func(self.toon.show),
                                                  Func(self.teleportToZone, self.zoneConnections[1])))),
                       Sequence(Wait(1.7), Func(base.playSfx, doorSfx, volume=1),
                                Parallel(Sequence(LerpHprInterval(leftDoor, 1, (80, 0, 0), (0, 0, 0),
                                                                  blendType='easeInOut'),
                                                  LerpHprInterval(leftDoor, 1.5, (-60, 0, 0), blendType='easeInOut'),
                                                  LerpHprInterval(leftDoor, 1.5, (30, 0, 0), blendType='easeInOut'),
                                                  LerpHprInterval(leftDoor, 1.5, (0, 0, 0), blendType='easeInOut')),
                                         Sequence(LerpHprInterval(rightDoor, 1, (-80, 0, 0), (0, 0, 0),
                                                                  blendType='easeInOut'),
                                                  LerpHprInterval(rightDoor, 1.5, (60, 0, 0), blendType='easeInOut'),
                                                  LerpHprInterval(rightDoor, 1.5, (-30, 0, 0), blendType='easeInOut'),
                                                  LerpHprInterval(rightDoor, 1.5, (0, 0, 0), blendType='easeInOut')))))
        seq.start()

    def generateMovie(self):
        episodeStatus = base.cr.episodeManager.getEpisodeStatus(self.episodeZoneId)
        if episodeStatus == 0:
            self.movie = Sequence(Func(self.toon.setPosHpr, 0, 42, 0, -180, 0, 0))
        elif episodeStatus == 1:
            self.movie = Sequence(Func(self.toon.setPosHpr, -0.19, -28.9, 0, 90, 0, 0))
        elif episodeStatus == 2:
            self.movie = Sequence(Func(self.toon.setPosHpr, 0, -32.25, 0, 0, 0, 0))
