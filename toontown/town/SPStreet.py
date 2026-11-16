from direct.task.Task import Task

from panda3d.core import CompassEffect, NodePath, TransparencyAttrib
from panda3d.toontown import NametagGlobals

from otp.distributed.TelemetryLimiter import RotationLimitToH, TLGatherAllAvs

from toontown.hood import ZoneUtil
from toontown.hood import SkyUtil
from toontown.toonbase import ToontownGlobals
from toontown.battle import BattleParticles
from toontown.toon.Toon import teleportDebug

from . import Street


class SPStreet(Street.Street):

    def __init__(self, loader, parentFSM, doneEvent):
        Street.Street.__init__(self, loader, parentFSM, doneEvent)
        self.sky = self.loader.hood.sky
        self.skyFile = {ToontownGlobals.TutorialTerrace: None,
                        ToontownGlobals.CogtownCentral: 'phase_9/models/cogHQ/cog_sky',
                        ToontownGlobals.SellbotHQFuture: 'phase_9/models/cogHQ/cog_sky'}

    def load(self):
        Street.Street.load(self)

    def unload(self):
        Street.Street.unload(self)

    def enter(self, requestStatus, visibilityFlag = 1, arrowsOn = 1):
        teleportDebug(requestStatus, 'Street.enter(%s)' % (requestStatus,))
        self._ttfToken = None
        self.fsm.enterInitialState()
        base.playMusic(self.loader.music, looping=1, volume=0.8)
        self.loader.geom.reparentTo(render)
        if visibilityFlag:
            self.visibilityOn()
        base.localAvatar.setGeom(self.loader.geom)
        base.localAvatar.setOnLevelGround(1)
        self._telemLimiter = TLGatherAllAvs('Street', RotationLimitToH)
        NametagGlobals.setMasterArrowsOn(arrowsOn)

        self.accept('doorDoneEvent', self.handleDoorDoneEvent)
        self.accept('DistributedDoor_doorTrigger', self.handleDoorTrigger)
        zoneId = requestStatus['zoneId']
        self.enterZone(zoneId)
        if zoneId != ToontownGlobals.SellbotHQFuture:
            self.tunnelOriginList = base.cr.hoodMgr.addLinkTunnelHooks(self, self.loader.nodeList)
        else:
            self.zoneId = zoneId

        self.fsm.request(requestStatus['how'], [requestStatus])
        self.replaceStreetSignTextures()
        zoneId = ZoneUtil.getBranchZone(zoneId)
        base.cr.discordManager.setInfo(base.cr.discordManager.getState(), None, ToontownGlobals.Zone2String.get(ZoneUtil.getHoodId(zoneId)), None, None, None, zoneId)

        def __lightDecorationOn__():
            geom = base.cr.playGame.getPlace().loader.geom
            self.halloweenLights = geom.findAllMatches('**/*light*')
            self.halloweenLights += geom.findAllMatches('**/*lamp*')
            self.halloweenLights += geom.findAllMatches('**/prop_snow_tree*')
            for light in self.halloweenLights:
                light.setColorScaleOff(1)

        # Get Theme information
        decoration = ToontownGlobals.Theme2Decoration.get('tt')

        winter = False
        halloween = False
        newsManager = base.cr.newsManager
        if newsManager:
            holidayIds = base.cr.newsManager.getDecorationHolidayId()
            winter = (ToontownGlobals.WINTER_DECORATIONS in holidayIds or ToontownGlobals.WINTER_CAROLING in holidayIds) and decoration[ToontownGlobals.ThemeWinter]
            halloween = (ToontownGlobals.HALLOWEEN_COSTUMES in holidayIds or ToontownGlobals.SPOOKY_COSTUMES in holidayIds) and decoration[ToontownGlobals.ThemeHalloween]
            if winter:
                self.loader.hood.startWinterSky()
                __lightDecorationOn__()
            if halloween:
                self.loader.hood.startSpookySky()
                base.cr.playGame.hood.loader.geom.setColorScale(0.55, 0.55, 0.65, 1)
                __lightDecorationOn__()

        # Handle unique skyboxes on a per-zone basis
        skyFile = self.skyFile.get(ZoneUtil.getCanonicalBranchZone(self.zoneId))
        if not skyFile:
            skyFile = ToontownGlobals.Playground2Skybox.get('tt')

        # Use unique skybox so long as it's not Winter or Halloween (Tutorial Terrace get's excluded)
        if skyFile and ((not winter and not halloween) or self.zoneId != ToontownGlobals.TutorialTerrace):
            # Hide the hood skybox
            if hasattr(self, 'sky') and self.sky:
                self.loader.hood.stopSky()

            # Create a new skybox just for this street
            self.sky = loader.loadModel(skyFile)
            self.sky.setTag('sky', 'Street')

            # Misc sky flags
            self.sky.setDepthTest(0)
            self.sky.setDepthWrite(0)
            self.sky.setBin('background', 100)

            # Only darken the skybox in Cogtown Central or Sellbot HQ Future
            if self.zoneId in (ToontownGlobals.CogtownCentral, ToontownGlobals.SellbotHQFuture):
                self.sky.setColor(0.5, 0.5, 0.5, 1)

            # We want the Tutorial Terrace skybox to be affected by Fog
            if self.zoneId != ToontownGlobals.TutorialTerrace:
                self.sky.setFogOff()

            # Activate clouds if the Toontown Central skybox is used
            if skyFile == 'phase_3.5/models/props/TT_sky':
                self.sky.find('**/Sky').reparentTo(self.sky, -1)
                skyTrackTask = Task(SkyUtil.cloudSkyTrack)
                skyTrackTask.h = 0
                skyTrackTask.cloud1 = self.sky.find('**/cloud1')
                skyTrackTask.cloud2 = self.sky.find('**/cloud2')
                if not skyTrackTask.cloud1.isEmpty() and not skyTrackTask.cloud2.isEmpty():
                    taskMgr.add(skyTrackTask, 'skyTrack')

            # Remaining sky setup
            self.sky.reparentTo(camera)
            self.sky.setTransparency(TransparencyAttrib.MDual, 1)
            self.sky.setZ(0.0)
            self.sky.setHpr(0.0, 0.0, 0.0)
            ce = CompassEffect.make(NodePath(), CompassEffect.PRot | CompassEffect.PZ)
            self.sky.node().setEffect(ce)

    def hideAllVisibles(self):
        if base.localAvatar.zoneId == ToontownGlobals.SellbotHQFuture:
            return
        Street.Street.hideAllVisibles(self)

    def showAllVisibles(self):
        if base.localAvatar.zoneId == ToontownGlobals.SellbotHQFuture:
            return
        Street.Street.showAllVisibles(self)

    def enterZone(self, newZone):
        if base.localAvatar.zoneId == ToontownGlobals.SellbotHQFuture:
            return
        Street.Street.enterZone(self, newZone)

    def doEnterZone(self, newZoneId):
        if base.localAvatar.zoneId == ToontownGlobals.SellbotHQFuture:
            return
        Street.Street.doEnterZone(self, newZoneId)

    def exit(self, visibilityFlag = 1):
        Street.Street.exit(self, visibilityFlag)

        messenger.send('exitSafeZone')

        # Get theme information
        decoration = ToontownGlobals.Theme2Decoration.get('tt')

        # Disable snow if we have any
        if hasattr(self, 'snow'):
            self.snow.cleanup()
            del self.snow
        if hasattr(self, 'snowRender'):
            del self.snowRender

        # Remove Fog if the theme called for it (only in Tutorial Terrrace)
        if (decoration[ToontownGlobals.ThemeFog] or decoration[ToontownGlobals.ThemeWinter]) and self.zoneId == ToontownGlobals.TutorialTerrace:
            self.loader.hood.setNoFog()

        # Cleanup unique street skybox
        if hasattr(self, 'sky') and self.sky:
            self.sky.removeNode()
            del self.sky
