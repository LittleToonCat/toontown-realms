import random

from direct.actor import Actor
from direct.directutil import Mopath
from direct.gui.DirectLabel import DirectLabel
from direct.gui.OnscreenImage import OnscreenImage
from direct.interval.IntervalGlobal import *
from direct.showbase import Audio3DManager

from panda3d.toontown import *

from panda3d.core import *

from toontown.episodes import EpisodeLocalizer
from otp.otpbase.PythonUtil import weightedChoice
from toontown.avatar import ToontownAvatarUtils
from toontown.episodes import DistributedEpisodeZone, EpisodeLocalizer
from toontown.episodes import EpisodeConfig
from toontown.episodes.EpisodeGlobals import *
from toontown.hood.PetShopFishAnimatedProp import PetShopFishAnimatedProp
from toontown.parties import PartyGlobals
from toontown.toontowngui.ServerTimeGui import ServerTimeGui
from toontown.toon.ToonDNA import ToonDNA
from toontown.toonbase import TTLocalizer, ToontownGlobals

from toontown.makeatoon import NameGenerator


class EP04DistributedScene3(DistributedEpisodeZone.DistributedEpisodeZone):

    def __init__(self, cr):
        DistributedEpisodeZone.DistributedEpisodeZone.__init__(self, cr)

        self.toons = []
        self.episodeZoneId = EpisodeConfig.EP04_INTRO

    def disable(self):
        DistributedEpisodeZone.DistributedEpisodeZone.disable(self)
        for toon in self.toons:
            toon.delete()
            del toon

    def generateGeom(self):
        base.loader.beginBulkLoad('episode', 'Entering ????', 3, 1, TTLocalizer.TIP_OFFLINE_MODE)

        self.geom = loader.loadModel('phase_14/models/modules/ttoff_m_ara_int_sosAtwScrooge')
        self.geom.reparentTo(render)
        base.loader.tick()

        self.geom.flattenMedium()
        base.loader.tick()

        self.toon.setPosHpr(0, 0, 0, 0, 0, 0)

        self.scrooge = ToontownAvatarUtils.createToon(30000)
        self.scrooge.reparentTo(self.geom)
        self.scrooge.setPos(Vec3(0, 17, 0.3))
        self.scrooge.setH(180)
        self.scrooge.animFSM.request('Sit')
        self.scrooge.addActive()

        self.toons.append(self.scrooge)

        base.loader.tick()

        self.sounds = {
        }  # type: dict[str, AudioSound]

        gsg = base.win.getGsg()
        if gsg:
            self.geom.prepareScene(gsg)

        base.loader.tick()
        base.loader.endBulkLoad('episode')

    def generateMovie(self):
        self.generateStory()
        self.story.hide()

        TTOFFLOGO = OnscreenImage(parent = aspect2dp,
                                  image = "phase_3/maps/ttoff_t_gamelogo_aprilToons2022.png", scale = (1.0, 1.0, 0.5))
        TTOFFLOGO.hide()
        TTOFFLOGO.setTransparency(TransparencyAttrib.MAlpha)

        SOSLOGO = OnscreenImage(parent = aspect2dp,
                                  image = "phase_3/maps/ttoff_t_gui_sosLogo.png", scale = (1.43165468, 1.0, 1.0))
        SOSLOGO.hide()
        SOSLOGO.setTransparency(TransparencyAttrib.MAlpha)


        self.movie = Sequence(
                Func(self.lockToon),
                Func(self.toon.animFSM.request, 'neutral'),

                Func(base.camera.setPosHpr, Vec3(0.97, 10.39, 7.02), Vec3(5.52, 5.85, 0)),
                Wait(1),
                LerpPosHprInterval(base.camera, 3,
                                   Vec3(-2.58, 5.66, 1.31),
                                   Vec3(-10.45, 5.85, 0),
                                   blendType = 'easeInOut'),
                Wait(0.4),

                self.getChatSequence(self.scrooge, EpisodeLocalizer.Sos4ScroogeIntro[0], wait = 3, preClear = True),


                self.getChatSequence(self.scrooge, EpisodeLocalizer.Sos4ScroogeIntro[1], wait = 3, preClear = True),

                Func(base.camera.setPosHpr, Vec3(16.87, -9, 1.33), Vec3(43, 5.7, 0.0)),

                self.getChatSequence(self.scrooge, EpisodeLocalizer.Sos4ScroogeIntro[2], wait = 3, preClear = True),
                self.getChatSequence(self.scrooge, EpisodeLocalizer.Sos4ScroogeIntro[3], wait = 3, preClear = True),
                self.getChatSequence(self.scrooge, EpisodeLocalizer.Sos4ScroogeIntro[4], wait = 3, preClear = True),
                self.getChatSequence(self.scrooge, EpisodeLocalizer.Sos4ScroogeIntro[5], wait = 3, preClear = True),
                self.getChatSequence(self.scrooge, EpisodeLocalizer.Sos4ScroogeIntro[6], wait = 3, preClear = True),
                self.getChatSequence(self.scrooge, EpisodeLocalizer.Sos4ScroogeIntro[7], wait = 3, preClear = True),
                self.getChatSequence(self.scrooge, EpisodeLocalizer.Sos4ScroogeIntro[8], wait = 3, preClear = True),
                self.getChatSequence(self.scrooge, EpisodeLocalizer.Sos4ScroogeIntro[9], wait = 3, preClear = True),
                self.getChatSequence(self.scrooge, EpisodeLocalizer.Sos4ScroogeIntro[10], wait = 3, preClear = True),
                self.getChatSequence(self.scrooge, EpisodeLocalizer.Sos4ScroogeIntro[11], wait = 3, preClear = True),
                self.getChatSequence(self.scrooge, EpisodeLocalizer.Sos4ScroogeIntro[12], wait = 3, preClear = True),
                self.getChatSequence(self.scrooge, EpisodeLocalizer.Sos4ScroogeIntro[13], wait = 3, preClear = True),
                self.getChatSequence(self.scrooge, EpisodeLocalizer.Sos4ScroogeIntro[14], wait = 0.2, preClear = True),

                Func(base.transitions.fadeOut, 2),
                Wait(2),

                Func(TTOFFLOGO.show),
                LerpColorScaleInterval(TTOFFLOGO, 2, VBase4(1.0), VBase4(1.0, 1.0, 1.0, 0.0)),
                Wait(3),
                LerpColorScaleInterval(TTOFFLOGO, 2, VBase4(1.0, 1.0, 1.0, 0.0), VBase4(1.0)),
                Func(TTOFFLOGO.hide),

                Func(SOSLOGO.show),
                LerpColorScaleInterval(SOSLOGO, 2, VBase4(1.0), VBase4(1.0, 1.0, 1.0, 0.0)),
                Wait(3),
                LerpColorScaleInterval(SOSLOGO, 2, VBase4(1.0, 1.0, 1.0, 0.0), VBase4(1.0)),
                Func(SOSLOGO.hide),
                Func(messenger.send, 'stopEpisode'),

                name = 'ep401_movie_main'
        )

        # Func(self.teleportToZone, self.zoneConnections[0])))
    def enterTunnel(self, collEntry):
        self.teleportToZone(self.zoneConnections[0])