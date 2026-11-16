from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM
from direct.fsm import State
from direct.showbase.DirectObject import DirectObject
from direct.showbase.MessengerGlobal import messenger
from direct.task.Task import Task
from direct.task.TaskManagerGlobal import taskMgr
from panda3d.core import TexturePool, ModelPool
from panda3d.toontown import DNAStorage

from toontown.hood import BRBetaHood, TLFFHood
from toontown.hood import BRHood
from toontown.hood import DDBetaHood
from toontown.hood import DDHood
from toontown.hood import DGBetaHood
from toontown.hood import DGHood
from toontown.hood import DLBetaHood
from toontown.hood import DLHood
from toontown.hood import EpisodeHood
from toontown.hood import EstateHood
from toontown.hood import GSHood
from toontown.hood import GZHood
from toontown.hood import MMBetaHood
from toontown.hood import MMHood
from toontown.hood import OZHood
from toontown.hood import PartyHood
from toontown.hood import QuietZoneState
from toontown.hood import SellbotHQ, CashbotHQ, LawbotHQ, BossbotHQ
from toontown.hood import SpecialHood
from toontown.hood import TTBetaHood
from toontown.hood import TTHood, CFHood
from toontown.hood import TutorialHood
from toontown.hood import ZoneUtil
from toontown.toonbase import ToontownGlobals, TTLocalizer
from toontown.toonbase.ToonBaseGlobal import *


