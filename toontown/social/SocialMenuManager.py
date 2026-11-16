from panda3d.core import *
from panda3d.toontown import *
from direct.directnotify import DirectNotifyGlobal
from toontown.toon import ToonTeleportPanel
from toontown.social import ToontownFriendSecret
from toontown.pets import PetAvatarPanel
from toontown.social import AvatarHandle
from toontown.social import ToonProfilePanel
from toontown.social import SocialMenu
from toontown.suit import SuitAvatarPanel
from toontown.toon import ToonDNA
from toontown.toonbase import ToontownGlobals
from toontown.toon import Toon
from otp.otpbase import OTPGlobals

class SocialMenuManager:
    notify = DirectNotifyGlobal.directNotify.newCategory('SocialMenuManager')

    def __init__(self):
        self.avatarPanel = None
        self.profilePanel = None
        self._preserveSocialMenu = False
        self._entered = False
        self.friendsRequestQueue = []

    def load(self):
        if hasattr(base.cr.friendManager, 'setSpecificGameFunction') and base.cr.friendManager:
            base.cr.friendManager.setGameSpecificFunction(self.processQueuedRequests)

    def unload(self):
        if hasattr(base.cr.friendManager, 'setSpecificGameFunction') and base.cr.friendManager:
            base.cr.friendManager.setGameSpecificFunction(None)
        self.exitSMM()
        if self.avatarPanel:
            del self.avatarPanel
        if self.profilePanel:
            del self.profilePanel
        ToonTeleportPanel.unloadTeleportPanel()

    def enterSMM(self):
        self.notify.debug('SocialMenuManager: enterSMM()')
        if self._preserveSocialMenu:
            self._preserveSocialMenu = 0
            return
        self._entered = True
        self.accept('openSocialMenu', self.__openSocialMenu)
        self.accept('hideSocialMenu', self.__hideSocialMenu)
        self.accept('clickedNametag', self.__handleClickedNametag)
        base.localAvatar.setFriendsListButtonActive(1)
        NametagGlobals.setMasterNametagsActive(1)
        self.accept('gotoAvatar', self.__handleGotoAvatar)
        self.accept(OTPGlobals.PlayerFriendInvitationEvent, self.__handlePlayerFriendInvitation)
        if base.cr.friendManager:
            base.cr.friendManager.setAvailable(1)

    def exitSMM(self):
        self.notify.debug('SocialMenuManager: exitSMM()')
        if self._preserveSocialMenu:
            return
        if not self._entered:
            return
        self._entered = False
        self.ignore('openSocialMenu')
        self.ignore('hideSocialMenu')
        self.ignore('clickedNametag')
        self.ignore('clickedNametagPlayer')
        base.localAvatar.setFriendsListButtonActive(0)
        NametagGlobals.setMasterNametagsActive(0)
        if self.avatarPanel:
            self.avatarPanel.cleanup()
            self.avatarPanel = None
        if self.profilePanel:
            self.profilePanel.cleanup()
            self.profilePanel = None
        self.ignore('gotoAvatar')
        SocialMenu.hideSocialMenu()
        ToontownFriendSecret.hideFriendSecret()
        if base.cr.friendManager:
            base.cr.friendManager.setAvailable(0)
        ToonTeleportPanel.hideTeleportPanel()

    def __openSocialMenu(self):
        SocialMenu.showSocialMenu()

    def __hideSocialMenu(self):
        SocialMenu.hideSocialMenu()

    def __handleClickedNametag(self, avatar, playerId = None):
        self.notify.debug('__handleClickedNametag. doId = %s' % avatar.doId)
        if avatar.isPet():
            self.avatarPanel = PetAvatarPanel.PetAvatarPanel(avatar)
        elif isinstance(avatar, Toon.Toon) or isinstance(avatar, AvatarHandle.AvatarHandle):
            if hasattr(self, 'profilePanel'):
                if self.profilePanel:
                    if not hasattr(self.profilePanel, 'getAvId') or self.profilePanel.getAvId() == avatar.doId:
                        if not self.profilePanel.isHidden():
                            return
                    self.profilePanel.cleanup()
            self.profilePanel = ToonProfilePanel.ToonProfilePanel(avatar)
        else:
            self.avatarPanel = SuitAvatarPanel.SuitAvatarPanel(avatar)

    def __handleGotoAvatar(self, avId, avName, avDisableName):
        ToonTeleportPanel.showTeleportPanel(avId, avName, avDisableName)

    def __handlePlayerFriendInvitation(self, avId, avName, inviterDna = None, context = None):
        self.notify.debug('incoming switchboard friend event')
        self.friendsRequestQueue.append((avId,
         avName,
         inviterDna,
         context))
        if base.cr.friendManager.getAvailable():
            self.processQueuedRequests()

    def processQueuedRequests(self):
        if len(self.friendsRequestQueue):
            request = self.friendsRequestQueue.pop(0)
            self.__processFriendRequest(request[0], request[1], request[2], request[3])

    def __processFriendRequest(self, avId, avName, inviterDna = None, context = None):
        self.notify.debug('__handleAvatarFriendInvitation')
        askerToon = base.cr.doId2do.get(avId)
        if askerToon:
            self.notify.debug('got toon')
            dna = askerToon.getStyle()
            if not base.cr.avatarFriendsManager.checkIgnored(avId):
                FriendInvitee.FriendInvitee(avId, avName, dna, context)
        else:
            self.notify.debug('no toon')

    def preserveSocialMenu(self):
        self.notify.debug('Preserving Social Menu')
        self._preserveSocialMenu = True
