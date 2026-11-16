from direct.showbase.MessengerGlobal import messenger
from panda3d.core import *

from otp.otpbase.PythonUtil import uniqueName
from otp.otpgui import OTPGUIUtils
from toontown.toonbase.ToontownGlobals import *
from toontown.distributed.ToontownMsgTypes import *
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import StateData
from direct.task.Task import Task
from toontown.minigame import Purchase
from direct.gui import OnscreenText
from toontown.building import SuitInterior
from . import QuietZoneState
from . import ZoneUtil
from toontown.toonbase import TTLocalizer, ToontownGlobals
from toontown.toon.Toon import teleportDebug
from direct.interval.IntervalGlobal import *
from toontown.episodes import EpisodeConfig

class Hood(StateData.StateData):
    notify = DirectNotifyGlobal.directNotify.newCategory('Hood')

    def __init__(self, parentFSM, doneEvent, dnaStore, hoodId):
        StateData.StateData.__init__(self, doneEvent)
        self.loader = 'not initialized'
        self.parentFSM = parentFSM
        self.dnaStore = dnaStore
        self.loaderDoneEvent = 'loaderDone'
        self.id = None
        self.hoodId = hoodId
        self.titleText = None
        self.titleTextSeq = None
        self.titleColor = (1, 1, 1, 1)
        self.holidayStorageDNADict = {}
        self.sky = None
        self.spookySkyFile = None
        self.winterSkyFile = None
        self.halloweenLights = []

    def enter(self, requestStatus):
        hoodId = requestStatus['hoodId']
        zoneId = requestStatus['zoneId']
        hoodText = self.getHoodText(zoneId)
        if hoodText:
            color = self.titleColor
            if isinstance(color, dict):
                color = color.get(zoneId)
            self.titleText = OnscreenText.OnscreenText(hoodText, fg=color, font=getSignFont(), pos=(0, -0.5),
                                                       scale=TTLocalizer.HtitleText, drawOrder=0, mayChange=1)
            self.titleText.hide()
        self.fsm.request(requestStatus['loader'], [requestStatus])
        base.cr.discordManager.setInfo(base.cr.discordManager.getState(), None,
                                       ToontownGlobals.Zone2String.get(zoneId), None, None, None, zoneId)

    def getHoodText(self, zoneId):
        hoodText = base.cr.hoodMgr.getFullnameFromId(self.id)
        if self.id != Tutorial:
            streetName = StreetNames.get(ZoneUtil.getCanonicalBranchZone(zoneId))
            if streetName:
                hoodText = hoodText + '\n' + streetName[-1]
        return hoodText

    def spawnTitleText(self, zoneId):
        hoodText = self.getHoodText(zoneId)
        self.doSpawnTitleText(hoodText, zoneId)

    def doSpawnTitleText(self, text, zoneId):
        if not text or not self.titleText:
            return
        self.titleText.setText(text)
        self.titleText.show()
        color = self.titleColor
        if isinstance(color, dict):
            color = color.get(zoneId)
        self.titleText.setColor(Vec4(*color))
        self.titleText.clearColorScale()
        self.titleText.setFg(color)
        self.titleTextSeq = Sequence(
            OTPGUIUtils.Animations.popup(self.titleText),
            Wait(5.5),
            LerpColorScaleInterval(self.titleText, 0.3, Vec4(1, 1, 1, 0), blendType = 'easeInOut'),
            Func(self.hideTitleText)
        )
        self.titleTextSeq.start()

    def hideTitleText(self):
        if self.titleText:
            self.titleText.hide()

    def exit(self):
        if self.titleTextSeq:
            self.titleTextSeq.finish()
            self.titleTextSeq = None
        if self.titleText:
            self.titleText.cleanup()
            self.titleText = None
        base.localAvatar.stopChat()
        return

    def load(self):
        if self.storageDNAFile:
            if isinstance(self.storageDNAFile, tuple):
                for storage in self.storageDNAFile:
                    loader.loadDNAFile(self.dnaStore, storage)
            else:
                loader.loadDNAFile(self.dnaStore, self.storageDNAFile)
        newsManager = base.cr.newsManager
        if newsManager:
            holidayIds = base.cr.newsManager.getDecorationHolidayId()
            for holiday in holidayIds:
                for storageFile in self.holidayStorageDNADict.get(holiday, []):
                    loader.loadDNAFile(self.dnaStore, storageFile)

            if (ToontownGlobals.HALLOWEEN_COSTUMES not in holidayIds and ToontownGlobals.SPOOKY_COSTUMES not in holidayIds or not self.spookySkyFile) and hasattr(self, 'skyFile'):
                self.sky = loader.loadModel(self.skyFile)
                self.sky.setTag('sky', 'Regular')
                self.sky.setScale(1.0)
                self.sky.setFogOff()
            elif ToontownGlobals.HALLOWEEN_COSTUMES in holidayIds or ToontownGlobals.SPOOKY_COSTUMES in holidayIds or self.spookySkyFile:
                self.sky = loader.loadModel(self.spookySkyFile)
                self.sky.setTag('sky', 'Halloween')
        if not newsManager:
            self.sky = loader.loadModel(self.skyFile)
            self.sky.setTag('sky', 'Regular')
            self.sky.setScale(1.0)
            self.sky.setFogOff()

    def unload(self):
        if hasattr(self, 'loader'):
            self.notify.info('Aggressively cleaning up loader: %s' % self.loader)
            self.loader.exit()
            self.loader.unload()
            del self.loader
        del self.fsm
        del self.parentFSM
        self.dnaStore.resetHood()
        del self.dnaStore
        if hasattr(self, 'sky') and self.sky:
            self.sky.removeNode()
            del self.sky
        self.ignoreAll()
        ModelPool.garbageCollect()
        TexturePool.garbageCollect()

    def enterStart(self):
        pass

    def exitStart(self):
        pass

    def isSameHood(self, status):
        return status['hoodId'] == self.hoodId

    def enterFinal(self):
        pass

    def exitFinal(self):
        pass

    def enterQuietZone(self, requestStatus):
        teleportDebug(requestStatus, 'Hood.enterQuietZone: status=%s' % requestStatus)
        self._quietZoneDoneEvent = uniqueName('quietZoneDone')
        self.acceptOnce(self._quietZoneDoneEvent, self.handleQuietZoneDone)
        self.quietZoneStateData = QuietZoneState.QuietZoneState(self._quietZoneDoneEvent)
        self._enterWaitForSetZoneResponseMsg = self.quietZoneStateData.getEnterWaitForSetZoneResponseMsg()
        self.acceptOnce(self._enterWaitForSetZoneResponseMsg, self.handleWaitForSetZoneResponse)
        self._quietZoneLeftEvent = self.quietZoneStateData.getQuietZoneLeftEvent()
        if base.placeBeforeObjects:
            self.acceptOnce(self._quietZoneLeftEvent, self.handleLeftQuietZone)
        self.quietZoneStateData.load()
        self.quietZoneStateData.enter(requestStatus)

    def exitQuietZone(self):
        self.ignore(self._quietZoneDoneEvent)
        self.ignore(self._quietZoneLeftEvent)
        self.ignore(self._enterWaitForSetZoneResponseMsg)
        del self._quietZoneDoneEvent
        self.quietZoneStateData.exit()
        self.quietZoneStateData.unload()
        self.quietZoneStateData = None
        return

    def loadLoader(self, requestStatus):
        pass

    def handleWaitForSetZoneResponse(self, requestStatus):
        loaderName = requestStatus['loader']
        if loaderName == 'safeZoneLoader':
            if not loader.inBulkBlock:
                loader.beginBulkLoad('hood', TTLocalizer.HeadingToPlayground, safeZoneCountMap[self.id], 1, TTLocalizer.TIP_GENERAL, requestStatus.get('zoneId', None))
            self.loadLoader(requestStatus)
            loader.endBulkLoad('hood')
        elif loaderName == 'townLoader':
            if not loader.inBulkBlock:
                zoneId = requestStatus['zoneId']
                toPhrase = StreetNames[ZoneUtil.getCanonicalBranchZone(zoneId)][0]
                streetName = StreetNames[ZoneUtil.getCanonicalBranchZone(zoneId)][-1]
                loader.beginBulkLoad('hood', TTLocalizer.HeadingToStreet % {'to': toPhrase, 'street': streetName}, townCountMap[self.id], 1, TTLocalizer.TIP_STREET,
                                     ZoneUtil.getCanonicalBranchZone(zoneId))
            self.loadLoader(requestStatus)
            loader.endBulkLoad('hood')
        elif loaderName == 'minigame':
            pass
        elif loaderName == 'cogHQLoader':
            print('should be loading HQ')
        elif loaderName == 'episodeLoader':
            self.loadLoader(requestStatus)

    def handleLeftQuietZone(self):
        status = self.quietZoneStateData.getRequestStatus()
        teleportDebug(status, 'handleLeftQuietZone, status=%s' % status)
        teleportDebug(status, 'requesting %s' % status['loader'])
        self.fsm.request(status['loader'], [status])

    def handleQuietZoneDone(self):
        if not base.placeBeforeObjects:
            status = self.quietZoneStateData.getRequestStatus()
            self.fsm.request(status['loader'], [status])

    def enterSafeZoneLoader(self, requestStatus):
        self.accept(self.loaderDoneEvent, self.handleSafeZoneLoaderDone)
        self.loader.enter(requestStatus)
        if not base.cr.buildLot:
            self.spawnTitleText(requestStatus['zoneId'])

    def exitSafeZoneLoader(self):
        if self.titleTextSeq:
            self.titleTextSeq.finish()
            self.titleTextSeq = None
        self.hideTitleText()
        self.ignore(self.loaderDoneEvent)
        self.loader.exit()
        self.loader.unload()
        del self.loader

    def handleSafeZoneLoaderDone(self):
        doneStatus = self.loader.getDoneStatus()
        teleportDebug(doneStatus, 'handleSafeZoneLoaderDone, doneStatus=%s' % doneStatus)
        if self.isSameHood(doneStatus) and doneStatus['where'] != 'party' or doneStatus['loader'] == 'minigame':
            teleportDebug(doneStatus, 'same hood')
            self.fsm.request('quietZone', [doneStatus])
        else:
            teleportDebug(doneStatus, 'different hood')
            self.doneStatus = doneStatus
            messenger.send(self.doneEvent)

    def startSky(self):
        self.sky.reparentTo(camera)
        self.sky.setZ(0.0)
        self.sky.setHpr(0.0, 0.0, 0.0)
        ce = CompassEffect.make(NodePath(), CompassEffect.PRot | CompassEffect.PZ)
        self.sky.node().setEffect(ce)
        messenger.send('resumeFireworks')

    def stopSky(self):
        taskMgr.remove('skyTrack')
        if hasattr(self, 'sky') and self.sky:
            self.sky.reparentTo(hidden)

    def startSpookySky(self):
        if not self.spookySkyFile:
            return
        if hasattr(self, 'sky') and self.sky:
            self.stopSky()
        self.sky = loader.loadModel(self.spookySkyFile)
        self.sky.setTag('sky', 'Halloween')
        self.sky.setColor(0.5, 0.5, 0.5, 1)
        self.sky.reparentTo(camera)
        self.sky.setTransparency(TransparencyAttrib.MDual, 1)
        fadeIn = self.sky.colorScaleInterval(1.5, Vec4(1, 1, 1, 1), startColorScale=Vec4(1, 1, 1, 0.25), blendType='easeInOut')
        fadeIn.start()
        self.sky.setZ(0.0)
        self.sky.setHpr(0.0, 0.0, 0.0)
        ce = CompassEffect.make(NodePath(), CompassEffect.PRot | CompassEffect.PZ)
        self.sky.node().setEffect(ce)
        messenger.send('resumeFireworks')

    def startWinterSky(self):
        if not self.winterSkyFile:
            return
        if hasattr(self, 'sky') and self.sky:
            self.stopSky()
        self.sky = loader.loadModel(self.winterSkyFile)
        self.sky.setTag('sky', 'Winter')
        self.sky.setDepthTest(0)
        self.sky.setDepthWrite(0)
        self.sky.setColor(0.9, 0.9, 0.9, 1)
        self.sky.setBin('background', 100)
        self.sky.setFogOff()
        self.sky.reparentTo(camera)
        self.sky.setTransparency(TransparencyAttrib.MDual, 1)
        fadeIn = self.sky.colorScaleInterval(1.5, Vec4(1, 1, 1, 1), startColorScale=Vec4(1, 1, 1, 0.25), blendType='easeInOut')
        fadeIn.start()
        self.sky.setZ(0.0)
        self.sky.setHpr(0.0, 0.0, 0.0)
        ce = CompassEffect.make(NodePath(), CompassEffect.PRot | CompassEffect.PZ)
        self.sky.node().setEffect(ce)
        messenger.send('resumeFireworks')

    def endHolidaySky(self):
        if hasattr(self, 'sky') and self.sky:
            self.sky.reparentTo(hidden)
        if hasattr(self, 'sky'):
            self.sky = loader.loadModel(self.skyFile)
            self.sky.setTag('sky', 'Regular')
            self.sky.setScale(1.0)
            self.startSky()
