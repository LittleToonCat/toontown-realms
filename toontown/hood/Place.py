from direct.showbase.MessengerGlobal import messenger
from direct.showbase.ShowBaseGlobal import globalClock
from direct.task.TaskManagerGlobal import taskMgr
from panda3d.core import *
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import StateData
from panda3d.toontown import NametagGlobals

from otp.otpbase.PythonUtil import PriorityCallbacks, SubframeCall, Functor
from toontown.safezone import PublicWalk
from toontown.launcher import DownloadForceAcknowledge
from . import ZoneUtil
from toontown.social import SocialMenuManager
from toontown.toonbase import ToontownGlobals, ClientSettings, HotkeySettings
from toontown.toon.Toon import teleportDebug
from toontown.estate import HouseGlobals
from toontown.toonbase import TTLocalizer
from otp.otpbase import OTPLocalizer, OTPGlobals
from otp.avatar import Emote
from otp.avatar.Avatar import teleportNotify
from direct.task import Task
from . import QuietZoneState
from toontown.sandbox.Prop import Prop
from ..toonbase.ToonBaseGlobal import *


class Place(StateData.StateData, SocialMenuManager.SocialMenuManager):
    notify = DirectNotifyGlobal.directNotify.newCategory('Place')

    def __init__(self, loader, doneEvent):
        StateData.StateData.__init__(self, doneEvent)
        SocialMenuManager.SocialMenuManager.__init__(self)
        self.loader = loader
        self.dfaDoneEvent = 'dfaDoneEvent'
        self.zoneId = None
        self._tiToken = None
        self._leftQuietZoneLocalCallbacks = PriorityCallbacks()
        self._leftQuietZoneSubframeCall = None
        self._setZoneCompleteLocalCallbacks = PriorityCallbacks()
        self._setZoneCompleteSubframeCall = None
        self.teleportAttempts = 0
        self.servers = None

    def load(self):
        StateData.StateData.load(self)
        SocialMenuManager.SocialMenuManager.load(self)
        self.walkDoneEvent = 'walkDone'
        self.walkStateData = PublicWalk.PublicWalk(self.fsm, self.walkDoneEvent)
        self.walkStateData.load()
        self._tempFSM = self.fsm

    def unload(self):
        StateData.StateData.unload(self)
        SocialMenuManager.SocialMenuManager.unload(self)
        self.notify.info('Unloading Place (%s). Fsm in %s' % (self.zoneId, self._tempFSM.getCurrentState().getName()))
        if self._leftQuietZoneSubframeCall:
            self._leftQuietZoneSubframeCall.cleanup()
            self._leftQuietZoneSubframeCall = None
        if self._setZoneCompleteSubframeCall:
            self._setZoneCompleteSubframeCall.cleanup()
            self._setZoneCompleteSubframeCall = None
        self._leftQuietZoneLocalCallbacks = None
        self._setZoneCompleteLocalCallbacks = None
        del self._tempFSM
        taskMgr.remove('goHomeFailed')
        del self.walkDoneEvent
        self.walkStateData.unload()
        del self.walkStateData
        del self.loader

    def _getQZState(self):
        if hasattr(base, 'cr') and hasattr(base.cr, 'playGame'):
            if hasattr(base.cr.playGame, 'quietZoneStateData') and base.cr.playGame.quietZoneStateData:
                return base.cr.playGame.quietZoneStateData
        return None

    def addLeftQuietZoneCallback(self, callback, priority = None):
        qzsd = self._getQZState()
        if qzsd:
            return qzsd.addLeftQuietZoneCallback(callback, priority)
        else:
            token = self._leftQuietZoneLocalCallbacks.add(callback, priority=priority)
            if not self._leftQuietZoneSubframeCall:
                self._leftQuietZoneSubframeCall = SubframeCall(self._doLeftQuietZoneCallbacks, taskMgr.getCurrentTask().getPriority() - 1)
            return token

    def removeLeftQuietZoneCallback(self, token):
        if token is not None:
            if token in self._leftQuietZoneLocalCallbacks:
                self._leftQuietZoneLocalCallbacks.remove(token)
            qzsd = self._getQZState()
            if qzsd:
                qzsd.removeLeftQuietZoneCallback(token)
        return

    def _doLeftQuietZoneCallbacks(self):
        self._leftQuietZoneLocalCallbacks()
        self._leftQuietZoneLocalCallbacks.clear()
        self._leftQuietZoneSubframeCall = None
        return

    def addSetZoneCompleteCallback(self, callback, priority = None):
        qzsd = self._getQZState()
        if qzsd:
            return qzsd.addSetZoneCompleteCallback(callback, priority)
        else:
            token = self._setZoneCompleteLocalCallbacks.add(callback, priority=priority)
            if not self._setZoneCompleteSubframeCall:
                self._setZoneCompleteSubframeCall = SubframeCall(self._doSetZoneCompleteLocalCallbacks, taskMgr.getCurrentTask().getPriority() - 1)
            return token

    def removeSetZoneCompleteCallback(self, token):
        if token is not None:
            if any(token == x[1] for x in self._setZoneCompleteLocalCallbacks._callbacks):
                self._setZoneCompleteLocalCallbacks.remove(token)
            qzsd = self._getQZState()
            if qzsd:
                qzsd.removeSetZoneCompleteCallback(token)
        return

    def _doSetZoneCompleteLocalCallbacks(self):
        self._setZoneCompleteSubframeCall = None
        localCallbacks = self._setZoneCompleteLocalCallbacks
        self._setZoneCompleteLocalCallbacks()
        localCallbacks.clear()
        return

    def setState(self, state):
        if hasattr(self, 'fsm'):
            curState = self.fsm.getName()
            if state == 'pet' or curState == 'pet':
                self.preserveSocialMenu()
            self.fsm.request(state)

    def getState(self):
        if hasattr(self, 'fsm'):
            curState = self.fsm.getCurrentState().getName()
            return curState

    def getZoneId(self):
        return self.zoneId

    def getTaskZoneId(self):
        return self.getZoneId()

    def isPeriodTimerEffective(self):
        return 1

    def handleTeleportQuery(self, receiverId):
        base.localAvatar.d_reflectTeleportResponse(receiverId, 1, base.cr.playGame.getPlaceId(), self.getZoneId())

    def enablePeriodTimer(self):
        if self.isPeriodTimerEffective():
            if base.cr.periodTimerExpired:
                taskMgr.doMethodLater(5, self.redoPeriodTimer, 'redoPeriodTimer')
            self.accept('periodTimerExpired', self.periodTimerExpired)

    def disablePeriodTimer(self):
        taskMgr.remove('redoPeriodTimer')
        self.ignore('periodTimerExpired')

    def redoPeriodTimer(self, task):
        messenger.send('periodTimerExpired')
        return Task.done

    def periodTimerExpired(self):
        self.fsm.request('final')
        if base.localAvatar.book.isEntered:
            base.localAvatar.book.exit()
            base.localAvatar.b_setAnimState('CloseBook', 1, callback=self.__handlePeriodTimerBookClose)
        else:
            base.localAvatar.b_setAnimState('TeleportOut', 1, self.__handlePeriodTimerExitTeleport)

    def exitPeriodTimerExpired(self):
        pass

    def __handlePeriodTimerBookClose(self):
        base.localAvatar.b_setAnimState('TeleportOut', 1, self.__handlePeriodTimerExitTeleport)

    def __handlePeriodTimerExitTeleport(self):
        base.cr.loginFSM.request('periodTimeout')

    def detectedPhoneCollision(self):
        self.fsm.request('phone')

    def detectedFishingCollision(self):
        self.fsm.request('fishing')

    def detectedClassicFishingCollision(self):
        self.fsm.request('classicfishing')

    def enterStart(self):
        pass

    def exitStart(self):
        pass

    def enterFinal(self):
        pass

    def exitFinal(self):
        pass

    def enterWalk(self, teleportIn = 0):
        if base.localAvatar.getLocked() or not hasattr(self, 'walkDoneEvent'):
            return
        self.enterSMM()
        self.walkStateData.enter()
        if teleportIn == 0:
            self.walkStateData.fsm.request('walking')
        self.acceptOnce(self.walkDoneEvent, self.handleWalkDone)
        self.accept('teleportQuery', self.handleTeleportQuery)
        base.localAvatar.setTeleportAvailable(1)
        base.localAvatar.questPage.acceptOnscreenHooks()
        base.localAvatar.invPage.acceptOnscreenHooks()
        base.localAvatar.questMap.acceptOnscreenHooks()
        base.localAvatar.acceptOnscreenHooks()
        self.walkStateData.fsm.request('walking')
        self.enablePeriodTimer()

    def exitWalk(self):
        if hasattr(base.cr, 'propGenerator') and base.cr.propGenerator:
            base.cr.propGenerator.closeNewPropWindow(wantTransition = False)
            if Prop.selectedProp is not None:
                Prop.selectedProp.deselect()
        self.exitSMM()
        self.disablePeriodTimer()
        messenger.send('wakeup')
        self.walkStateData.exit()
        self.ignore(self.walkDoneEvent)
        base.localAvatar.setTeleportAvailable(0)
        self.ignore('teleportQuery')
        if base.cr.playGame.hood != None:
            base.cr.playGame.hood.hideTitleText()
        base.localAvatar.questPage.hideQuestsOnscreen()
        base.localAvatar.questPage.ignoreOnscreenHooks()
        base.localAvatar.invPage.ignoreOnscreenHooks()
        base.localAvatar.invPage.hideInventoryOnscreen()
        base.localAvatar.ignoreOnscreenHooks()
        base.localAvatar.questMap.hide()
        base.localAvatar.questMap.ignoreOnscreenHooks()
        messenger.send('toonExitWalk')

    def handleWalkDone(self, doneStatus):
        mode = doneStatus['mode']
        if mode == 'StickerBook':
            self.last = self.fsm.getCurrentState().getName()
            self.fsm.request('stickerBook')
        elif mode == 'Options':
            self.last = self.fsm.getCurrentState().getName()
            self.fsm.request('stickerBook', [base.localAvatar.optionsPage])
        elif mode == 'Sit':
            self.last = self.fsm.getCurrentState().getName()
            self.fsm.request('sit')
        else:
            Place.notify.error('Invalid mode: %s' % mode)

    def enterSit(self):
        self.enterSMM()
        base.localAvatar.laffMeter.start()
        self.accept('teleportQuery', self.handleTeleportQuery)
        base.localAvatar.setTeleportAvailable(1)
        base.localAvatar.b_setAnimState('SitStart', 1)
        self.accept(HotkeySettings.MoveForward.getPressed(), self.fsm.request, extraArgs=['walk'])

    def exitSit(self):
        self.exitSMM()
        base.localAvatar.laffMeter.stop()
        base.localAvatar.setTeleportAvailable(0)
        self.ignore('teleportQuery')
        self.ignore(HotkeySettings.MoveForward.getPressed())

    def enterDrive(self):
        self.enterSMM()
        base.localAvatar.laffMeter.start()
        self.accept('teleportQuery', self.handleTeleportQuery)
        base.localAvatar.setTeleportAvailable(1)
        base.localAvatar.b_setAnimState('SitStart', 1)

    def exitDrive(self):
        self.exitSMM()
        base.localAvatar.laffMeter.stop()
        base.localAvatar.setTeleportAvailable(0)
        self.ignore('teleportQuery')

    def enterPush(self):
        self.enterSMM()
        base.localAvatar.laffMeter.start()
        self.accept('teleportQuery', self.handleTeleportQuery)
        base.localAvatar.setTeleportAvailable(1)
        base.localAvatar.attachCamera()
        base.localAvatar.activateCamera()
        base.localAvatar.startPosHprBroadcast(period = ClientSettings.PositionSendRate.get())
        base.localAvatar.b_setAnimState('Push', 1)

    def exitPush(self):
        self.exitSMM()
        base.localAvatar.laffMeter.stop()
        base.localAvatar.setTeleportAvailable(0)
        base.localAvatar.deactivateCamera()
        base.localAvatar.detachCamera()
        base.localAvatar.stopPosHprBroadcast()
        self.ignore('teleportQuery')

    def enterStickerBook(self, page = None):
        self.enterSMM()
        base.localAvatar.laffMeter.start()
        target = base.cr.doFind('DistributedTarget')
        if target:
            target.hideGui()
        self.accept('teleportQuery', self.handleTeleportQuery)
        base.localAvatar.setTeleportAvailable(1)
        if page:
            base.localAvatar.book.setPage(page)
        base.localAvatar.b_setAnimState('OpenBook', 1, self.enterStickerBookGUI)
        base.localAvatar.obscureMoveFurnitureButton(1)

    def enterStickerBookGUI(self):
        base.localAvatar.collisionsOn()
        base.localAvatar.book.showButton()
        base.localAvatar.book.enter()
        base.localAvatar.setGuiConflict(1)
        base.localAvatar.startSleepWatch(self.__handleFallingAsleep)
        self.accept('bookDone', self.__handleBook)
        base.localAvatar.b_setAnimState('ReadBook', 1)
        self.enablePeriodTimer()

    def __handleFallingAsleep(self, task=None):
        base.localAvatar.book.exit()
        base.localAvatar.b_setAnimState('CloseBook', 1, callback=self.__handleFallingAsleepBookClose)
        if task:
            return task.done

    def __handleFallingAsleepBookClose(self):
        if hasattr(self, 'fsm'):
            self.fsm.request('walk')
        base.localAvatar.forceGotoSleep()

    def exitStickerBook(self):
        base.localAvatar.stopSleepWatch()
        self.disablePeriodTimer()
        self.exitSMM()
        base.localAvatar.laffMeter.stop()
        base.localAvatar.setGuiConflict(0)
        base.localAvatar.book.exit()
        base.localAvatar.book.hideButton()
        base.localAvatar.collisionsOff()
        self.ignore('bookDone')
        base.localAvatar.setTeleportAvailable(0)
        self.ignore('teleportQuery')
        base.localAvatar.obscureMoveFurnitureButton(-1)
        target = base.cr.doFind('DistributedTarget')
        if target:
            target.showGui()

    def __handleBook(self, servers=None):
        base.localAvatar.stopSleepWatch()
        base.localAvatar.book.exit()
        bookStatus = base.localAvatar.book.getDoneStatus()
        if bookStatus['mode'] == 'close':
            base.localAvatar.b_setAnimState('CloseBook', 1, callback=self.handleBookClose)
        elif bookStatus['mode'] == 'teleport':
            zoneId = bookStatus['hood']
            base.localAvatar.collisionsOff()
            base.localAvatar.b_setAnimState('CloseBook', 1, callback=self.handleBookCloseTeleport, extraArgs=[zoneId, zoneId])
        elif bookStatus['mode'] == 'exit':
            self.exitTo = bookStatus.get('exitTo')
            if servers:
                self.servers = servers
            base.localAvatar.collisionsOff()
            base.localAvatar.b_setAnimState('CloseBook', 1, callback=self.__handleBookCloseExit)
        elif bookStatus['mode'] == 'gohome':
            zoneId = bookStatus['hood']
            base.localAvatar.collisionsOff()
            base.localAvatar.b_setAnimState('CloseBook', 1, callback=self.goHomeNow, extraArgs=[zoneId])
        elif bookStatus['mode'] == 'startparty':
            firstStart = bookStatus['firstStart']
            hostId = bookStatus['hostId']
            base.localAvatar.collisionsOff()
            base.localAvatar.b_setAnimState('CloseBook', 1, callback=self.startPartyNow, extraArgs=[firstStart, hostId])

    def handleBookCloseTeleport(self, hoodId, zoneId):
        if localAvatar.hasActiveBoardingGroup():
            rejectText = TTLocalizer.BoardingCannotLeaveZone
            localAvatar.elevatorNotifier.showMe(rejectText)
            return
        self.requestLeave({'loader': ZoneUtil.getBranchLoaderName(zoneId),
                           'where': ZoneUtil.getToonWhereName(zoneId),
                           'how': 'teleportIn',
                           'hoodId': hoodId,
                           'zoneId': zoneId,
                           'avId': -1})

    def __handleBookCloseExit(self):
        base.localAvatar.b_setAnimState('TeleportOut', 1, self.__handleBookExitTeleport, [0])

    def __handleBookExitTeleport(self, requestStatus):
        if base.cr.timeManager:
            base.cr.timeManager.setDisconnectReason(ToontownGlobals.DisconnectBookExit)
        base.transitions.fadeScreen(1.0)
        if self.servers:
            if isinstance(self.servers, list):
                base.cr.loginFSM.request('loginOff')
                base.cr.loginFSM.request('connect', [self.servers])
            elif isinstance(self.servers, int):
                base.cr.loginFSM.request('loginOff')
                base.startServer()

            self.servers = None
        base.cr.gameFSM.request(self.exitTo)

    def goHomeNow(self, curZoneId):
        if localAvatar.hasActiveBoardingGroup():
            rejectText = TTLocalizer.BoardingCannotLeaveZone
            localAvatar.elevatorNotifier.showMe(rejectText)
            return
        hoodId = ToontownGlobals.MyEstate
        self.requestLeave({'loader': 'safeZoneLoader',
         'where': 'estate',
         'how': 'teleportIn',
         'hoodId': hoodId,
         'zoneId': -1,
         'avId': -1})

    def startPartyNow(self, firstStart, hostId):
        if localAvatar.hasActiveBoardingGroup():
            rejectText = TTLocalizer.BoardingCannotLeaveZone
            localAvatar.elevatorNotifier.showMe(rejectText)
            return
        base.localAvatar.creatingNewPartyWithMagicWord = False
        base.localAvatar.aboutToPlanParty = False
        hoodId = ToontownGlobals.PartyHood
        if firstStart:
            base.cr.playGame.getPlace().requestLeave({'loader': 'safeZoneLoader',
             'where': 'party',
             'how': 'teleportIn',
             'hoodId': hoodId,
             'zoneId': 0,
             'avId': -1})
        else:
            if hostId is None:
                hostId = base.localAvatar.doId
            base.cr.partyManager.sendAvatarToParty(hostId)

    def handleBookClose(self):
        if hasattr(self, 'fsm'):
            self.fsm.request('walk')
        if hasattr(self, 'toonSubmerged') and self.toonSubmerged == 1:
            if hasattr(self, 'walkStateData'):
                self.walkStateData.fsm.request('swimming', [self.loader.swimSound])

    def requestLeave(self, requestStatus):
        teleportDebug(requestStatus, 'requestLeave(%s)' % (requestStatus,))
        if hasattr(self, 'fsm'):
            self.doRequestLeave(requestStatus)

    def doRequestLeave(self, requestStatus):
        teleportDebug(requestStatus, 'requestLeave(%s)' % (requestStatus,))
        self.fsm.request('DFA', [requestStatus])

    def enterDFA(self, requestStatus):
        base.localAvatar.cleanupGreenEffectIntervals()
        base.localAvatar.cleanupDropPropIntervals()
        teleportDebug(requestStatus, 'enterDFA(%s)' % (requestStatus,))
        self.acceptOnce(self.dfaDoneEvent, self.enterDFACallback, [requestStatus])
        self.dfa = DownloadForceAcknowledge.DownloadForceAcknowledge(self.dfaDoneEvent)
        self.dfa.enter(base.cr.hoodMgr.getPhaseFromHood(requestStatus['hoodId']))

    def exitDFA(self):
        self.ignore(self.dfaDoneEvent)

    def handleEnterTunnel(self, requestStatus, collEntry):
        if localAvatar.hasActiveBoardingGroup():
            rejectText = TTLocalizer.BoardingCannotLeaveZone
            localAvatar.elevatorNotifier.showMe(rejectText)
            dummyNP = NodePath('dummyNP')
            dummyNP.reparentTo(render)
            tunnelOrigin = requestStatus['tunnelOrigin']
            dummyNP.setPos(localAvatar.getPos())
            dummyNP.setH(tunnelOrigin.getH())
            dummyNP.setPos(dummyNP, 0, 4, 0)
            localAvatar.setPos(dummyNP.getPos())
            dummyNP.removeNode()
            del dummyNP
            return
        self.requestLeave(requestStatus)

    def enterDFACallback(self, requestStatus, doneStatus):
        teleportDebug(requestStatus, 'enterDFACallback%s' % ((requestStatus, doneStatus),))
        self.dfa.exit()
        del self.dfa
        if doneStatus['mode'] == 'complete':
            if requestStatus.get('tutorial', 0):
                out = {'teleportIn': 'tunnelOut'}
            else:
                out = {'teleportIn': 'teleportOut',
                       'tunnelIn': 'tunnelOut',
                       'doorIn': 'doorOut',
                       'episode': 'episode',
                       'placeIn': 'teleportOut'}
            teleportDebug(requestStatus, 'requesting %s, requestStatus=%s' % (out[requestStatus['how']], requestStatus))
            self.fsm.request(out[requestStatus['how']], [requestStatus])
        elif doneStatus['mode'] == 'incomplete':
            self.fsm.request('DFAReject')
        else:
            Place.notify.error('Unknown done status for DownloadForceAcknowledge: ' + repr(doneStatus))

    def enterDFAReject(self):
        self.fsm.request('walk')

    def exitDFAReject(self):
        pass

    def enterDoorIn(self, requestStatus):
        base.localAvatar.setTransitioning(True)
        NametagGlobals.setMasterArrowsOn(0)
        door = base.cr.doId2do.get(requestStatus['doorDoId'])
        door.readyToExit()
        base.localAvatar.obscureMoveFurnitureButton(1)
        base.localAvatar.startQuestMap()

    def exitDoorIn(self):
        base.localAvatar.setTransitioning(False)
        NametagGlobals.setMasterArrowsOn(1)
        base.localAvatar.obscureMoveFurnitureButton(-1)

    def enterDoorOut(self):
        base.localAvatar.setTransitioning(True)
        base.localAvatar.obscureMoveFurnitureButton(1)

    def exitDoorOut(self):
        base.localAvatar.setTransitioning(False)
        base.localAvatar.obscureMoveFurnitureButton(-1)
        base.localAvatar.stopQuestMap()

    def handleDoorDoneEvent(self, requestStatus):
        self.doneStatus = requestStatus
        messenger.send(self.doneEvent)

    def handleDoorTrigger(self):
        self.fsm.request('doorOut')

    def enterTunnelIn(self, requestStatus):
        base.localAvatar.setTransitioning(True)
        self.notify.debug('enterTunnelIn(requestStatus=' + str(requestStatus) + ')')
        tunnelOrigin = base.render.find(requestStatus['tunnelName'])
        self.accept('tunnelInMovieDone', self.__tunnelInMovieDone)
        base.localAvatar.reconsiderCheesyEffect()
        base.localAvatar.tunnelIn(tunnelOrigin)
        base.localAvatar.startQuestMap()

    def __tunnelInMovieDone(self):
        self.ignore('tunnelInMovieDone')
        self.fsm.request('walk')

    def exitTunnelIn(self):
        base.localAvatar.setTransitioning(False)

    def enterSkipTunnelIn(self, requestStatus):
        tunnelOrigin = base.render.find(requestStatus['tunnelName'])
        base.localAvatar.reconsiderCheesyEffect()
        if base.localAvatar.doId in base.cr.karts:
            kart = base.cr.karts[base.localAvatar.doId]
            kart.setPos(tunnelOrigin, 0, 6, 0)
            kart.setHpr(tunnelOrigin, 0, 0, 0)
            kart.stopCarImmediately()
            kart.disableForSeconds(0.25)
        self.fsm.request('stopped')

    def exitSkipTunnelIn(self):
        pass

    def enterTunnelOut(self, requestStatus):
        base.localAvatar.setTransitioning(True)
        hoodId = requestStatus['hoodId']
        zoneId = requestStatus['zoneId']
        how = requestStatus['how']
        tunnelOrigin = requestStatus['tunnelOrigin']
        fromZoneId = ZoneUtil.getCanonicalZoneId(self.getZoneId())
        tunnelName = requestStatus.get('tunnelName')
        if tunnelName == None:
            tunnelName = base.cr.hoodMgr.makeLinkTunnelName(self.loader.hood.id, fromZoneId)
        self.doneStatus = {'loader': ZoneUtil.getLoaderName(zoneId),
         'where': ZoneUtil.getToonWhereName(zoneId),
         'how': how,
         'hoodId': hoodId,
         'zoneId': zoneId,
         'tunnelName': tunnelName}
        self.accept('tunnelOutMovieDone', self.__tunnelOutMovieDone)
        base.localAvatar.tunnelOut(tunnelOrigin)
        base.localAvatar.stopQuestMap()

    def tunnelOutSkip(self, fromZoneId, zoneId):
        tunnelName = base.cr.hoodMgr.makeLinkTunnelName(self.loader.hood.id, fromZoneId)
        self.doneStatus = {'loader': ZoneUtil.getLoaderName(zoneId),
         'where': ZoneUtil.getToonWhereName(zoneId),
         'how': 'skipTunnelIn',
         'hoodId': ZoneUtil.getHoodId(zoneId),
         'zoneId': zoneId,
         'tunnelName': tunnelName}
        messenger.send(self.doneEvent)

    def __tunnelOutMovieDone(self):
        self.ignore('tunnelOutMovieDone')
        messenger.send(self.doneEvent)

    def exitTunnelOut(self):
        base.localAvatar.setTransitioning(False)

    def enterTeleportIn(self, requestStatus):
        base.localAvatar.setTransitioning(True)
        try:
            hoods = list(ToontownGlobals.hood2Coords.keys())
            coordinates = list(ToontownGlobals.hood2Coords.values())
            for hood in hoods:
                index = hoods.index(hood)
                for shorthand in hood:
                    if shorthand == base.queuedHood:
                        coords = coordinates[index]
            base.queuedHood = None
            base.localAvatar.setPosHpr(render, *coords)
        except:
            pass
        self._tiToken = self.addSetZoneCompleteCallback(Functor(self._placeTeleportInPostZoneComplete, requestStatus), 100)

    def _placeTeleportInPostZoneComplete(self, requestStatus):
        if not self.teleportAttempts:
            teleportDebug(requestStatus, '_placeTeleportInPostZoneComplete(%s)' % (requestStatus,))
        NametagGlobals.setMasterArrowsOn(0)
        base.localAvatar.laffMeter.start()
        base.localAvatar.startQuestMap()
        base.localAvatar.reconsiderCheesyEffect()
        base.localAvatar.obscureMoveFurnitureButton(1)
        avId = requestStatus.get('avId', -1)
        if avId != -1:
            if avId in base.cr.doId2do:
                teleportDebug(requestStatus, 'teleport to avatar')
                avatar = base.cr.doId2do[avId]
                avatar.forceToTruePosition()
                base.localAvatar.gotoNode(avatar)
                base.localAvatar.b_sayTeleportGreeting(avId)
            else:
                avatar = base.cr.identifyAvatar(avId)
                if avatar != None:
                    self.teleportAttempts += 1
                    if self.teleportAttempts < 10:
                        teleportDebug(requestStatus, 'avatar not here, attempting again in next frame. %d/10 attempts' % self.teleportAttempts)
                        taskMgr.doMethodLater(0, self._placeTeleportInPostZoneComplete, 'place_TeleportInPostZoneComplete', extraArgs=[requestStatus])
                        return
                    teleportDebug(requestStatus, 'avatar not here, giving up')
                    base.localAvatar.setSystemMessage(avId, OTPLocalizer.WhisperTargetLeftVisit % (avatar.getName(),))
                    base.localAvatar.d_reflectTeleportGiveup(avId)
        base.transitions.irisIn()
        self.nextState = requestStatus.get('nextState', 'walk')
        base.localAvatar.attachCamera()
        base.localAvatar.activateCamera()
        base.localAvatar.startPosHprBroadcast(period = ClientSettings.PositionSendRate.get())
        globalClock.tick()
        base.localAvatar.b_setAnimState('TeleportIn', 1, callback=self.teleportInDone)
        base.localAvatar.d_broadcastPositionNow()
        base.localAvatar.b_setParent(ToontownGlobals.SPRender)
        if self.teleportAttempts:
            self.teleportAttempts = 0
        return

    def teleportInDone(self):
        if hasattr(self, 'fsm'):
            teleportNotify.debug('teleportInDone: %s' % self.nextState)
            self.fsm.request(self.nextState, [1])

    def exitTeleportIn(self):
        base.localAvatar.setTransitioning(False)
        self.removeSetZoneCompleteCallback(self._tiToken)
        self._tiToken = None
        NametagGlobals.setMasterArrowsOn(1)
        base.localAvatar.laffMeter.stop()
        base.localAvatar.obscureMoveFurnitureButton(-1)
        base.localAvatar.deactivateCamera()
        base.localAvatar.detachCamera()
        base.localAvatar.stopPosHprBroadcast()
        return

    def enterTeleportOut(self, requestStatus, callback):
        base.localAvatar.setTransitioning(True)
        base.localAvatar.laffMeter.start()
        base.localAvatar.b_setAnimState('TeleportOut', 1, callback, [requestStatus])
        base.localAvatar.obscureMoveFurnitureButton(1)

    def exitTeleportOut(self):
        base.localAvatar.setTransitioning(False)
        base.localAvatar.laffMeter.stop()
        base.localAvatar.stopQuestMap()
        base.localAvatar.obscureMoveFurnitureButton(-1)

    def enterPlaceIn(self, requestStatus, callback):
        pass

    def exitPlaceIn(self):
        pass

    def requestTeleport(self, hoodId, zoneId, avId):
        if avId > 0:
            teleportNotify.debug('requestTeleport%s' % ((hoodId,
              zoneId,
              avId),))
        if localAvatar.hasActiveBoardingGroup():
            if avId > 0:
                teleportNotify.debug('requestTeleport: has active boarding group')
            rejectText = TTLocalizer.BoardingCannotLeaveZone
            localAvatar.elevatorNotifier.showMe(rejectText)
            return
        loaderId = ZoneUtil.getBranchLoaderName(zoneId)
        whereId = ZoneUtil.getToonWhereName(zoneId)
        if hoodId == ToontownGlobals.MyEstate:
            loaderId = 'safeZoneLoader'
            whereId = 'estate'
        # HACK
        if hoodId == ToontownGlobals.ToontownSkies and ZoneUtil.isDynamicZone(zoneId):
            whereId = 'toonInterior'
        if hoodId == ToontownGlobals.PartyHood:
            loaderId = 'safeZoneLoader'
            whereId = 'party'
        self.requestLeave({'loader': loaderId,
         'where': whereId,
         'how': 'teleportIn',
         'hoodId': hoodId,
         'zoneId': zoneId,
         'avId': avId})

    def hookTeleportInDone(self):
        teleportNotify.debug('Hooked TeleportInDone')
        if hasattr(self, 'fsm'):
            teleportNotify.debug('teleportInDone: %s' % self.nextState)
            self.fsm.request(self.nextState, [1])

    def doTeleport(self, zone):
        try:
            base.queuedHood = zone
            zoneId = None
            zoneIds = list(ToontownGlobals.hood2Id.keys())
            hoods = list(ToontownGlobals.hood2Id.values())
            for hood in hoods:
                index = hoods.index(hood)
                for shorthand in hood:
                    if zone == shorthand:
                        zoneId = zoneIds[index]
        except:
            return

        if not zoneId:
            # hack but i dont feel like fixing rn
            if 30100 <= zone <= 30500:
                zoneId = zone
            else:
                return

        hoodId = ZoneUtil.getHoodId(zoneId)

        # If a furniture manager is active, release us if applicable.
        # Otherwise, we're ghosted, and we don't want that!
        messenger.send('releaseDirector')

        Place.teleportInDone = lambda self: self.hookTeleportInDone()
        if zoneId == ToontownGlobals.MyEstate:
            self.goHomeNow(zoneId)
        else:
            self.handleBookCloseTeleport(hoodId, zoneId)

    def enterDied(self, requestStatus, callback = None):
        base.localAvatar.setTransitioning(True)
        if callback == None:
            callback = self.__diedDone
        base.localAvatar.laffMeter.start()
        base.camera.wrtReparentTo(render)
        base.localAvatar.b_setAnimState('Died', 1, callback, [requestStatus])
        base.localAvatar.obscureMoveFurnitureButton(1)
        return

    def __diedDone(self, requestStatus):
        self.doneStatus = requestStatus
        messenger.send(self.doneEvent)

    def exitDied(self):
        base.localAvatar.setTransitioning(False)
        base.localAvatar.laffMeter.stop()
        base.localAvatar.obscureMoveFurnitureButton(-1)

    def getEstateZoneAndGoHome(self, requestStatus):
        self.doneStatus = requestStatus
        avId = requestStatus['avId']
        self.acceptOnce('setLocalEstateZone', self.goHome)
        if avId > 0:
            base.cr.estateMgr.getLocalEstateZone(avId)
        else:
            base.cr.estateMgr.getLocalEstateZone(base.localAvatar.getDoId())
        if HouseGlobals.WANT_TELEPORT_TIMEOUT:
            taskMgr.doMethodLater(HouseGlobals.TELEPORT_TIMEOUT, self.goHomeFailed, 'goHomeFailed')

    def goHome(self, ownerId, zoneId):
        self.notify.debug('goHome ownerId = %s' % ownerId)
        taskMgr.remove('goHomeFailed')
        if ownerId > 0 and ownerId != base.localAvatar.doId and not base.cr.isFriend(ownerId):
            self.doneStatus['failed'] = 1
            self.goHomeFailed(None)
            return
        if ownerId == 0 and zoneId == 0:
            self.doneStatus['failed'] = 1
            self.goHomeFailed(None)
            return
        if self.doneStatus['zoneId'] == -1:
            self.doneStatus['zoneId'] = zoneId
        elif self.doneStatus['zoneId'] != zoneId:
            self.doneStatus['where'] = 'house'
        self.doneStatus['ownerId'] = ownerId
        messenger.send(self.doneEvent)
        messenger.send('localToonLeft')

    def goHomeFailed(self, task):
        self.notify.debug('goHomeFailed')
        self.notifyUserGoHomeFailed()
        self.ignore('setLocalEstateZone')
        self.doneStatus['hood'] = base.localAvatar.lastHood
        self.doneStatus['zone'] = base.localAvatar.lastHood
        self.fsm.request('teleportIn', [self.doneStatus])
        return Task.done

    def notifyUserGoHomeFailed(self):
        self.notify.debug('notifyUserGoHomeFailed')
        failedToVisitAvId = self.doneStatus.get('avId', -1)
        avName = None
        if failedToVisitAvId != -1:
            avatar = base.cr.identifyAvatar(failedToVisitAvId)
            if avatar:
                avName = avatar.getName()
        if avName:
            message = TTLocalizer.EstateTeleportFailedNotFriends % avName
        else:
            message = TTLocalizer.EstateTeleportFailed
        base.localAvatar.setSystemMessage(0, message)
        return

    def enterQuest(self, npcToon):
        base.localAvatar.b_setAnimState('neutral', 1)
        self.accept('teleportQuery', self.handleTeleportQuery)
        base.localAvatar.setTeleportAvailable(1)
        base.localAvatar.laffMeter.start()
        base.localAvatar.obscureMoveFurnitureButton(1)

    def exitQuest(self):
        base.localAvatar.setTeleportAvailable(0)
        self.ignore('teleportQuery')
        base.localAvatar.laffMeter.stop()
        base.localAvatar.obscureMoveFurnitureButton(-1)

    def enterPurchase(self):
        base.localAvatar.b_setAnimState('neutral', 1)
        self.accept('teleportQuery', self.handleTeleportQuery)
        base.localAvatar.setTeleportAvailable(1)
        base.localAvatar.laffMeter.start()
        base.localAvatar.obscureMoveFurnitureButton(1)

    def exitPurchase(self):
        base.localAvatar.setTeleportAvailable(0)
        self.ignore('teleportQuery')
        base.localAvatar.laffMeter.stop()
        base.localAvatar.obscureMoveFurnitureButton(-1)

    def enterFishing(self):
        base.localAvatar.b_setAnimState('neutral', 1)
        self.accept('teleportQuery', self.handleTeleportQuery)
        base.localAvatar.setTeleportAvailable(1)
        base.localAvatar.laffMeter.start()
        base.localAvatar.startQuestMap()

    def exitFishing(self):
        base.localAvatar.setTeleportAvailable(0)
        self.ignore('teleportQuery')
        base.localAvatar.laffMeter.stop()
        base.localAvatar.startQuestMap()

    def enterClassicFishing(self):
        self.enterFishing()

    def exitClassicFishing(self):
        self.exitFishing()

    def enterBanking(self):
        base.localAvatar.b_setAnimState('neutral', 1)
        self.accept('teleportQuery', self.handleTeleportQuery)
        base.localAvatar.setTeleportAvailable(1)
        base.localAvatar.laffMeter.start()
        base.localAvatar.obscureMoveFurnitureButton(1)
        base.localAvatar.startSleepWatch(self.__handleFallingAsleepBanking)
        self.enablePeriodTimer()

    def __handleFallingAsleepBanking(self, arg):
        if hasattr(self, 'fsm'):
            messenger.send('bankAsleep')
            self.fsm.request('walk')
        base.localAvatar.forceGotoSleep()

    def exitBanking(self):
        base.localAvatar.setTeleportAvailable(0)
        self.ignore('teleportQuery')
        base.localAvatar.laffMeter.stop()
        base.localAvatar.obscureMoveFurnitureButton(-1)
        base.localAvatar.stopSleepWatch()
        self.disablePeriodTimer()

    def enterPhone(self):
        base.localAvatar.b_setAnimState('neutral', 1)
        self.accept('teleportQuery', self.handleTeleportQuery)
        base.localAvatar.setTeleportAvailable(1)
        base.localAvatar.laffMeter.start()
        base.localAvatar.obscureMoveFurnitureButton(1)
        base.localAvatar.startSleepWatch(self.__handleFallingAsleepPhone)
        self.enablePeriodTimer()

    def __handleFallingAsleepPhone(self, arg):
        if hasattr(self, 'fsm'):
            self.fsm.request('walk')
        messenger.send('phoneAsleep')
        base.localAvatar.forceGotoSleep()

    def exitPhone(self):
        base.localAvatar.setTeleportAvailable(0)
        self.ignore('teleportQuery')
        base.localAvatar.laffMeter.stop()
        base.localAvatar.obscureMoveFurnitureButton(-1)
        base.localAvatar.stopSleepWatch()
        self.disablePeriodTimer()

    def enterStopped(self):
        base.localAvatar.b_setAnimState('neutral', 1)
        Emote.globalEmote.disableBody(base.localAvatar, 'enterStopped')
        self.accept('teleportQuery', self.handleTeleportQuery)
        if base.localAvatar.getTransformationsIndex(ToontownGlobals.TransformationCog):
            base.localAvatar.setTeleportAvailable(0)
        else:
            base.localAvatar.setTeleportAvailable(1)
        base.localAvatar.laffMeter.start()
        base.localAvatar.obscureMoveFurnitureButton(1)
        base.localAvatar.startSleepWatch(self.__handleFallingAsleepStopped)
        self.enablePeriodTimer()

    def __handleFallingAsleepStopped(self, arg):
        if hasattr(self, 'fsm'):
            self.fsm.request('walk')
        base.localAvatar.forceGotoSleep()
        messenger.send('stoppedAsleep')

    def exitStopped(self):
        Emote.globalEmote.releaseBody(base.localAvatar, 'exitStopped')
        base.localAvatar.setTeleportAvailable(0)
        self.ignore('teleportQuery')
        base.localAvatar.laffMeter.stop()
        base.localAvatar.obscureMoveFurnitureButton(-1)
        base.localAvatar.stopSleepWatch()
        self.disablePeriodTimer()
        messenger.send('exitingStoppedState')

    def enterPet(self):
        base.localAvatar.b_setAnimState('neutral', 1)
        Emote.globalEmote.disableBody(base.localAvatar, 'enterPet')
        self.accept('teleportQuery', self.handleTeleportQuery)
        base.localAvatar.setTeleportAvailable(1)
        base.localAvatar.setTeleportAllowed(0)
        base.localAvatar.laffMeter.start()
        self.enterSMM()

    def exitPet(self):
        base.localAvatar.setTeleportAvailable(0)
        base.localAvatar.setTeleportAllowed(1)
        Emote.globalEmote.releaseBody(base.localAvatar, 'exitPet')
        self.ignore('teleportQuery')
        base.localAvatar.laffMeter.stop()
        self.exitSMM()

    def enterQuietZone(self, requestStatus):
        self.quietZoneDoneEvent = uniqueName('quietZoneDone')
        self.acceptOnce(self.quietZoneDoneEvent, self.handleQuietZoneDone)
        self.quietZoneStateData = QuietZoneState.QuietZoneState(self.quietZoneDoneEvent)
        self.quietZoneStateData.load()
        self.quietZoneStateData.enter(requestStatus)

    def exitQuietZone(self):
        self.ignore(self.quietZoneDoneEvent)
        del self.quietZoneDoneEvent
        self.quietZoneStateData.exit()
        self.quietZoneStateData.unload()
        self.quietZoneStateData = None
        return

    def handleQuietZoneDone(self):
        how = base.cr.handlerArgs['how']
        self.fsm.request(how, [base.cr.handlerArgs])

    def enterPortalOut(self, requestStatus, callback):
        base.localAvatar.setTransitioning(True)
        base.localAvatar.laffMeter.start()
        base.localAvatar.b_setAnimState('PortalOut', 1, callback, [requestStatus])
        base.localAvatar.obscureMoveFurnitureButton(1)

    def exitPortalOut(self):
        base.localAvatar.setTransitioning(False)
        base.localAvatar.laffMeter.stop()
        base.localAvatar.stopQuestMap()
        base.localAvatar.obscureMoveFurnitureButton(-1)

    def enterPortalIn(self, requestStatus):
        base.localAvatar.setTransitioning(True)
        self._tiToken = self.addSetZoneCompleteCallback(Functor(self._placePortalInPostZoneComplete, requestStatus), 100)

    def _placePortalInPostZoneComplete(self, requestStatus):
        teleportDebug(requestStatus, '_placePortalInPostZoneComplete(%s)' % (requestStatus,))
        NametagGlobals.setMasterArrowsOn(0)
        base.localAvatar.laffMeter.start()
        base.localAvatar.startQuestMap()
        base.localAvatar.reconsiderCheesyEffect()
        base.localAvatar.obscureMoveFurnitureButton(1)
        base.transitions.irisIn()
        self.nextState = requestStatus.get('nextState', 'walk')
        base.localAvatar.attachCamera()
        base.localAvatar.activateCamera()
        base.localAvatar.startPosHprBroadcast(period = ClientSettings.PositionSendRate.get())
        globalClock.tick()
        base.localAvatar.b_setAnimState('PortalIn', 1, callback=self.portalInDone)
        base.localAvatar.d_broadcastPositionNow()
        base.localAvatar.b_setParent(ToontownGlobals.SPRender)
        return

    def portalInDone(self):
        if hasattr(self, 'fsm'):
            teleportNotify.debug('portalInDone: %s' % self.nextState)
            self.fsm.request(self.nextState, [1])

    def exitPortalIn(self):
        base.localAvatar.setTransitioning(False)
        self.removeSetZoneCompleteCallback(self._tiToken)
        self._tiToken = None
        NametagGlobals.setMasterArrowsOn(1)
        base.localAvatar.laffMeter.stop()
        base.localAvatar.obscureMoveFurnitureButton(-1)
        base.localAvatar.deactivateCamera()
        base.localAvatar.detachCamera()
        base.localAvatar.stopPosHprBroadcast()
        return

    def handleEnterPortal(self, hoodId, zoneId):
        if localAvatar.hasActiveBoardingGroup():
            if avId > 0:
                teleportNotify.debug('handleEnterPortal: has active boarding group')
            rejectText = TTLocalizer.BoardingCannotLeaveZone
            localAvatar.elevatorNotifier.showMe(rejectText)
            return
        self.requestLeave({'loader': ZoneUtil.getBranchLoaderName(zoneId),
         'where': ZoneUtil.getToonWhereName(zoneId),
         'how': 'portalIn',
         'hoodId': hoodId,
         'zoneId': zoneId,
         'avId': -1})

    def enterEpisode(self, requestStatus):
        self.fsm.request('walk')
        base.localAvatar.b_setParent(ToontownGlobals.SPRender)
        globalClock.tick()
        base.transitions.irisIn()

    def exitEpisode(self):
        pass