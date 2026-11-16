from panda3d.core import *
from direct.gui.DirectGui import *
from toontown.toonbase import ToontownGlobals
from direct.showbase import DirectObject
from direct.fsm import ClassicFSM, State
from direct.directnotify import DirectNotifyGlobal
from otp.avatar.Avatar import teleportNotify
from toontown.toonbase import TTLocalizer
from toontown.hood import ZoneUtil
globalTeleport = None

def showTeleportPanel(avId, avName, avDisableName):
    global globalTeleport
    if globalTeleport != None:
        globalTeleport.cleanup()
        globalTeleport = None
    globalTeleport = ToonTeleportPanel(avId, avName, avDisableName)


def hideTeleportPanel():
    global globalTeleport
    if globalTeleport != None:
        globalTeleport.cleanup()
        globalTeleport = None


def unloadTeleportPanel():
    global globalTeleport
    if globalTeleport != None:
        globalTeleport.cleanup()
        globalTeleport = None


class ToonTeleportPanel(DirectFrame):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToonTeleportPanel')

    def __init__(self, avId, avName, avDisableName):
        DirectFrame.__init__(self, pos=(0.3, 0.1, 0.65), image_color=ToontownGlobals.GlobalDialogColor, image_scale=(1.0, 1.0, 0.6), text='', text_wordwrap=13.5, text_scale=0.06, text_pos=(0.0, 0.18))
        messenger.send('releaseDirector')
        self['image'] = DGG.getDefaultDialogGeom()
        self.avId = avId
        self.avName = avName
        self.avDisableName = avDisableName
        self.fsm = ClassicFSM.ClassicFSM('ToonTeleportPanel', [
            State.State('off',
                self.enterOff,
                self.exitOff),
            State.State('begin',
                self.enterBegin,
                self.exitBegin),
            State.State('checkAvailability',
                self.enterCheckAvailability,
                self.exitCheckAvailability),
            State.State('notAvailable',
                self.enterNotAvailable,
                self.exitNotAvailable),
            State.State('ignored',
                self.enterIgnored,
                self.exitIgnored),
            State.State('friendsOnly',
                self.enterFriendsOnly,
                self.exitFriendsOnly),
            State.State('notAcceptingRequests',
                self.enterNotAcceptingRequests,
                self.exitNotAcceptingRequests),
            State.State('notOnline',
                self.enterNotOnline,
                self.exitNotOnline),
            State.State('wentAway',
                self.enterWentAway,
                self.exitWentAway),
            State.State('self',
                self.enterSelf,
                self.exitSelf),
            State.State('unknownHood',
                self.enterUnknownHood,
                self.exitUnknownHood),
            State.State('unavailableHood',
                self.enterUnavailableHood,
                self.exitUnavailableHood),
            State.State('teleport',
                self.enterTeleport,
                self.exitTeleport)],
            'off', 'off')
        buttons = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
        self.bOk = DirectButton(self, image=(buttons.find('**/ChtBx_OKBtn_UP'), buttons.find('**/ChtBx_OKBtn_DN'), buttons.find('**/ChtBx_OKBtn_Rllvr')), relief=None, text=TTLocalizer.TeleportPanelOK, text_scale=0.05, text_pos=(0.0, -0.1), pos=(0.0, 0.0, -0.1), command=self.__handleOk)
        self.bOk.hide()
        self.bCancel = DirectButton(self, image=(buttons.find('**/CloseBtn_UP'), buttons.find('**/CloseBtn_DN'), buttons.find('**/CloseBtn_Rllvr')), relief=None, text=TTLocalizer.TeleportPanelCancel, text_scale=0.05, text_pos=(0.0, -0.1), pos=(0.0, 0.0, -0.1), command=self.__handleCancel)
        self.bCancel.hide()
        self.bYes = DirectButton(self, image=(buttons.find('**/ChtBx_OKBtn_UP'), buttons.find('**/ChtBx_OKBtn_DN'), buttons.find('**/ChtBx_OKBtn_Rllvr')), relief=None, text=TTLocalizer.TeleportPanelYes, text_scale=0.05, text_pos=(0.0, -0.1), pos=(-0.15, 0.0, -0.15), command=self.__handleYes)
        self.bYes.hide()
        self.bNo = DirectButton(self, image=(buttons.find('**/CloseBtn_UP'), buttons.find('**/CloseBtn_DN'), buttons.find('**/CloseBtn_Rllvr')), relief=None, text=TTLocalizer.TeleportPanelNo, text_scale=0.05, text_pos=(0.0, -0.1), pos=(0.15, 0.0, -0.15), command=self.__handleNo)
        self.bNo.hide()
        buttons.removeNode()
        self.accept(self.avDisableName, self.__handleDisableAvatar)
        self.show()
        self.fsm.enterInitialState()
        self.fsm.request('begin')

    def cleanup(self):
        self.fsm.request('off')
        del self.fsm
        self.ignore(self.avDisableName)
        self.destroy()

    def enterOff(self):
        pass

    def exitOff(self):
        pass

    def enterBegin(self):
        myId = base.localAvatar.doId
        if self.avId == myId:
            self.fsm.request('self')
        elif base.cr.getAvatarVisibility(self.avId, forceVisibility = self.avId in base.cr.doId2do and base.cr.doId2do[self.avId].ghostMode != 2):
            self.fsm.request('checkAvailability')
        else:
            self.fsm.request('notOnline')

    def exitBegin(self):
        pass

    def enterCheckAvailability(self):
        base.localAvatar.d_reflectTeleportQuery(self.avId)
        self['text'] = TTLocalizer.TeleportPanelCheckAvailability % self.avName
        self.accept('teleportResponse', self.__teleportResponse)
        self.bCancel.show()

    def exitCheckAvailability(self):
        self.ignore('teleportResponse')
        self.bCancel.hide()

    def enterNotAvailable(self):
        self['text'] = TTLocalizer.TeleportPanelNotAvailable % self.avName
        self.bOk.show()

    def exitNotAvailable(self):
        self.bOk.hide()

    def enterIgnored(self):
        self['text'] = TTLocalizer.TeleportPanelNotAvailable % self.avName
        self.bOk.show()

    def exitIgnored(self):
        self.bOk.hide()

    def enterFriendsOnly(self):
        self['text'] = TTLocalizer.TeleportPanelFriendsOnly.format(self.avName)
        self.bOk.show()

    def exitFriendsOnly(self):
        self.bOk.hide()

    def enterNotAcceptingRequests(self):
        self['text'] = TTLocalizer.TeleportPanelNotAcceptingRequests.format(self.avName)
        self.bOk.show()

    def exitNotAcceptingRequests(self):
        self.bOk.hide()

    def enterNotOnline(self):
        self['text'] = TTLocalizer.TeleportPanelNotOnline % self.avName
        self.bOk.show()

    def exitNotOnline(self):
        self.bOk.hide()

    def enterWentAway(self):
        self['text'] = TTLocalizer.TeleportPanelWentAway % self.avName
        self.bOk.show()

    def exitWentAway(self):
        self.bOk.hide()

    def enterUnknownHood(self, hoodId):
        self['text'] = TTLocalizer.TeleportPanelUnknownHood % base.cr.hoodMgr.getFullnameFromId(hoodId)
        self.bOk.show()

    def exitUnknownHood(self):
        self.bOk.hide()

    def enterUnavailableHood(self, hoodId):
        self['text'] = TTLocalizer.TeleportPanelUnavailableHood % base.cr.hoodMgr.getFullnameFromId(hoodId)
        self.bOk.show()

    def exitUnavailableHood(self):
        self.bOk.hide()

    def enterSelf(self):
        self['text'] = TTLocalizer.TeleportPanelDenySelf
        self.bOk.show()

    def exitSelf(self):
        self.bOk.hide()

    def enterTeleport(self, hoodId, zoneId):
        teleportNotify.debug(f'enterTeleport({hoodId}, {zoneId})')
        hoodsVisited = base.localAvatar.hoodsVisited
        canonicalHoodId = ZoneUtil.getCanonicalZoneId(hoodId)
        if hoodId == ToontownGlobals.MyEstate:
            teleportNotify.debug('enterTeleport: estate')
            place = base.cr.playGame.getPlace()
            place.requestTeleport(hoodId, zoneId, self.avId)
            unloadTeleportPanel()
        elif canonicalHoodId not in hoodsVisited + ToontownGlobals.HoodsAlwaysVisited:
            teleportNotify.debug('enterTeleport: unknownHood')
            self.fsm.request('unknownHood', [hoodId])
        elif canonicalHoodId not in base.cr.hoodMgr.getAvailableZones():
            print(f'hoodId {hoodId} not ready')
            self.fsm.request('unavailableHood', [hoodId])
        else:
            teleportNotify.debug('enterTeleport: requesting teleport')
            place = base.cr.playGame.getPlace()
            place.requestTeleport(hoodId, zoneId, self.avId)
            unloadTeleportPanel()

    def exitTeleport(self):
        pass

    def __handleOk(self):
        unloadTeleportPanel()

    def __handleCancel(self):
        unloadTeleportPanel()

    def __handleYes(self):
        self.fsm.request('teleport', [self.hoodId, self.zoneId])

    def __handleNo(self):
        unloadTeleportPanel()

    def __teleportResponse(self, avId, available, hoodId, zoneId):
        teleportNotify.debug('__teleportResponse%s' % ((avId,
          available,
          hoodId,
          zoneId),))
        if avId != self.avId:
            return
        if available == 0:
            teleportNotify.debug('__teleportResponse: not available')
            self.fsm.request('notAvailable')
        elif available == 2:
            teleportNotify.debug('__teleportResponse: ignored')
            self.fsm.request('ignored')
        elif available == 3:
            teleportNotify.debug('__teleportResponse: accepting friends only')
            self.fsm.request('friendsOnly')
        elif available == 4:
            teleportNotify.debug('__teleportResponse: not accepting requests from anyone')
            self.fsm.request('notAcceptingRequests')
        else:
            teleportNotify.debug('__teleportResponse: teleport')
            self.fsm.request('teleport', [hoodId, zoneId])

    def __handleDisableAvatar(self):
        self.fsm.request('wentAway')