class PlayGame(DirectObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('PlayGame')
    Hood2ClassDict = {
        ToontownGlobals.ToontownCentral: TTHood.TTHood,
        ToontownGlobals.DonaldsDock: DDHood.DDHood,
        ToontownGlobals.TheBrrrgh: BRHood.BRHood,
        ToontownGlobals.MinniesMelodyland: MMHood.MMHood,
        ToontownGlobals.DaisyGardens: DGHood.DGHood,
        ToontownGlobals.DonaldsDreamland: DLHood.DLHood,
        ToontownGlobals.GoofySpeedway: GSHood.GSHood,
        ToontownGlobals.OutdoorZone: OZHood.OZHood,
        ToontownGlobals.Tutorial: TutorialHood.TutorialHood,
        ToontownGlobals.MyEstate: EstateHood.EstateHood,
        ToontownGlobals.BossbotHQ: BossbotHQ.BossbotHQ,
        ToontownGlobals.SellbotHQ: SellbotHQ.SellbotHQ,
        ToontownGlobals.CashbotHQ: CashbotHQ.CashbotHQ,
        ToontownGlobals.LawbotHQ: LawbotHQ.LawbotHQ,
        ToontownGlobals.GolfZone: GZHood.GZHood,
        ToontownGlobals.PartyHood: PartyHood.PartyHood,
        ToontownGlobals.ToontownOutskirts: SpecialHood.SpecialHood,
        ToontownGlobals.ToontownCentralBeta: TTBetaHood.TTBetaHood,
        ToontownGlobals.DaisyGardensBeta: DGBetaHood.DGBetaHood,
        ToontownGlobals.MinniesMelodylandBeta: MMBetaHood.MMBetaHood,
        ToontownGlobals.DonaldsDreamlandBeta: DLBetaHood.DLBetaHood,
        ToontownGlobals.TheBrrrghBeta: BRBetaHood.BRBetaHood,
        ToontownGlobals.DonaldsDockBeta: DDBetaHood.DDBetaHood,
        ToontownGlobals.Episode: EpisodeHood.EpisodeHood,
        ToontownGlobals.ToonLandFunnyFarm: TLFFHood.TLFFHood,
        ToontownGlobals.ToontownSkies: CFHood.CFHood

    }
    Hood2StateDict = {
        ToontownGlobals.ToontownCentral: 'TTHood',
        ToontownGlobals.DonaldsDock: 'DDHood',
        ToontownGlobals.TheBrrrgh: 'BRHood',
        ToontownGlobals.MinniesMelodyland: 'MMHood',
        ToontownGlobals.DaisyGardens: 'DGHood',
        ToontownGlobals.DonaldsDreamland: 'DLHood',
        ToontownGlobals.GoofySpeedway: 'GSHood',
        ToontownGlobals.OutdoorZone: 'OZHood',
        ToontownGlobals.Tutorial: 'TutorialHood',
        ToontownGlobals.MyEstate: 'EstateHood',
        ToontownGlobals.BossbotHQ: 'BossbotHQ',
        ToontownGlobals.SellbotHQ: 'SellbotHQ',
        ToontownGlobals.CashbotHQ: 'CashbotHQ',
        ToontownGlobals.LawbotHQ: 'LawbotHQ',
        ToontownGlobals.GolfZone: 'GZHood',
        ToontownGlobals.PartyHood: 'PartyHood',
        ToontownGlobals.ToontownOutskirts: 'SpecialHood',
        ToontownGlobals.ToontownCentralBeta: 'TTBetaHood',
        ToontownGlobals.DaisyGardensBeta: 'DGBetaHood',
        ToontownGlobals.MinniesMelodylandBeta: 'MMBetaHood',
        ToontownGlobals.DonaldsDreamlandBeta: 'DLBetaHood',
        ToontownGlobals.TheBrrrghBeta: 'BRBetaHood',
        ToontownGlobals.DonaldsDockBeta: 'DDBetaHood',
        ToontownGlobals.Episode: 'EpisodeHood',
        ToontownGlobals.ToonLandFunnyFarm: 'TLFFHood',
        ToontownGlobals.ToontownSkies: 'CFHood'

    }

    def __init__(self, parentFSM):
        self.place = None
        self.fsm = ClassicFSM.ClassicFSM('PlayGame', [
            State.State('start', self.enterStart, self.exitStart, ['quietZone']),
            State.State('quietZone', self.enterQuietZone, self.exitQuietZone,
                        [
                            'TTHood',
                            'DDHood',
                            'BRHood',
                            'MMHood',
                            'DGHood',
                            'DLHood',
                            'GSHood',
                            'OZHood',
                            'GZHood',
                            'SellbotHQ',
                            'CashbotHQ',
                            'LawbotHQ',
                            'BossbotHQ',
                            'TutorialHood',
                            'EstateHood',
                            'PartyHood',
                            'SpecialHood',
                            'TTBetaHood',
                            'DGBetaHood',
                            'MMBetaHood',
                            'DLBetaHood',
                            'BRBetaHood',
                            'DDBetaHood',
                            'EpisodeHood',
                            'CFHood',
                            'TLFFHood']),
         State.State('TTHood', self.enterTTHood, self.exitTTHood, ['quietZone']),
         State.State('DDHood', self.enterDDHood, self.exitDDHood, ['quietZone']),
         State.State('BRHood', self.enterBRHood, self.exitBRHood, ['quietZone']),
         State.State('MMHood', self.enterMMHood, self.exitMMHood, ['quietZone']),
         State.State('DGHood', self.enterDGHood, self.exitDGHood, ['quietZone']),
         State.State('DLHood', self.enterDLHood, self.exitDLHood, ['quietZone']),
         State.State('GSHood', self.enterGSHood, self.exitGSHood, ['quietZone']),
         State.State('OZHood', self.enterOZHood, self.exitOZHood, ['quietZone']),
         State.State('GZHood', self.enterGZHood, self.exitGZHood, ['quietZone']),
         State.State('BossbotHQ', self.enterBossbotHQ, self.exitBossbotHQ, ['quietZone']),
         State.State('SellbotHQ', self.enterSellbotHQ, self.exitSellbotHQ, ['quietZone']),
         State.State('CashbotHQ', self.enterCashbotHQ, self.exitCashbotHQ, ['quietZone']),
         State.State('LawbotHQ', self.enterLawbotHQ, self.exitLawbotHQ, ['quietZone']),
         State.State('TutorialHood', self.enterTutorialHood, self.exitTutorialHood, ['quietZone']),
         State.State('EstateHood', self.enterEstateHood, self.exitEstateHood, ['quietZone']),
         State.State('PartyHood', self.enterPartyHood, self.exitPartyHood, ['quietZone']),
         State.State('SpecialHood', self.enterSpecialHood, self.exitSpecialHood, ['quietZone']),
         State.State('TTBetaHood', self.enterTTBetaHood, self.exitTTBetaHood, ['quietZone']),
         State.State('DGBetaHood', self.enterDGBetaHood, self.exitDGBetaHood, ['quietZone']),
         State.State('MMBetaHood', self.enterMMBetaHood, self.exitMMBetaHood, ['quietZone']),
         State.State('DLBetaHood', self.enterDLBetaHood, self.exitDLBetaHood, ['quietZone']),
         State.State('BRBetaHood', self.enterBRBetaHood, self.exitBRBetaHood, ['quietZone']),
         State.State('DDBetaHood', self.enterDDBetaHood, self.exitDDBetaHood, ['quietZone']),
         State.State('EpisodeHood', self.enterEpisodeHood, self.exitEpisodeHood, ['quietZone']),
         State.State('CFHood', self.enterCFHood, self.exitCFHood, ['quietZone']),
         State.State('TLFFHood', self.enterTLFFHood, self.exitTLFFHood, ['quietZone']),
        ], 'start', 'start')
        self.fsm.enterInitialState()
        self.parentFSM = parentFSM
        self.parentFSM.getStateNamed('playGame').addChild(self.fsm)
        self.hoodDoneEvent = 'hoodDone'
        self.hood = None
        self.quietZoneDoneEvent = uniqueName('quietZoneDone')
        self.quietZoneStateData = None

    def enter(self, hoodId, zoneId, avId):
        if hoodId == ToontownGlobals.Tutorial:
            loaderName = 'townLoader'
            whereName = 'toonInterior'
        elif hoodId == ToontownGlobals.MyEstate:
            self.getEstateZoneAndGoHome(avId, zoneId)
            return
        elif hoodId == ToontownGlobals.PartyHood:
            self.getPartyZoneAndGoToParty(avId, zoneId)
            return
        else:
            loaderName = ZoneUtil.getLoaderName(zoneId)
            whereName = ZoneUtil.getToonWhereName(zoneId)
        self.fsm.request('quietZone', [{'loader': loaderName,
          'where': whereName,
          'how': 'teleportIn',
          'hoodId': hoodId,
          'zoneId': zoneId,
          'avId': avId}])

    def exit(self):
        if base.placeBeforeObjects and self.quietZoneStateData:
            self.quietZoneStateData.exit()
            self.quietZoneStateData.unload()
            self.quietZoneStateData = None
        self.ignore(self.quietZoneDoneEvent)

    def load(self):
        pass

    def loadDnaStoreTutorial(self):
        self.dnaStore = DNAStorage()
        loader.loadDNAFile(self.dnaStore, 'phase_3.5/dna/ttrm_d_strg_tutorial.dna')
        loader.loadDNAFile(self.dnaStore, 'phase_3.5/dna/ttrm_d_strg_interior.dna')

    def loadDnaStore(self):
        if not hasattr(self, 'dnaStore'):
            self.dnaStore = DNAStorage()
            loader.loadDNAFile(self.dnaStore, 'phase_4/dna/ttrm_d_strg.dna')
            if loader.loadingScreen.getActiveHoliday() == ToontownGlobals.HolidayHalloween:
                loader.loadDNAFile(self.dnaStore, 'phase_4/dna/ttrm_d_strg_halloween.dna')
            #elif loader.loadingScreen.getActiveHoliday() == ToontownGlobals.HolidayWinter:
            #    loader.loadDNAFile(self.dnaStore, 'phase_4/dna/ttrm_d_strg_winter.dna')
            #elif loader.loadingScreen.getActiveHoliday() == ToontownGlobals.HolidayAprilFools:
            #    loader.loadDNAFile(self.dnaStore, 'phase_4/dna/ttrm_d_strg_aprilfools.dna')
            self.dnaStore.storeFont('humanist', ToontownGlobals.getInterfaceFont())
            self.dnaStore.storeFont('mickey', ToontownGlobals.getSignFont())
            self.dnaStore.storeFont('suit', ToontownGlobals.getSuitFont())
            loader.loadDNAFile(self.dnaStore, 'phase_3.5/dna/ttrm_d_strg_interior.dna')

    def unloadDnaStore(self):
        if hasattr(self, 'dnaStore'):
            self.dnaStore.resetNodes()
            self.dnaStore.resetTextures()
            del self.dnaStore
            ModelPool.garbageCollect()
            TexturePool.garbageCollect()

    def unload(self):
        self.unloadDnaStore()
        if self.hood:
            self.notify.info('Aggressively cleaning up hood: %s' % self.hood)
            self.hood.exit()
            self.hood.unload()
            self.hood = None

    def enterStart(self):
        pass

    def exitStart(self):
        pass

    def handleHoodDone(self):
        doneStatus = self.hood.getDoneStatus()
        if doneStatus['where'] == 'party':
            self.getPartyZoneAndGoToParty(doneStatus['avId'], doneStatus['zoneId'])
            return
        how = doneStatus['how']
        if how in ['tunnelIn', 'teleportIn', 'doorIn', 'elevatorIn', 'skipTunnelIn', 'portalIn', 'placeIn']:
            self.fsm.request('quietZone', [doneStatus])
        else:
            self.notify.error('Exited hood with unexpected mode %s' % how)

    def _destroyHood(self):
        self.ignore(self.hoodDoneEvent)
        self.hood.exit()
        self.hood.unload()
        self.hood = None
        base.cr.cache.flush()

    def enterQuietZone(self, requestStatus):
        self.acceptOnce(self.quietZoneDoneEvent, self.handleQuietZoneDone)
        self.quietZoneStateData = QuietZoneState.QuietZoneState(self.quietZoneDoneEvent)
        self._quietZoneLeftEvent = self.quietZoneStateData.getQuietZoneLeftEvent()
        if base.placeBeforeObjects:
            self.acceptOnce(self._quietZoneLeftEvent, self.handleLeftQuietZone)
        self._enterWaitForSetZoneResponseMsg = self.quietZoneStateData.getEnterWaitForSetZoneResponseMsg()
        self.acceptOnce(self._enterWaitForSetZoneResponseMsg, self.handleWaitForSetZoneResponse)
        self.quietZoneStateData.load()
        self.quietZoneStateData.enter(requestStatus)

    def exitQuietZone(self):
        self.ignore(self._quietZoneLeftEvent)
        self.ignore(self._enterWaitForSetZoneResponseMsg)
        if not base.placeBeforeObjects:
            self.ignore(self.quietZoneDoneEvent)
            self.quietZoneStateData.exit()
            self.quietZoneStateData.unload()
            self.quietZoneStateData = None

    def handleWaitForSetZoneResponse(self, requestStatus):
        hoodId = requestStatus['hoodId']
        loaderName = requestStatus['loader']
        canonicalHoodId = ZoneUtil.getCanonicalZoneId(hoodId)
        if canonicalHoodId in list(ToontownGlobals.hoodNameMap.keys()):
            toHoodPhrase = ToontownGlobals.hoodNameMap[canonicalHoodId][0]
            hoodName = ToontownGlobals.hoodNameMap[canonicalHoodId][-1]
        else:
            names = TTLocalizer.GlobalStreetNames.get(ZoneUtil.getHoodId(canonicalHoodId), ('to', 'on', 'null'))
            toHoodPhrase = names[0]
            hoodName = names[-1]
        zoneId = requestStatus['zoneId']
        avId = requestStatus.get('avId', -1)
        ownerId = requestStatus.get('ownerId', avId)
        if base.config.GetBool('want-qa-regression', 0):
            self.notify.info('QA-REGRESSION: NEIGHBORHOODS: Visit %s' % hoodName)
        count = ToontownGlobals.hoodCountMap.get(ZoneUtil.getHoodId(canonicalHoodId), 5)

        if loaderName == 'safeZoneLoader':
            count += ToontownGlobals.safeZoneCountMap[ZoneUtil.getHoodId(canonicalHoodId)]
        elif loaderName == 'townLoader':
            count += ToontownGlobals.townCountMap[ZoneUtil.getHoodId(canonicalHoodId)]
        if not loader.inBulkBlock:
            if hoodId == ToontownGlobals.MyEstate:
                if avId == -1:
                    loader.beginBulkLoad('hood', TTLocalizer.HeadingToYourEstate, count, 1, TTLocalizer.TIP_ESTATE, zoneId = 'estate')
                else:
                    owner = base.cr.identifyAvatar(ownerId)
                    if owner == None:
                        friend = base.cr.identifyAvatar(avId)
                        if friend != None:
                            avName = friend.getName()
                            loader.beginBulkLoad('hood', TTLocalizer.HeadingToFriend % avName, count, 1, TTLocalizer.TIP_ESTATE, zoneId = 'estate')
                        else:
                            self.notify.warning("we can't perform this teleport")
                            return
                    else:
                        avName = owner.getName()
                        loader.beginBulkLoad('hood', TTLocalizer.HeadingToEstate % avName, count, 1, TTLocalizer.TIP_ESTATE, zoneId = 'estate')
            elif ZoneUtil.isCogHQZone(zoneId):
                loader.beginBulkLoad('hood', TTLocalizer.HeadingToHood % {'to': toHoodPhrase, 'hood': hoodName}, count, 1, TTLocalizer.TIP_COGHQ, zoneId)
            elif ZoneUtil.isGoofySpeedwayZone(zoneId):
                loader.beginBulkLoad('hood', TTLocalizer.HeadingToHood % {'to': toHoodPhrase, 'hood': hoodName}, count, 1, TTLocalizer.TIP_KARTING, zoneId)
            elif requestStatus.get('buildLot', 0):
                if ownerId == base.localAvatar.doId:
                    loader.beginBulkLoad('hood', TTLocalizer.HeadingToYourLot, count, 1, TTLocalizer.TIP_LOT, zoneId = 'buildLot')
                else:
                    owner = base.cr.identifyAvatar(ownerId)
                    if owner:
                        avName = owner.getName()
                    else:
                        avName = 'Toon'
                    loader.beginBulkLoad('hood', TTLocalizer.HeadingToLot % avName, count, 1, TTLocalizer.TIP_LOT, zoneId = 'buildLot')
            else:
                loader.beginBulkLoad('hood', TTLocalizer.HeadingToHood % {'to': toHoodPhrase, 'hood': hoodName}, count, 1, TTLocalizer.TIP_GENERAL, zoneId)
        if hoodId == ToontownGlobals.Tutorial:
            self.loadDnaStoreTutorial()
        else:
            self.loadDnaStore()
        hoodClass = self.getHoodClassByNumber(ZoneUtil.getHoodId(canonicalHoodId))
        self.hood = hoodClass(self.fsm, self.hoodDoneEvent, self.dnaStore, hoodId)
        self.hood.load()
        self.hood.loadLoader(requestStatus)
        if not base.placeBeforeObjects:
            loader.endBulkLoad('hood')

    def handleLeftQuietZone(self):
        status = self.quietZoneStateData.getRequestStatus()
        hoodId = ZoneUtil.getCanonicalZoneId(status['hoodId'])
        hoodState = self.getHoodStateByNumber(ZoneUtil.getHoodId(hoodId))
        self.fsm.request(hoodState, [status])

    def handleQuietZoneDone(self):
        if base.placeBeforeObjects:
            self.quietZoneStateData.exit()
            self.quietZoneStateData.unload()
            self.quietZoneStateData = None
            loader.endBulkLoad('hood')
        else:
            self.handleLeftQuietZone()

    def enterTTHood(self, requestStatus):
        self.accept(self.hoodDoneEvent, self.handleHoodDone)
        self.hood.enter(requestStatus)

    def exitTTHood(self):
        self._destroyHood()

    def enterDDHood(self, requestStatus):
        self.accept(self.hoodDoneEvent, self.handleHoodDone)
        self.hood.enter(requestStatus)

    def exitDDHood(self):
        self._destroyHood()

    def enterMMHood(self, requestStatus):
        self.accept(self.hoodDoneEvent, self.handleHoodDone)
        self.hood.enter(requestStatus)

    def exitMMHood(self):
        self._destroyHood()

    def enterBRHood(self, requestStatus):
        self.accept(self.hoodDoneEvent, self.handleHoodDone)
        self.hood.enter(requestStatus)

    def exitBRHood(self):
        self._destroyHood()

    def enterDGHood(self, requestStatus):
        self.accept(self.hoodDoneEvent, self.handleHoodDone)
        self.hood.enter(requestStatus)

    def exitDGHood(self):
        self._destroyHood()

    def enterDLHood(self, requestStatus):
        self.accept(self.hoodDoneEvent, self.handleHoodDone)
        self.hood.enter(requestStatus)

    def exitDLHood(self):
        self._destroyHood()

    def enterGSHood(self, requestStatus):
        self.accept(self.hoodDoneEvent, self.handleHoodDone)
        self.hood.enter(requestStatus)

    def exitGSHood(self):
        self._destroyHood()

    def enterOZHood(self, requestStatus):
        self.accept(self.hoodDoneEvent, self.handleHoodDone)
        self.hood.enter(requestStatus)

    def exitOZHood(self):
        self._destroyHood()

    def enterGZHood(self, requestStatus):
        self.accept(self.hoodDoneEvent, self.handleHoodDone)
        self.hood.enter(requestStatus)

    def exitGZHood(self):
        self._destroyHood()

    def enterSellbotHQ(self, requestStatus):
        self.accept(self.hoodDoneEvent, self.handleHoodDone)
        self.hood.enter(requestStatus)

    def exitSellbotHQ(self):
        self._destroyHood()

    def enterCashbotHQ(self, requestStatus):
        self.accept(self.hoodDoneEvent, self.handleHoodDone)
        self.hood.enter(requestStatus)

    def exitCashbotHQ(self):
        self._destroyHood()

    def enterLawbotHQ(self, requestStatus):
        self.accept(self.hoodDoneEvent, self.handleHoodDone)
        self.hood.enter(requestStatus)

    def exitLawbotHQ(self):
        self._destroyHood()

    def enterBossbotHQ(self, requestStatus):
        self.accept(self.hoodDoneEvent, self.handleHoodDone)
        self.hood.enter(requestStatus)

    def exitBossbotHQ(self):
        self._destroyHood()

    def enterTutorialHood(self, requestStatus):
        messenger.send('toonArrivedTutorial')
        self.accept(self.hoodDoneEvent, self.handleHoodDone)
        base.localAvatar.book.obscureButton(1)
        base.localAvatar.book.disableBookOpenButton()
        base.localAvatar.book.setSafeMode(1)
        base.localAvatar.laffMeter.obscure(1)
        base.localAvatar.chatMgr.setBackgroundFocus(False, True)
        requestStatus['how'] = 'tutorial'
        if base.japanDialog:
            musicVolume = base.config.GetFloat('tutorial-music-volume', 0.5)
            requestStatus['musicVolume'] = musicVolume
        self.hood.enter(requestStatus)

    def exitTutorialHood(self):
        self.unloadDnaStore()
        self._destroyHood()
        base.localAvatar.book.obscureButton(0)
        base.localAvatar.book.enableBookOpenButton()
        base.localAvatar.book.setSafeMode(0)
        base.localAvatar.laffMeter.obscure(0)

    def enterEstateHood(self, requestStatus):
        self.accept(self.hoodDoneEvent, self.handleHoodDone)
        self.hood.enter(requestStatus)

    def exitEstateHood(self):
        self._destroyHood()

    def getEstateZoneAndGoHome(self, avId, zoneId):
        self.doneStatus = {'avId': avId,
         'zoneId': zoneId,
         'hoodId': ToontownGlobals.MyEstate,
         'loader': 'safeZoneLoader',
         'how': 'teleportIn'}
        self.acceptOnce('setLocalEstateZone', self.goHome)
        if avId > 0:
            base.cr.estateMgr.getLocalEstateZone(avId)
        else:
            base.cr.estateMgr.getLocalEstateZone(base.localAvatar.getDoId())

    def goHome(self, ownerId, zoneId):
        self.notify.debug('goHome ownerId = %s' % ownerId)
        if ownerId > 0 and ownerId != base.localAvatar.doId and not base.cr.isFriend(ownerId):
            self.doneStatus['failed'] = 1
            taskMgr.remove('goHomeFailed')
            taskMgr.add(self.goHomeFailed, 'goHomeFailed')
            return
        if ownerId == 0 and zoneId == 0:
            self.doneStatus['failed'] = 1
            self.goHomeFailed(None)
            return
        if self.doneStatus['zoneId'] != zoneId:
            self.doneStatus['where'] = 'house'
        else:
            self.doneStatus['where'] = 'estate'
        self.doneStatus['ownerId'] = ownerId
        self.fsm.request('quietZone', [self.doneStatus])

    def goHomeFailed(self, task):
        self.notify.debug('goHomeFailed')
        failedToVisitAvId = self.doneStatus.get('avId')
        if failedToVisitAvId > 0:
            message = TTLocalizer.EstateTeleportFailedNotFriends % base.cr.identifyAvatar(failedToVisitAvId).getName()
        else:
            message = TTLocalizer.EstateTeleportFailed
        self.notify.debug('goHomeFailed, why =: %s' % message)
        self.ignore('setLocalEstateZone')
        zoneId = base.localAvatar.lastHood
        loaderName = ZoneUtil.getLoaderName(zoneId)
        whereName = ZoneUtil.getToonWhereName(zoneId)
        base.localAvatar.setSystemMessage(0, message)
        self.fsm.request('quietZone', [{'loader': loaderName,
          'where': whereName,
          'how': 'teleportIn',
          'hoodId': zoneId,
          'zoneId': zoneId}])
        return Task.done

    def enterPartyHood(self, requestStatus):
        self.accept(self.hoodDoneEvent, self.handleHoodDone)
        requestStatus['where'] = 'party'
        self.hood.enter(requestStatus)

    def exitPartyHood(self):
        self._destroyHood()

    def getPartyZoneAndGoToParty(self, avId, zoneId):
        self.doneStatus = {'avId': avId,
         'zoneId': zoneId,
         'hoodId': ToontownGlobals.PartyHood,
         'loader': 'safeZoneLoader',
         'how': 'teleportIn'}
        if avId < 0:
            avId = base.localAvatar.getDoId()
        base.cr.partyManager.requestPartyZone(avId, zoneId, callback=self.goToParty)

    def goToParty(self, ownerId, partyId, zoneId, retCode):
        if ownerId == 0 and partyId == 0 and zoneId == 0:
            self.goToPartyFailed(ourParty=True if retCode == 1 else False)
        else:
            self.doneStatus['where'] = 'party'
            self.doneStatus['ownerId'] = ownerId
            self.doneStatus['partyId'] = partyId
            self.doneStatus['zoneId'] = zoneId
            self.fsm.request('quietZone', [self.doneStatus])

    def goToPartyFailed(self, ourParty=False):
        self.notify.debug('goToPartyFailed')
        failedToVisitAvId = self.doneStatus.get('avId')
        self.ignore('gotLocalPartyZone')
        zoneId = base.localAvatar.lastHood
        loaderName = ZoneUtil.getLoaderName(zoneId)
        whereName = ZoneUtil.getToonWhereName(zoneId)
        if ourParty:
            base.localAvatar.setSystemMessage(0, TTLocalizer.PartyTimedOut)
        else:
            base.localAvatar.setSystemMessage(0, TTLocalizer.PartyGatePartyUnavailable)
        self.fsm.request('quietZone', [{'loader': loaderName,
          'where': whereName,
          'how': 'teleportIn',
          'hoodId': zoneId,
          'zoneId': zoneId}])
        return Task.done

    def enterSpecialHood(self, requestStatus):
        base.camLens.setNearFar(ToontownGlobals.SpecialHoodCameraNear, ToontownGlobals.SpecialHoodCameraFar)
        self.accept(self.hoodDoneEvent, self.handleHoodDone)
        self.hood.enter(requestStatus)

    def exitSpecialHood(self):
        base.camLens.setNearFar(ToontownGlobals.DefaultCameraNear, ToontownGlobals.DefaultCameraFar)
        self._destroyHood()

    def enterTTBetaHood(self, requestStatus):
        self.accept(self.hoodDoneEvent, self.handleHoodDone)
        self.hood.enter(requestStatus)

    def exitTTBetaHood(self):
        self._destroyHood()

    def enterDGBetaHood(self, requestStatus):
        self.accept(self.hoodDoneEvent, self.handleHoodDone)
        self.hood.enter(requestStatus)

    def exitDGBetaHood(self):
        self._destroyHood()

    def enterMMBetaHood(self, requestStatus):
        self.accept(self.hoodDoneEvent, self.handleHoodDone)
        self.hood.enter(requestStatus)

    def exitMMBetaHood(self):
        self._destroyHood()

    def enterDLBetaHood(self, requestStatus):
        self.accept(self.hoodDoneEvent, self.handleHoodDone)
        self.hood.enter(requestStatus)

    def exitDLBetaHood(self):
        self._destroyHood()

    def enterBRBetaHood(self, requestStatus):
        self.accept(self.hoodDoneEvent, self.handleHoodDone)
        self.hood.enter(requestStatus)

    def exitBRBetaHood(self):
        self._destroyHood()

    def enterDDBetaHood(self, requestStatus):
        self.accept(self.hoodDoneEvent, self.handleHoodDone)
        self.hood.enter(requestStatus)

    def exitDDBetaHood(self):
        self._destroyHood()

    def enterCFHood(self, requestStatus):
        base.camLens.setNearFar(ToontownGlobals.SpecialHoodCameraNear, ToontownGlobals.EpisodeCameraFar)
        self.accept(self.hoodDoneEvent, self.handleHoodDone)
        self.hood.enter(requestStatus)

    def exitCFHood(self):
        base.camLens.setNearFar(ToontownGlobals.DefaultCameraNear, ToontownGlobals.DefaultCameraFar)
        self._destroyHood()

    def enterEpisodeHood(self, requestStatus):
        messenger.send('toonArrivedEpisode')
        self.accept(self.hoodDoneEvent, self.handleHoodDone)
        base.localAvatar.book.obscureButton(1)
        base.localAvatar.book.setSafeMode(1)
        base.localAvatar.laffMeter.obscure(1)
        base.localAvatar.chatMgr.setBackgroundFocus(False, False)
        base.localAvatar.obscureClarabelleButton(1)
        requestStatus['how'] = 'episode'
        self.hood.enter(requestStatus)

    def exitEpisodeHood(self):
        self.unloadDnaStore()
        self._destroyHood()

    def enterTLFFHood(self, requestStatus):
        self.accept(self.hoodDoneEvent, self.handleHoodDone)
        self.hood.enter(requestStatus)

    def exitTLFFHood(self):
        self._destroyHood()

    def getCatalogCodes(self, category):
        numCodes = self.dnaStore.getNumCatalogCodes(category)
        codes = []
        for i in range(numCodes):
            codes.append(self.dnaStore.getCatalogCode(category, i))

        return codes

    def getNodePathList(self, catalogGroup):
        result = []
        codes = self.getCatalogCodes(catalogGroup)
        for code in codes:
            np = self.dnaStore.findNode(code)
            result.append(np)

        return result

    def getNodePathDict(self, catalogGroup):
        result = {}
        codes = self.getCatalogCodes(catalogGroup)
        for code in codes:
            np = self.dnaStore.findNode(code)
            result[code] = np

        return result

    def getHoodClassByNumber(self, hoodNumber):
        return self.Hood2ClassDict[hoodNumber]

    def getHoodStateByNumber(self, hoodNumber):
        return self.Hood2StateDict[hoodNumber]

    def setPlace(self, place):
        self.place = place
        if self.place:
            messenger.send('playGameSetPlace')

    def getPlace(self):
        return self.place

    def getPlaceId(self):
        if self.hood:
            return self.hood.hoodId
        return None
