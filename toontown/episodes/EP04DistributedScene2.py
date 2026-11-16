import random

from direct.actor import Actor
from direct.directutil import Mopath
from direct.gui.DirectLabel import DirectLabel
from direct.gui.DirectWaitBar import DirectWaitBar
from direct.gui.OnscreenText import OnscreenText
from direct.interval.IntervalGlobal import *
from direct.showbase import Audio3DManager

from panda3d.toontown import *

from panda3d.core import *

from otp.otpbase import OTPGlobals
from toontown.episodes import EpisodeLocalizer
from otp.otpbase.PythonUtil import weightedChoice
from toontown.avatar import ToontownAvatarUtils
from toontown.episodes import DistributedEpisodeZone, EpisodeLocalizer
from toontown.episodes import EpisodeConfig
from toontown.episodes.EpisodeGlobals import *
from toontown.hood import SkyUtil
from toontown.hood.PetShopFishAnimatedProp import PetShopFishAnimatedProp
from toontown.parties import PartyGlobals
from toontown.toontowngui.ServerTimeGui import ServerTimeGui
from toontown.toon.ToonDNA import ToonDNA
from toontown.toonbase import TTLocalizer, ToontownGlobals, HotkeySettings, ControlManager

from toontown.makeatoon import NameGenerator


class EP04DistributedScene2(DistributedEpisodeZone.DistributedEpisodeZone):

    def __init__(self, cr):
        DistributedEpisodeZone.DistributedEpisodeZone.__init__(self, cr)

        self.toons = []
        self.episodeZoneId = EpisodeConfig.EP04_INTRO

        # QTE
        self.__chewProgress = 0.0
        self.__chewQTEStarted = False
        self.__chewDecayTaskName = 'chew-qte-decay'

    def disable(self):
        DistributedEpisodeZone.DistributedEpisodeZone.disable(self)
        self.sky.removeNode()
        taskMgr.remove('skyTrack')
        for toon in self.toons:
            toon.delete()

    def generateGeom(self):
        base.loader.beginBulkLoad('episode', TTLocalizer.HeadingToHood % {
            'to': TTLocalizer.ToontownCentral[0],
            'hood': "????"
        }, 12, 1, TTLocalizer.TIP_OFFLINE_MODE)
        loader.loadDNAFile(base.cr.playGame.hood.dnaStore, 'phase_4/dna/ttrm_d_strg_ttc.dna')
        loader.loadDNAFile(base.cr.playGame.hood.dnaStore, 'phase_4/dna/ttrm_d_strg_ttc_sz.dna')
        loader.loadDNAFile(base.cr.playGame.hood.dnaStore, 'phase_5/dna/ttrm_d_strg_ttc_town.dna')

        node = loader.loadDNAFile(base.cr.playGame.hood.dnaStore, 'phase_14/dna/ttrm_d_ara_ttc_1_ep04.dna')
        if node.getNumParents() == 1:
            self.geom = NodePath(node.getParent(0))
            self.geom.reparentTo(render)
        else:
            self.geom = render.attachNewNode(node)
        base.loader.tick()

        self.geom.flattenMedium()

        # Hide the black parts in the doors
        doorHoles = self.geom.findAllMatches('**/doorFrameHole*')
        for hole in doorHoles:
            hole.removeNode()

        base.loader.tick()

        self.audio3d = Audio3DManager.Audio3DManager(base.sfxManagerList[0], camera)

        self.sounds = {
        }  # type: dict[str, AudioSound]

        base.loader.tick()

        cSphere = CollisionSphere(0.0, 0.0, 0.0, 8)
        cSphere.setTangible(0)
        cSphereNode = CollisionNode('door_interact')
        cSphereNode.addSolid(cSphere)
        self.cSphereNodePath = self.geom.attachNewNode(cSphereNode)
        self.cSphereNodePath.setPos(1175, 20, 0.03)
        #self.cSphereNodePath.show()
        cSphereNode.setCollideMask(ToontownGlobals.WallBitmask)

        base.loader.tick()

        self.sky = loader.loadModel('phase_3.5/models/props/TT_sky')
        self.sky.reparentTo(self.geom)

        self.startCloudSky()

        gsg = base.win.getGsg()
        if gsg:
            self.geom.prepareScene(gsg)

        self.acceptOnce('enterdoor_interact', self.__interactWithDoor)

        gsg = base.win.getGsg()
        if gsg:
            self.geom.prepareScene(gsg)

        base.loader.tick()
        base.loader.endBulkLoad('episode')

    def startCloudSky(self):
        return SkyUtil.startCloudSky(self)

    def skyTrack(self, task):
        return SkyUtil.cloudSkyTrack(task)

    def generateMovie(self):
        self.generateStory()
        self.story.hide()

        self.movie = Sequence(
                Func(self.lockToon),

                # mput movie here

                # EXIT
                Func(self.toon.show),
                Func(self.releaseToon),
                Func(self.toon.enableAvatarControls),
                Func(self.toon.setPosHpr, self.toon, 20, 20.5, 0, -90, 0, 0),

                name = 'ep402_movie_main'
        )

        # Func(self.teleportToZone, self.zoneConnections[0])))

    def __interactWithDoor(self, collEntry):
        # gameplay prototype, obviously not final
        self.lockToon()

        self.toon.animFSM.request('Push')
        self.toon.setPos(1174, 20, 0.03)
        base.camera.setPosHpr(Vec3(1160, 6.3, 2.26),
                              Vec3(-48, 3, 0))

        # show a tooltip
        text: str = ControlManager.ControlManager.parseHotkeyString(TTLocalizer.EP04_InteractWithDoor, useGlyphs=True)
        self.qteSpamHint = OnscreenText(text, style = 3, scale = .065, parent = aspect2d,
                                        font = ToontownGlobals.getSuitFont(), fg = (0.5, 0.5, 0.5, 1.0),
                                        pos = (0.0, -0.45))
        self.qteSpamProgress = DirectWaitBar(range = 100.0, value = 0.0, pos = (0.0, 0.0, -0.6), scale = 0.8)

        self.accept(HotkeySettings.Interact.getPressed(),
                    self.__chewQTETap)

    def __chewQTETap(self):
        self.__chewProgress += 10.0
        if not self.__chewQTEStarted:
            self.__chewQTEStarted = True
            self.doMethodLater(0.08, self.__chewQTEDecay, self.__chewDecayTaskName)
        self.__updateQTEProgress()

    def __chewQTEDecay(self, task):
        self.__chewProgress -= 1.0
        self.__updateQTEProgress()
        return task.again

    def __updateQTEProgress(self):
        self.qteSpamProgress['value'] = self.__chewProgress
        if self.__chewProgress < 0:
            self.removeTask(self.__chewDecayTaskName)
            self.ignore(HotkeySettings.Interact.getPressed())
            self.qteSpamProgress.destroy()
            self.qteSpamHint.destroy()
            self.generateStory()
            self.story.hide()
            self.story.setPos(-0.8, 0, -0.5)

            seq = Sequence(
                    Func(self.enterText, self.story),
                    Func(self.speakText, self.story, EpisodeLocalizer.SosFailDoorCard),
                    self.toon.getDiedInterval(),
                    Func(messenger.send, 'stopEpisode')
            )
            seq.start()

        if self.__chewProgress >= 100:
            self.removeTask(self.__chewDecayTaskName)
            self.ignore(HotkeySettings.Interact.getPressed())
            self.qteSpamProgress.destroy()
            self.qteSpamHint.destroy()
            self.teleportToZone(self.zoneConnections[0])
