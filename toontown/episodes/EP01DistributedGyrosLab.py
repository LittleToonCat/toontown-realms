from panda3d.core import *
from panda3d.toontown import DNADoor

from direct.actor import Actor
from direct.gui.DirectGui import *
from direct.interval.IntervalGlobal import *

from panda3d.toontown import CFSpeech, CFTimeout, CFExclaim

from toontown.episodes import EpisodeLocalizer
from toontown.avatar import ToontownAvatarUtils
from toontown.building import ToonInteriorColors
from toontown.toonbase import ToontownGlobals, ClientSettings

from toontown.episodes import DistributedEpisodeZone
from toontown.episodes import EpisodeConfig
from toontown.effects.CarSmoke import CarSmoke
from toontown.suit.Chairman import Chairman, unloadDialog
from toontown.suit.GoonDeath import createGoonExplosion

import random


AssemblyLineSpeeds = (
    2.0,
    0.7,
    0.25
)


class EP01DistributedGyrosLab(DistributedEpisodeZone.DistributedEpisodeZone):

    def __init__(self, cr):
        DistributedEpisodeZone.DistributedEpisodeZone.__init__(self, cr)
        self.episodeZoneId = EpisodeConfig.EP01_GYROS_LAB

        self.__advanceMovieWarned = False
        self.cogs = []
        self.track = None
        self.moveSfx = None

    def disable(self):
        DistributedEpisodeZone.DistributedEpisodeZone.disable(self)

        del self.randomGenerator

        if self.track:
            self.track.finish()
            self.track = None

        for cog in self.cogs:
            cog.disableBattleDetect()
            cog.removeActive()
            cog.delete()

        if self.chairman:
            self.chairman.removeActive()
            self.chairman.delete()
            unloadDialog()
            del self.chairman

        if self.note:
            self.note.delete()
            del self.note

        self.title.destroy()
        del self.title

        self.moveSfx = None

    def generateGeom(self):
        # copied from toontown.building.DistributedGyrosLabInterior, modified slightly for episodes
        interior = loader.loadModel('phase_14/models/modules/gyros_lab_interior')
        self.geom = interior.copyTo(render)
        self.geom.find('**/entrance/**/Floor').setBin('ground', -10)
        self.geom.find('**/GyroGearhead_int_egg/**/Floor').setBin('ground', -10)
        self.geom.find('**/bulb_g').hide()
        self.geom.find('**/control_stand').setScale(1.25)
        self.geom.find('**/door').setH(-60)

        sky = loader.loadModel('phase_8/models/props/DL_sky')
        sky.setPos(0, 0, -50)
        sky.reparentTo(self.geom)

        self.randomGenerator = random.Random()
        self.randomGenerator.seed(ToontownGlobals.GyrosLab)
        hoodId = ToontownGlobals.DaisyGardensBeta
        self.colors = ToonInteriorColors.colors[hoodId]
        door = self.dnaStore.findNode('door_double_round_ur')
        doorOrigin = self.geom.attachNewNode('door_origin')
        doorOrigin.setPosHpr(-49, -12, 0.02, 90, 0, 0)
        doorOriginNPName = doorOrigin.getName()
        doorOriginIndexStr = doorOriginNPName[len('door_origin_'):]
        newNode = ModelNode('door_' + doorOriginIndexStr)
        newNodePath = NodePath(newNode)
        newNodePath.reparentTo(self.geom)
        doorNP = door.copyTo(newNodePath)
        doorOrigin.setScale(0.8, 0.8, 0.8)
        doorOrigin.setPos(doorOrigin, 0, -0.025, 0)
        color = self.randomGenerator.choice(self.colors['TI_door'])
        # triggerId = "{block}_{idx}".format(block=self.block, idx=doorOriginIndexStr)
        DNADoor.setupDoor(doorNP, newNodePath, doorOrigin, self.dnaStore, str(self.block), color)
        doorFrame = doorNP.find('door_*_flat')
        doorFrame.setColor(color)

        if not self.movieOnDoorIn:
            startNode = CollisionNode('startNode')
            startNode.addSolid(CollisionBox(Point3(-37.87, -13.28, 0), 0.5, 30, 10))
            self.geom.attachNewNode(startNode)
            self.acceptOnce('enterstartNode', self.startMovie)

        # Apply a hardware animation shader for performance
        attr = ShaderAttrib.make(Shader.load(Shader.SLGLSL,
                                             fragment = 'phase_3/shaders/ttoff_sha_av_hw.frag',
                                             vertex = 'phase_3/shaders/ttoff_sha_av_hw.vert'))
        attr = attr.setFlag(ShaderAttrib.F_hardware_skinning, True)

        for idx, cogInfo in enumerate(ToontownGlobals.PrologueCogInfo):
            cogType = cogInfo[0]
            cogLevel = cogInfo[1]
            cog = ToontownAvatarUtils.createCog(cogType, 178.00, 12.60, 3.55, 180.00, 0.00, 0.00, level=cogLevel,
                                                do=self)
            cog.addActive()
            cog.hideName()
            cog.stash()
            cog.setAttrib(attr)
            self.cogs.append(cog)

        self.chairman = Chairman()
        self.chairman.reparentTo(self.geom)
        self.chairman.setPosHpr(175.5, -24.5, 0.1, 90.0, 0.0, 0.0)
        self.chairman.pose('neutral', 0)
        self.chairman.find('**/left_eye').setColorScale(1, 1, 1, 0)
        self.chairman.find('**/right_eye').setColorScale(1, 1, 1, 0)
        self.chairman.getChild(0).setScale(1.3)
        self.chairman.addActive()
        self.chairman.setAttrib(attr)

        self.note = Actor.Actor('phase_14/models/char/gyros-note-mod',
                                {'fall': 'phase_14/models/char/gyros-note-chan'})
        self.note.reparentTo(self.geom)
        self.note.setBlend(frameBlend=ClientSettings.SmoothAnimations.get())
        self.note.setPosHpr(175.25, -24.57, 0.0, -90.0, 0.0, 0.0)
        self.note.setAttrib(attr)

        self.title = DirectLabel(relief=None, text='', pos=(0, 0, 0), scale=0.15,
                                 text_font=ToontownGlobals.getEpisodeFont(), text_fg=(1, 1, 1, 1),
                                 text_shadow=(0.1, 0.1, 0.1, 1), sortOrder=DGG.NO_FADE_SORT_INDEX)

    def generateMovie(self):
        base.cr.episodeManager.setEpisodeStatus(EpisodeConfig.EP01_OAK_STREET, 1)

        sceneMusic = loader.loadMusic('phase_14/audio/bgm/LAB_activate.ogg')

        walkSfx = loader.loadSfx('phase_3.5/audio/sfx/AV_footstep_walkloop.ogg')
        runSfx = loader.loadSfx('phase_3.5/audio/sfx/AV_footstep_runloop_new.ogg')
        stompSfx = loader.loadSfx('phase_9/audio/sfx/CHQ_FACT_stomper_med.ogg')
        stompSfx.setPlayRate(2.05)
        shockSfx = loader.loadSfx('phase_5/audio/sfx/AA_sound_aoogah.ogg')
        shockSfx.setVolume(.420)
        laughSfx = loader.loadSfx('phase_4/audio/sfx/avatar_emotion_laugh.ogg')
        cashSfx = loader.loadSfx('phase_14/audio/sfx/cash.ogg')
        wireMessUpSfx = loader.loadSfx('phase_5/audio/sfx/TL_train_cog.ogg')
        signHitSfx = loader.loadSfx('phase_5/audio/sfx/SA_hardball_impact_only.ogg')
        signHitSfx.setPlayRate(1.15)
        maxSfx = loader.loadSfx('phase_9/audio/sfx/CHQ_GOON_tractor_beam_alarmed.ogg')
        controlStand = self.geom.find('**/control_stand')
        # We're doing this so the smoke effect won't hide when the control stand
        # is hidden
        smokeEffect = CarSmoke(render)
        smokeEffect.effectNode.setPos(controlStand.getPos())

        smokeParticle = smokeEffect.effect.getParticlesNamed('particles-1')

        def setParticleLifespan(val):
            smokeParticle.factory.setLifespanBase(val)
            smokeParticle.factory.setLifespanSpread(val)

        sadSfx = loader.loadSfx('phase_5/audio/sfx/ENC_Lose.ogg')

        self.moveSfx = loader.loadSfx('phase_9/audio/sfx/CHQ_FACT_elevator_up_down.ogg')

        dialogue = EpisodeLocalizer.PrologueLabDialogue

        lightTrackGreen = Sequence(Func(self.geom.find('**/bulb_g').setColorScale, 0, 1, 0, 1), Wait(0.3),
                                   Func(self.geom.find('**/bulb_g').setColorScale, 0, 0.5, 0, 1), Wait(0.3))
        lightTrackRed = Sequence(Func(self.geom.find('**/bulb_r').setColorScale, 1, 0, 0, 1), Wait(0.15),
                                 Func(self.geom.find('**/bulb_r').setColorScale, 0.5, 0, 0, 1), Wait(0.15))
        quickCogTrack = Sequence()
        cogNum = 15
        for n in range(24):
            quickCogTrack.append(Sequence(Func(self.moveCog, self.cogs[cogNum], 11, 2), Wait(0.25)))
            cogNum += 1

        self.track = Sequence(#Func(self.toon.stopLookAround), Func(base.camLens.setMinFov, 40 / (4.0 / 3.0)),
                              #Func(self.toon.setScale, 1.3), Func(self.toon.collisionsOff), Func(self.toon.setZ, 0.0049),
                              #Func(self.lockToon), Func(base.camera.setPosHpr, -14.18, -2.485, 3.0964, 103.0, -2.2, 0.0),
                              #Parallel(Sequence(Func(self.toon.loop, 'walk'), Func(base.playSfx, walkSfx, looping=1),
                              #                  self.toon.posHprInterval(10.0, (27.999, -12.5, 0.0049),
                              #                                           (-90.0, 0.0, 0.0)),
                              #                  Func(self.toon.loop, 'neutral'), Func(walkSfx.stop)),
                              #         Sequence(LerpPosHprInterval(base.camera, 6.0, (30.916, -2.677, 2.9784),
                              #                                     (97.9, -3.7, 0.0), blendType='easeInOut'),
                              #                  Func(base.camera.setPosHpr, 11.799, 9.3096, 5.7685, 162.0, -3.1, 0.0),
                              #                  LerpPosHprInterval(base.camera, 5.0, (11.728, 5.8065, 5.7065),
                              #                                     (220.0, -5.8, 0.0), blendType='easeInOut'),
                              #                  Func(base.camera.setPosHpr, 16.287, -17.74, 4.5701, 290.0, -2.5, 0.0),
                              #                  Func(base.camera.setPosHpr, 24.110, -19.46, 1.4756, 312.0, 1.24, 0.0),
                              #                  LerpPosHprInterval(base.camera, 4.0, (17.320, -24.95, 1.0933),
                              #                                     (311.0, 7.24, 0.0), blendType='easeInOut'),
                              #                  Func(base.camera.setPosHpr, 65.452, 23.934, 5.4702, 501.0, -2.3, 1.5),
                              #                  LerpPosHprInterval(base.camera, 3.0, (41.255, 8.3955, 1.7335),
                              #                                     (526.0, 5.12, -9.1)),
                              #                  Func(base.camera.setPosHpr, 47.289, -9.755, 1.1757, 818.0, 7.51, -1.5),
                              #                  Parallel(Sequence(Func(self.toon.loop, 'walk'),
                              #                                    Func(base.playSfx, walkSfx, looping=1),
                              #                                    self.toon.posHprInterval(2.0,
                              #                                                             (36.916, -10.98, 0.0049),
                              #                                                             (-81.0, 0.0, 0.0)),
                              #                                    Func(self.toon.loop, 'neutral'), Func(walkSfx.stop),
                              #                                    self.getChatSequence(self.toon, dialogue[0],
                              #                                                         wait=3.0)),
                              #                           LerpPosHprInterval(base.camera, 3.0, (50.044, -14.31, 1.2822),
                              #                                              (787.0, 8.0, -1.5), blendType='easeInOut'),
                              #                           self.toon.find('**/__Actor_head').hprInterval(3.0, (30, 5, 0))))),
                              #Func(base.camera.setPosHpr, 43.061, -25.55, 2.3485, 728.0, 1.64, -1.5),
                              #Func(self.toon.loop, 'walk'),
                              #Parallel(self.toon.find('**/__Actor_head').hprInterval(2.0, (-45, 0, 0)),
                              #         LerpPosHprInterval(base.camera, 5.0, (33.798, -27.21, 0.7388),
                              #                            (663.0, 5.68, -1.5), blendType='easeInOut'),
                              #         Sequence(Func(base.playSfx, walkSfx, looping=1),
                              #                  self.toon.posHprInterval(6.5, (69.539, -15.0, 0.0049),
                              #                                           (-100.0, 0.0, 0.0)),
                              #                  Func(walkSfx.stop)),
                              #         Sequence(Wait(2.0), self.getChatSequence(self.toon, dialogue[1], preClear=True),
                              #                  self.toon.find('**/__Actor_head').hprInterval(2.0, (45, 0, 0)),
                              #                  self.getChatSequence(self.toon, wait=1.0, postClear=True)
                              #                  )),
                              #Func(base.camera.setPosHpr, 116.30, -11.26, 3.1910, 655.0, 8.44, -1.5),
                              #Parallel(Sequence(Func(base.playSfx, walkSfx, looping=1),
                              #                  self.toon.posHprInterval(7.75, (148.22, -23.05, 0.0049),
                              #                                           (-92.0, 0.0, 0.0)),
                              #                  Func(walkSfx.stop)),
                              #         LerpPosHprInterval(base.camera, 7.0, (173.91, -33.42, 1.0765),
                              #                            (772.0, 4.20, 0.0), blendType='easeInOut')),
                              #Parallel(LerpPosHprInterval(base.camera, 4.0, (173.43, -34.17, 1.1712),
                              #                            (719.0, -0.3, 0.0), blendType='easeInOut'),
                              #         Sequence(Func(base.playSfx, walkSfx, looping=1),
                              #                  self.toon.posHprInterval(4.0, (169, -23.82, 0.0049),
                              #                                           (-92.0, 0.0, 0.0)),
                              #                  Func(walkSfx.stop))),
                              #Wait(0.1), Func(self.toon.loop, 'neutral'),
                              #Parallel(LerpPosHprInterval(base.camera, 1.5, (173.25, -43.91, 3.0478),
                              #                            (719.0, 1.54, 0.0), blendType='easeOut'),
                              #         self.toon.find('**/__Actor_head').hprInterval(1.0, (0, 30, 0))),
                              #Func(base.playMusic, sceneMusic),
                              #Func(base.camera.setPosHpr, 177.71, -30.00, 4.6150, 765.0, -9.2, 0.0),
                              #Parallel(Sequence(ActorInterval(self.toon, 'conked'), Func(self.toon.loop, 'neutral')),
                              #         Sequence(Func(self.toon.surpriseEyes),
                              #                  Func(shockSfx.play), Wait(1.5),
                              #                  Func(self.toon.openEyes), Func(self.toon.startBlink))),
                              #Func(base.camera.setPosHpr, 163.41, -34.09, -4.481, 677.0, 45.2, -22.0),
                              #self.getChatSequence(self.toon, dialogue[2], preClear=True),
                              #self.toon.find('**/__Actor_head').hprInterval(1.5, (0, 40, 0)), Wait(3.0),
                              #Func(base.camera.setPosHpr, 177.49, -33.20, 2.8221, 754.0, 9.65, -1.0),
                              #Parallel(LerpPosHprInterval(base.camera, 3.0, (176.13, -40.72, 2.6019),
                              #                            (733.0, 4.03, -1.0), blendType='easeInOut'),
                              #         Sequence(ActorInterval(self.toon, 'think', playRate=0.8),
                              #                  Func(self.toon.loop, 'neutral')),
                              #         self.toon.find('**/__Actor_head').hprInterval(1.5, (0, 5, 0)),
                              #         Sequence(self.getChatSequence(self.toon, dialogue[3], wait=2.5,
                              #                                       preClear=True, postClear=True),
                              #                  self.getChatSequence(self.toon, dialogue[4], wait=3.0, postClear=True))
                              #         ),
                              #Func(base.camera.setPosHpr, 177.21, -35.14, 0.4713, 751.0, 11.5, -1.0),
                              #self.toon.find('**/__Actor_head').hprInterval(0, (0, 5, 0)),
                              #self.getChatSequence(self.toon, dialogue[5], wait=5.0, postClear=True),
                              #Func(self.toon.cashEyes),
                              #Func(base.camera.setPosHpr, 177.97, -16.06, 15.817, 849.0, -47.0, -1.0), Wait(0.2),
                              #Func(base.playSfx, cashSfx), self.getChatSequence(self.toon, dialogue[6]),
                              #ActorInterval(self.toon, 'good-putt', playRate=0.9), Func(self.toon.loop, 'neutral'),
                              #Wait(0.25), Func(base.camera.setPosHpr, 163.41, -34.09, -4.481, 677.0, 45.2, -22.0),
                              #Func(self.toon.openEyes), Func(self.toon.startBlink),
                              #Func(self.toon.blinkEyes), self.toon.find('**/__Actor_head').hprInterval(0, (0, 30, 0)),
                              #self.getChatSequence(self.toon, dialogue[7], wait=3.0, preClear=True, postClear=True),
                              #self.getChatSequence(self.toon, dialogue[8], wait=3.0, postClear=True),
                              #Func(self.toon.blinkEyes), Func(self.toon.setPlayRate, 10, 'neutral'),
                              #Func(laughSfx.play),
                              #self.getChatSequence(self.toon, dialogue[9], wait=2.0, postClear=True),
                              #Func(self.toon.blinkEyes), Func(self.toon.setPlayRate, 10, 'neutral'),
                              #Func(self.toon.setPlayRate, 1, 'neutral'),
                              #Wait(1.0), Parallel(self.toon.find('**/__Actor_head').hprInterval(1.5, (0, 0, 0)),
                              #                    LerpPosHprInterval(base.camera, 3.0, (158.87, -42.97, 5.2917),
                              #                                       (682.0, -3.6, 0.5))),
                              #Parallel(LerpPosHprInterval(base.camera, 5.5, (148.32, -8.628, 7.7651),
                              #                            (597.0, -8.1, 0.5)),
                              #         Sequence(self.getChatSequence(self.toon, dialogue[10], wait=4.0, postClear=True),
                              #                  self.getChatSequence(self.toon, dialogue[11]),
                              #                  Func(self.toon.loop, 'walk'),
                              #                  self.toon.posHprInterval(2.0, (171.99, -21.68, 0.0049),
                              #                                           (-90.0, 0.0, 0.0)),
                              #                  Func(wireMessUpSfx.play), self.getChatSequence(self.toon),
                              #                  ActorInterval(self.toon, 'slip-forward'),
                              #                  Func(self.toon.loop, 'neutral'))),
                              #Func(base.camera.setPosHpr, 141.88, -24.24, 11.491, 627.0, 1.35, 0.5),
                              #Func(self.note.wrtReparentTo, self.chairman.find('**/joint_attachMeter')),
                              #Func(self.chairmanWakeup), Wait(3.0),
                              #Func(base.camera.setPosHpr, 154.00, -32.77, 5.6959, 649.0, 25.3, 0.5),
                              #self.getChatSequence(self.chairman, dialogue[12], chatFlags=CFExclaim | CFTimeout,
                              #                     chatType=EpisodeConfig.CHATABSOLUTE, wait=3.0),
                              #Parallel(Func(self.note.wrtReparentTo, self.geom),
                              #                    self.getChatSequence(self.chairman),
                              #                    Func(self.note.setPlayRate, 1.5, 'fall'),
                              #                    ActorInterval(self.note, 'fall'), Func(self.note.setZ, 0.5),
                              #                    Func(base.camera.setPosHpr, 138.13, -45.56, 17.617, 661.0, -19.0,
                              #                         0.5),
                              #                    Func(self.toon.setPosHpr, 170.13, -31.16, 0.0049, -34.0, 0.0, 0.0),
                              #                    Sequence(Wait(2.5), Func(signHitSfx.play),
                              #                             Parallel(ActorInterval(self.toon, 'slip-backward', playRate=0.95),
                              #                                      Sequence(Wait(3.0),
                              #                                               Func(base.camera.setPosHpr, 157.37, -37.67, 1.6761, 663., 4.15, 0.5),
                              #                                               Parallel(Func(self.chairman.loop, 'walk'),
                              #                                                        Sequence(Func(self.toon.loop, 'walk'),
                              #                                                                 self.toon.posHprInterval(2.0, (170.13, -31.15, 0.0049),
                              #                                                                                          (85, 0.0, 0.0)),
                              #                                                                 Func(self.toon.loop, 'neutral')),
                              #                                                        Sequence(Func(base.playSfx, stompSfx, looping=1, volume=0.3),
                              #                                                                 self.chairman.posHprInterval(14, (47.25, -6.0, 0.1000),
                              #                                                                                              (90.0, 0.0, 0.0)),
                              #                                                                 Func(stompSfx.stop),
                              #                                                                 ActorInterval(self.chairman, 'into-type'),
                              #                                                                 Func(self.chairman.loop, 'type')),
                              #                                                        Sequence(LerpPosHprInterval(base.camera, 3.25,
                              #                                                                                    (157.37, -37.67, 1.6761),
                              #                                                                                    (730, -0.3, 0.5),
                              #                                                                                    blendType='easeInOut'),
                              #                                                                 Wait(0.5),
                              #                                                                 Func(base.camera.setPosHpr, 152.08, -29.38, 1.6785, 622.0, 5.60, 0.5),
                              #                                                                 Func(self.toon.sadEyes),
                              #                                                                 Func(self.toon.blinkEyes),
                              #                                                                 self.getChatSequence(self.toon, dialogue[13], preClear=True),
                              #                                                                 Wait(3.5),
                              #                                                                 self.getChatSequence(self.toon),
                              #                                                                 Func(base.camera.setPosHpr, 47.022, -24.35, 3.2820, 635.0, -0.4, 0.5),
                              #                                                                 LerpPosHprInterval(base.camera, 7.0,
                              #                                                                                    (44.759, -25.84, 3.3121),
                              #                                                                                    (717., -0.4, 0.5),
                              #                                                                                    blendType='easeInOut'),
                              #                                                                 Func(self.geom.find('**/entrance_walls').hide),
                              #                                                                 Wait(2.0),
                              #                                                                 Func(base.camera.setPosHpr, 23.014, -2.485, 3.2709, 617.0, 12.2, 0.5),
                              #                                                                 Wait(2.5))))))),
                              #Func(base.camera.setPosHpr, 146.61, -48.53, 14.749, 708.0, -3.2, 0.5),
                              #Parallel(LerpPosHprInterval(base.camera, 6.0, (156.15, -32.35, 14.201),
                              #                            (717.0, -4.3, -0.2), blendType='easeInOut'),
                              #         Sequence(Func(self.moveConveyor), Func(self.geom.find('**/bulb_g').show),
                              #                  Func(self.geom.find('**/bulb_r').hide),
                              #                  Func(self.moveCog, self.cogs[0], 11), Wait(3),
                              #                  Func(self.moveCog, self.cogs[1], 10), Wait(3),
                              #                  Func(self.moveCog, self.cogs[2], 9), Wait(3),
                              #                  Func(self.moveCog, self.cogs[3], 8), Wait(3),
                              #                  Func(base.camera.setPosHpr, 26.682, 4.9415, 6.4833, 596.0, -3.0, -0.1),
                              #                  Parallel(LerpPosHprInterval(base.camera, 3.0, (33.574, 0.2927, 7.8111),
                              #                                              (596., -10.0, -0.1), blendType='easeInOut'),
                              #                           Sequence(Wait(3.0), lightTrackGreen, lightTrackGreen,
                              #                                    lightTrackGreen, lightTrackGreen, lightTrackGreen,
                              #                                    lightTrackGreen, lightTrackGreen),
                              #                           Sequence(Func(self.cogs[1].stash), Func(self.cogs[2].stash),
                              #                                    Func(self.cogs[3].stash),
                              #                                    Func(self.moveConveyor, speed=1),
                              #                                    Func(self.moveCog, self.cogs[4], 11, 1), Wait(0.7),
                              #                                    Func(self.moveCog, self.cogs[5], 10, 1), Wait(0.7),
                              #                                    Func(self.moveCog, self.cogs[6], 9, 1), Wait(0.7),
                              #                                    Func(self.moveCog, self.cogs[7], 8, 1), Wait(0.7),
                              #                                    Func(self.moveCog, self.cogs[8], 8, 1), Wait(0.7),
                              #                                    Func(self.moveCog, self.cogs[9], 8, 1), Wait(0.7),
                              #                                    Func(self.moveCog, self.cogs[10], 8, 1), Wait(0.7),
                              #                                    Func(base.camera.setPosHpr, 155.52, -39.56, 13.655, 717.0, -6.6, -13),
                              #                                    Func(self.moveCog, self.cogs[11], 8, 1), Wait(0.7),
                              #                                    Func(self.moveCog, self.cogs[12], 8, 1), Wait(0.7),
                              #                                    Func(self.moveCog, self.cogs[13], 8, 1), Wait(0.7),
                              #                                    Func(self.moveCog, self.cogs[14], 8, 1), Wait(0.7))))),
                              #Func(base.camera.setPosHpr, 159.41, 7.1237, 16.364, 652.0, 13.6, -7.0), lightTrackGreen,
                              #lightTrackGreen, lightTrackGreen, lightTrackGreen, lightTrackGreen,
                              #Func(self.geom.find('**/bulb_g').setColorScale, 0, 1, 0, 1), Wait(0.3),
                              #Func(base.camera.setPosHpr, 34.093, 18.422, 4.0903, 561.0, 3.89, -7.0),
                              #Func(self.chairman.setPlayRate, 1.5, 'type'), Wait(2.0),
                              #Func(base.camera.setPosHpr, 162.0, -26.64, 1.0642, 594.0, 14.2, -20.0),
                              #Parallel(Sequence(ActorInterval(self.toon, 'cringe', endTime=1.3),
                              #                  Func(self.toon.loop, 'neutral')),
                              #         Sequence(Parallel(quickCogTrack, Sequence(Wait(1.3), Func(base.playSfx, maxSfx),
                              #                                                   Func(base.camera.setPosHpr, 141.60, -11.71, -1.990, 674.0, 21.7, 8.5),
                              #                                                   Func(self.geom.find('**/bulb_g').hide),
                              #                                                   Func(self.geom.find('**/bulb_r').show),
                              #                                                   lightTrackRed, lightTrackRed,
                              #                                                   lightTrackRed, lightTrackRed,
                              #                                                   lightTrackRed, lightTrackRed,
                              #                                                   lightTrackRed, lightTrackRed,
                              #                                                   Func(base.playSfx, maxSfx),
                              #                                                   lightTrackRed, lightTrackRed,
                              #                                                   lightTrackRed, lightTrackRed,
                              #                                                   lightTrackRed, lightTrackRed,
                              #                                                   lightTrackRed, lightTrackRed)))),
                              #Func(LerpFunctionInterval(self.moveSfx.setVolume, fromData=0.5,
                              #                          toData=0.0, duration=2.0).start), Func(self.moveSfx.stop),
                              #Func(base.camera.setPosHpr, 43.721, 25.693, 22.024, 898.0, -18.0, 8.5),
                              #Parallel(LerpColorScaleInterval(controlStand, 0.3, (0.15, 0.15, 0.15, 1)),
                              #         Func(smokeEffect.start)),
                              #ActorInterval(self.chairman, 'into-type', playRate=-1.15),
                              #Func(self.chairman.loop, 'neutral'),
                              #Wait(2),
                              #Parallel(createGoonExplosion(render, controlStand.getPos(), 1.15),
                              #         Sequence(Wait(0.6), Func(controlStand.hide),
                              #                  Func(setParticleLifespan, 0))),
                              #Func(smokeEffect.destroy),
                              #Parallel(LerpPosHprInterval(base.camera, 4.0, (38.340, 23.763, 22.492),
                              #                            (919.0, -15.0, -0.5), blendType='easeInOut'),
                              #         Sequence(Func(self.chairman.loop, 'walk'),
                              #                  Func(base.playSfx, stompSfx, looping=1, volume=0.3),
                              #                  self.chairman.posHprInterval(2.0, (47.25, -6.0, 0.1000),
                              #                                               (-84.0, 0.0, 0.0)),
                              #                  self.chairman.posHprInterval(2.0, (62.199, -7.635, 0.1000),
                              #                                               (-88.0, 0.0, 0.0)),
                              #                  Func(stompSfx.stop))),
                              #Func(self.setUpCogsPos), Func(self.cogs[2].unstash),
                              #Func(base.camera.setPosHpr, 94.226, -39.27, 11.539, 1121, -0.0, -0.5),
                              #Parallel(LerpPosHprInterval(base.camera, 5.0, (159.09, -54.35, 19.262),
                              #                            (1128, -6.0, -0.5), blendType='easeInOut'),
                              #         Sequence(Func(base.playSfx, stompSfx, looping=1, volume=0.3),
                              #                  self.chairman.posHprInterval(3.25, (86.773, -13.88, 0.1000),
                              #                                               (-113, 0.0, 0.0)),
                              #                  self.chairman.posHprInterval(2.0, (86.773, -13.88, 0.1000),
                              #                                               (-1.0, 0.0, 0.0)))),
                              #Wait(1.0), Func(stompSfx.stop), Func(self.chairman.loop, 'neutral'),
                              #Func(base.camera.setPosHpr, 97.698, 2.2782, 15.029, 1220, 9.05, -0.5),
                              #self.getChatSequence(self.chairman, dialogue[14], chatFlags=CFExclaim | CFTimeout,
                              #                     chatType=EpisodeConfig.CHATABSOLUTE, wait=2.5, postClear=True),
                              #Func(base.camera.setPosHpr, 136.69, -33.24, 7.0890, 1127, 1.24, -0.5),
                              #Func(self.flyOutCogs), Wait(6.0),
                              #Func(base.camera.setPosHpr, 71.977, 4.0326, 8.3297, 1133, 2.19, -0.5),
                              #self.cogs[0].find('**/yesman').hprInterval(1, (45, 0, 0)), Wait(0.75),
                              #Func(base.camera.setPosHpr, 56.031, 19.483, 7.8635, 1286, 3.33, -0.5),
                              #Func(self.chairman.headsUp, self.cogs[0]), Wait(1.5),
                              #Func(base.camera.setPosHpr, 79.866, 12.831, 19.093, 923.0, -10.0, -0.5),
                              #Func(self.toon.setPosHpr, 127.41, -37.45, 0.0049, 85.0, 0.0, 0.0),
                              #Func(self.toon.loop, 'run'), Parallel(LerpPosHprInterval(base.camera, 4.5,
                              #                                                         (88.102, 12.090, 6.0741),
                              #                                                         (884.0, -5.3, -0.5),
                              #                                                         blendType='easeInOut'),
                              #                                      Sequence(Func(base.playSfx, runSfx, looping=1,
                              #                                                    volume=0.25),
                              #                                               self.toon.posHprInterval(5.0,
                              #                                                                        (63.362, -23.81, 0.0049),
                              #                                                                        (77.5, 0.0, 0.0)),
                              #                                               Func(runSfx.stop)),
                              #                                      Sequence(Wait(4.0),
                              #                                               Func(self.chairman.loop, 'walk'),
                              #                                               Func(base.playSfx, stompSfx, looping=1,
                              #                                                    volume=0.3),
                              #                                               self.chairman.posHprInterval(1.0,
                              #                                                                            (86.773, -13.88, 0.1000),
                              #                                                                            (98.4, 0.0, 0.0)))),
                              #Func(self.chairman.loop, 'neutral'),
                              #Func(base.camera.setPosHpr, 79.443, -18.20, 4.5169, 812.0, -5.3, -0.5),
                              #Func(self.cogs[0].setPosHpr, 36.718, -12.69, 6.0, -104, 0.0, 0.0),
                              #Func(self.geom.find('**/entrance_walls').show),
                              #Parallel(LerpPosHprInterval(base.camera, 4.0, (57.298, -4.872, 3.2793),
                              #                            (827.0, 0.03, 1.30), blendType='easeInOut'),
                              #         Sequence(self.toon.posHprInterval(4.5, (42.233, -14.00, 0.0049),
                              #                                           (77.5, 0.0, 0.0)),
                              #                  Func(self.toon.loop, 'neutral')), Func(self.yesmanBlock)), Wait(2.0),
                              #Func(self.cogs[0].loop, 'neutral'),
                              #Func(base.camera.setPosHpr, 51.523, -27.10, 2.1350, 761.0, 4.27, 1.29),
                              #self.getChatSequence(self.cogs[0], dialogue[15], chatFlags=CFSpeech | CFTimeout,
                              #                     wait=3.0, chatType=EpisodeConfig.CHATABSOLUTE, postClear=True),
                              #Func(self.cogs[0].hide),
                              #Func(base.camera.setPosHpr, 30.981, -14.67, 5.0901, 632.0, -4.8, 1.27),
                              #Parallel(self.toon.find('**/__Actor_head').hprInterval(0, (0, 10, 0)),
                              #         Sequence(self.getChatSequence(self.toon, dialogue[16], wait=3.5, preClear=True,
                              #                                       postClear=True),
                              #                  self.getChatSequence(self.toon, dialogue[17], wait=3.5,
                              #                                       postClear=True)),
                              #         Sequence(Wait(6.5), LerpFunctionInterval(stompSfx.setVolume, fromData=0.25,
                              #                                                  toData=0.0, duration=0.3),
                              #                  Func(stompSfx.stop)),
                              #         Sequence(Func(self.chairman.loop, 'walk'),
                              #                  self.chairman.posHprInterval(7.0, (53.609, -13.63, 0.1000),
                              #                                               (87.9, 0.0, 0.0)),
                              #                  ActorInterval(self.chairman, 'capture')),
                              #         Sequence(Wait(4), LerpPosHprInterval(base.camera, 4.0, (30.981, -14.67, -1.809),
                              #                                              (631.0, 34.1, 1.26), blendType='easeInOut'),
                              #                  Wait(1.0), Func(base.transitions.fadeOut, 1))),
                              #Func(base.camLens.setMinFov, ToontownGlobals.DefaultCameraFov / (4.0 / 3.0)),
                              #Func(self.toon.setScale, 1), Wait(1.5), Func(sadSfx.play), Wait(3.5),
                              #Func(self.speakText, self.title, EpisodeLocalizer.PrologueOutro, scale=0.75, zPos=0.85,
                              #     delay=0.08),
                              Wait(14.0), LerpColorScaleInterval(self.title, 4.0, (1, 1, 1, 0)), Wait(0.5),
                              Func(self.releaseToon), Func(self.endEpisode))
        if self.movieOnDoorIn:
            self.movie = self.track

    def startMovie(self, coll):
        if not self.movieOnDoorIn:
            self.track.start()

    def yesmanBlock(self):
        seq = Sequence(Func(self.cogs[0].setPos, 36.718, -12.69, 0.0023), Func(self.cogs[0].headsUp, self.toon),
                       Func(self.cogs[0].find('**/yesman').setHpr, 0, 0, 0),
                       self.cogs[0].beginSupaFlyMove(VBase3(36.718, -12.69, 0.0023), 1, 'flyIn'),
                       Func(self.cogs[0].loop, 'neutral'))
        seq.start()

    def flyOutCogs(self):
        flyTrack = Parallel()
        flyOutSfx = base.loader.loadSfx('phase_5/audio/sfx/ENC_propeller_out.ogg')
        flyOutSfx.setVolume(0.5)
        for cog in self.cogs:
            if cog != self.cogs[0]:
                flyTrack.append(
                    Sequence(cog.beginSupaFlyMove(VBase3(cog.getX(), cog.getY(), cog.getZ()), 0, 'flyOut')))
        flyTrack.append(Func(flyOutSfx.play))
        flyTrack.start()

    def setUpCogsPos(self):
        num = 0
        for cog in self.cogs:
            posInfo = ToontownGlobals.PrologueCogPosInfo[num]
            cog.setPosHpr(posInfo[0], posInfo[1], posInfo[2], posInfo[3], 0, 0)
            num += 1

    def moveCog(self, cog, moves, speed=0):
        cog.unstash()
        cogTrack = Sequence()
        x = 178
        if speed == 0:
            for m in range(moves):
                x -= 10.75
                cogTrack.append(cog.posInterval(2.0, (x, cog.getY(), cog.getZ())))
                cogTrack.append(Wait(1))
        elif speed == 1:
            for m in range(moves):
                x -= 15
                cogTrack.append(cog.posInterval(2.0, (x, cog.getY(), cog.getZ())))
        elif speed == 2:
            for m in range(moves):
                x -= 5
                cogTrack.append(cog.posInterval(.25, (x, cog.getY(), cog.getZ())))
        cogTrack.start()

    def moveConveyor(self, speed=0):
        moveTrack = Sequence()
        if speed == 0:
            for x in range(4):
                moveTrack.append(Func(self.conveyorMovement))
                moveTrack.append(Wait(3.0))
        elif speed == 1:
            self.conveyorMovement(1)
        moveTrack.start()

    def conveyorMovement(self, speed=0):
        lerper = NodePath('lerper')
        self.geom.find('**/shelf_5').setTexProjector(TextureStage.getDefault(), NodePath(), lerper)
        if speed == 0:
            seq = Sequence(Func(base.playSfx, self.moveSfx, volume=0.5), lerper.posInterval(2.0, VBase3(1, 0, 0)))
        elif speed == 1:
            seq = Sequence(Func(base.playSfx, self.moveSfx, looping=1, volume=0.5),
                           lerper.posInterval(8.0, VBase3(5.5, 0, 0)))
        seq.start()

    def chairmanWakeup(self):
        seq = Sequence()
        self.chairman.setPlayRate(0, 'neutral')
        self.chairman.loop('neutral')
        for x in range(0, 101):
            rate = x / 100.0
            seq.append(Func(self.chairman.setPlayRate, rate, 'neutral'))
            seq.append(Wait(.01))
        for x in range(0, 101):
            alpha = x / 100.0
            seq.append(Func(self.chairman.find('**/left_eye').setColorScale, 1, 1, 1, alpha))
            seq.append(Func(self.chairman.find('**/right_eye').setColorScale, 1, 1, 1, alpha))
            seq.append(Wait(.01))
        seq.start()

    def cleanupMovie(self):
        if hasattr(self, 'track') and self.track is not None:
            if self.track.isPlaying():
                self.track.pause()
                if self.clearToFinishInterval:
                    self.track.finish()
            self.track = None
        DistributedEpisodeZone.DistributedEpisodeZone.cleanupMovie(self)

    def advanceMovie(self, state):
        if not __debug__:
            self.notify.debug('Devs only.')
            return
        if not self.allowAdvanceMovie:
            if not self.__advanceMovieWarned:
                self.notify.warning('advanceMovie() is *very* buggy with Gyro\'s Lab movie!')
                self.notify.warning('If you\'re *really* sure you want to continue, add the following in dev.prc:')
                self.notify.warning('episode-prologue-gyroslab-allowAdvanceMovie #t')
                self.notify.warning('If you do, just note: I warned you. - Gustavo')
                self.__advanceMovieWarned = True
            return
        movie = None
        if self.movieOnDoorIn:
            if hasattr(self, 'movie') and self.movie is not None:
                movie = self.movie
        else:
            if hasattr(self, 'track') and self.track is not None:
                movie = self.track
        if movie is None:
            # don't attempt to set a play rate on a movie that doesn't exist!
            self.notify.debug('No movie to advance.')
            return
        if state:
            self.movie.setPlayRate(self._FAST_PLAYRATE)
        else:
            self.movie.setPlayRate(self._NORMAL_PLAYRATE)

    @property
    def block(self):
        return ToontownGlobals.GyrosLab % 100

    # *.prc defines (as properties)
    @property
    def movieOnDoorIn(self):
        try:
            # I actually tried this out earlier, and it works out pretty well
            # Then again, I did delay the episodeZone ready message until we finish with the door...
            # Also, I apologize for the horribly long name; I wanted to make it unique enough, but I apparently sucked
            # hard on that...
            return base.config.GetBool('episode-prologue-gyroslab-movieOnDoorIn', False)
        except Exception:
            self.notify.debug('Failed to acquire movieOnDoorIn config value; returning False.')
            return False

    @property
    def allowAdvanceMovie(self):
        if not __debug__:
            self.notify.debug('Devs only.')
            return False
        try:
            return base.config.GetBool('episode-prologue-gyroslab-allowAdvanceMovie', False)
        except Exception:
            self.notify.debug('Failed to acquire allowAdvanceMovie config value; returning False.')
            return False
