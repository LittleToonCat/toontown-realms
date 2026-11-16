from panda3d.core import *
from direct.gui.DirectGui import *
from direct.fsm import StateData
from toontown.social import ToonProfilePanel
from toontown.social import ToontownFriendSecret
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from otp.otpbase import OTPGlobals
from otp.otpbase.PythonUtil import cmp_to_key
from toontown.toon import ToonDNA


FLPZone = 1
FLPServer = 2
FLPFriends = 3
FLPPets = 4
FLPEnemies = 5
globalSocialMenu = None


def determineAvatarName(avTuple):
    avId, flags = avTuple
    handle = base.cr.identifyFriend(avId)
    if handle:
        avName = handle.getName()
    else:
        avName = 'Toon'

    return avName


def compareAvatars(f1, f2):
    name1 = determineAvatarName(f1)
    name2 = determineAvatarName(f2)
    if name1 > name2:
        return 1
    elif name1 == name2:
        return 0
    else:
        return -1


def showSocialMenu():
    global globalSocialMenu
    if globalSocialMenu == None:
        globalSocialMenu = SocialMenu()
    globalSocialMenu.enter()


def hideSocialMenu():
    if globalSocialMenu != None:
        globalSocialMenu.exit()

def getGlobalSocialMenu():
    if globalSocialMenu is not None:
        return globalSocialMenu
    return None

def showSocialMenuTutorial():
    global globalSocialMenu
    if globalSocialMenu == None:
        globalSocialMenu = SocialMenu()
    globalSocialMenu.enter()
    globalSocialMenu.closeCommand = globalSocialMenu.close['command']
    globalSocialMenu.close['command'] = None


def hideSocialMenuTutorial():
    if globalSocialMenu != None:
        if hasattr(globalSocialMenu, 'closeCommand'):
            globalSocialMenu.close['command'] = globalSocialMenu.closeCommand
        globalSocialMenu.exit()


def isSocialMenuShown():
    if globalSocialMenu != None:
        return globalSocialMenu.isEntered
    return 0


def unloadSocialMenu():
    global globalSocialMenu
    if globalSocialMenu != None:
        globalSocialMenu.unload()
        globalSocialMenu = None


class SocialMenu(DirectFrame, StateData.StateData):

    def __init__(self):
        self.leftmostPanel = FLPZone
        self.rightmostPanel = FLPEnemies
        DirectFrame.__init__(self, relief=None)
        self.listScrollIndex = [0] * 7
        self.initialiseoptions(SocialMenu)
        StateData.StateData.__init__(self, 'friends-list-done')
        self.avatars = {}
        self.textRolloverColor = Vec4(1, 1, 0, 1)
        self.textDownColor = Vec4(0.5, 0.9, 1, 1)
        self.textDisabledColor = Vec4(0.4, 0.8, 0.4, 1)
        self.panelType = FLPServer

    def load(self):
        if self.isLoaded == 1:
            return None
        self.isLoaded = 1
        gui = loader.loadModel('phase_3.5/models/gui/friendslist_gui')
        auxGui = loader.loadModel('phase_3.5/models/gui/avatar_panel_gui')
        self.title = DirectLabel(parent=self, relief=None, text='', text_scale=TTLocalizer.FLPtitle, text_fg=(0, 0.1, 0.4, 1), pos=(0.007, 0.0, 0.2))
        background_image = gui.find('**/FriendsBox_Open')
        self['image'] = background_image
        self.scrollList = DirectScrolledList(parent=self, relief=None, incButton_image=(gui.find('**/FndsLst_ScrollUp'),
         gui.find('**/FndsLst_ScrollDN'),
         gui.find('**/FndsLst_ScrollUp_Rllvr'),
         gui.find('**/FndsLst_ScrollUp')), incButton_relief=None, incButton_pos=(0.0, 0.0, -0.316), incButton_image3_color=Vec4(0.6, 0.6, 0.6, 0.6), incButton_scale=(1.0, 1.0, -1.0), decButton_image=(gui.find('**/FndsLst_ScrollUp'),
         gui.find('**/FndsLst_ScrollDN'),
         gui.find('**/FndsLst_ScrollUp_Rllvr'),
         gui.find('**/FndsLst_ScrollUp')), decButton_relief=None, decButton_pos=(0.0, 0.0, 0.117), decButton_image3_color=Vec4(0.6, 0.6, 0.6, 0.6), itemFrame_pos=(-0.17, 0.0, 0.06), itemFrame_relief=None, numItemsVisible=8, items=[])
        clipper = PlaneNode('clipper')
        clipper.setPlane(Plane(Vec3(-1, 0, 0), Point3(0.2, 0, 0)))
        clipNP = self.scrollList.attachNewNode(clipper)
        self.scrollList.setClipPlane(clipNP)
        self.close = DirectButton(parent=self, relief=None, image=(auxGui.find('**/CloseBtn_UP'), auxGui.find('**/CloseBtn_DN'), auxGui.find('**/CloseBtn_Rllvr')), pos=(0.01, 0, -0.38), command=self.__close)
        self.left = DirectButton(parent=self, relief=None, image=(gui.find('**/Horiz_Arrow_UP'),
         gui.find('**/Horiz_Arrow_DN'),
         gui.find('**/Horiz_Arrow_Rllvr'),
         gui.find('**/Horiz_Arrow_UP')), image3_color=Vec4(0.6, 0.6, 0.6, 0.6), pos=(-0.15, 0.0, -0.38), scale=(-1.0, 1.0, 1.0), command=self.__left)
        self.right = DirectButton(parent=self, relief=None, image=(gui.find('**/Horiz_Arrow_UP'),
         gui.find('**/Horiz_Arrow_DN'),
         gui.find('**/Horiz_Arrow_Rllvr'),
         gui.find('**/Horiz_Arrow_UP')), image3_color=Vec4(0.6, 0.6, 0.6, 0.6), pos=(0.17, 0, -0.38), command=self.__right)
        self.newFriend = DirectButton(parent=self, relief=None, pos=(-0.14, 0.0, 0.14), image=(auxGui.find('**/Frnds_Btn_UP'), auxGui.find('**/Frnds_Btn_DN'), auxGui.find('**/Frnds_Btn_RLVR')), text='', text_scale=TTLocalizer.FLPnewFriend, text_fg=(1, 1, 1, 1), text_shadow = (0, 0, 0, 1), text_bg = (0, 0, 0, 0.6), text_pos=(0.1, 0.065), textMayChange=1)
        self.secrets = DirectButton(parent=self, relief=None, pos=TTLocalizer.FLPsecretsPos, image=(auxGui.find('**/ChtBx_ChtBtn_UP'), auxGui.find('**/ChtBx_ChtBtn_DN'), auxGui.find('**/ChtBx_ChtBtn_RLVR')), text=('',
         TTLocalizer.FriendsListPanelSecrets,
         TTLocalizer.FriendsListPanelSecrets,
         ''), text_scale=TTLocalizer.FLPsecrets, text_fg=(1, 1, 1, 1), text_shadow = (0, 0, 0, 1), text_bg = (0, 0, 0, 0.6), text_pos=(-0.09, 0.065), textMayChange=0, command=self.__secrets)
        gui.removeNode()
        auxGui.removeNode()

    def unload(self):
        if self.isLoaded == 0:
            return None
        self.isLoaded = 0
        self.exit()
        del self.title
        del self.scrollList
        del self.close
        del self.left
        del self.right
        del self.avatars
        DirectFrame.destroy(self)

    def makeAvatarButton(self, avatarTuple, colorChoice = None, bold = 0):
        avId, flags = avatarTuple
        toonName = None
        if avId == base.localAvatar.doId:
            toonName = TTLocalizer.SocialMenuViewProfile
        else:
            handle = base.cr.identifyFriend(avId)
            if handle:
                toonName = handle.getName()
            else:
                toonName = 'Unknown'
        fg = ToontownGlobals.ColorNoChat
        if flags & ToontownGlobals.FriendChat:
            fg = ToontownGlobals.ColorAvatar
        if colorChoice:
            fg = colorChoice
        fontChoice = ToontownGlobals.getToonFont()
        fontScale = 0.04
        bg = None
        if colorChoice and bold:
            fontScale = 0.04
            colorS = 0.7
            bg = (colorChoice[0] * colorS,
             colorChoice[1] * colorS,
             colorChoice[2] * colorS,
             0.3)
        db = DirectButton(
                relief=None,
                text=toonName.replace('\n', ' '),
                text_scale=fontScale,
                text_align=TextNode.ALeft,
                text_fg=fg,
                text_shadow=bg,
                text1_bg=self.textDownColor,
                text2_bg=self.textRolloverColor,
                text3_fg=self.textDisabledColor,
                text_font=fontChoice,
                textMayChange=0,
                command=self.__choseAvatar,
                extraArgs=[avId]
        )
        return db

    def enter(self):
        if self.isEntered == 1:
            return None
        self.isEntered = 1
        if self.isLoaded == 0:
            self.load()
        base.localAvatar.bSocialMenu['command'] = base.localAvatar.sendHideSocialMenuEvent
        self.__updateScrollList()
        self.__updateTitle()
        self.__updateArrows()
        if len(base.localAvatar.friendsList) == 1:
            friendsText = TTLocalizer.SocialMenuFriendInfoS
        else:
            friendsText = TTLocalizer.SocialMenuFriendInfoP.format(len(base.localAvatar.friendsList))
        self.newFriend['text'] = ('', friendsText, friendsText)
        self.show()
        self.accept('onlineAvatarsChanged', self.__avatarsListChanged)
        self.accept('petHandleChanged', self.__avatarsListChanged)
        self.accept('friendsListChanged', self.__friendsListChanged)
        self.accept('AvatarIgnoreChange', self.__ignoreListChanged)
        self.accept(OTPGlobals.PlayerFriendAddEvent, self.__friendsListChanged)
        self.accept(OTPGlobals.PlayerFriendUpdateEvent, self.__friendsListChanged)

    def exit(self):
        if self.isEntered == 0:
            return None
        self.isEntered = 0
        self.listScrollIndex[self.panelType] = self.scrollList.index
        self.hide()

        base.localAvatar.bSocialMenu['command'] = base.localAvatar.sendSocialMenuEvent
        self.ignore('onlineAvatarsChanged')
        self.ignore('petHandleChanged')
        self.ignore('friendsListChanged')
        self.ignore('ignoreListChanged')
        self.ignore(OTPGlobals.PlayerFriendAddEvent)
        self.ignore(OTPGlobals.PlayerFriendUpdateEvent)
        messenger.send(self.doneEvent)

    def __close(self):
        messenger.send('wakeup')
        self.exit()

    def __left(self):
        messenger.send('wakeup')
        self.listScrollIndex[self.panelType] = self.scrollList.index
        if self.panelType > self.leftmostPanel:
            self.panelType -= 1
        self.__updateScrollList()
        self.__updateTitle()
        self.__updateArrows()

    def __right(self):
        messenger.send('wakeup')
        self.listScrollIndex[self.panelType] = self.scrollList.index
        if self.panelType < self.rightmostPanel:
            self.panelType += 1
        self.__updateScrollList()
        self.__updateTitle()
        self.__updateArrows()

    def __secrets(self):
        messenger.send('wakeup')
        ToontownFriendSecret.showFriendSecret(ToontownFriendSecret.AvatarSecret)

    def __choseAvatar(self, friendId):
        messenger.send('wakeup')
        handle = base.cr.identifyFriend(friendId)
        if handle != None:
            self.notify.info("Clicked on name in friend's list. doId = %s" % handle.doId)
            messenger.send('clickedNametag', [handle])

    def __updateScrollList(self):
        onlineFriends = []
        onlineOtherPlayers = []
        offlineFriends = []
        otherAvatars = []

        if self.panelType == FLPZone:
            for objId, obj in list(base.cr.doId2do.items()):
                if objId == base.localAvatar.getDoId():
                    continue
                from toontown.toon import DistributedToon
                if isinstance(obj, DistributedToon.DistributedToon) and obj.isPlayerControlled():
                    # Ghost mode 1 is for estate decoration, we don't care about that
                    if base.cr.getAvatarVisibility(objId):
                        if base.cr.isFriend(objId):
                            onlineFriends.append((objId, 0))
                        else:
                            onlineOtherPlayers.append((objId, 0))

        if self.panelType == FLPServer:
            for avatarId in base.cr.onlineAvatars:
                if avatarId == base.localAvatar.doId:
                    continue
                if base.cr.getAvatarVisibility(avatarId):
                    if base.cr.isFriend(avatarId):
                        onlineFriends.append((avatarId, 0))
                    else:
                        onlineOtherPlayers.append((avatarId, 0))

        if self.panelType == FLPFriends:
            if base.friendMode == 0:
                for friendPair in base.localAvatar.friendsList:
                    if base.cr.getAvatarVisibility(friendPair[0]):
                        onlineFriends.append((friendPair[0], friendPair[1]))
                    else:
                        offlineFriends.append((friendPair[0], friendPair[1]))

        if self.panelType == FLPPets:
            for objId, obj in list(base.cr.doId2do.items()):
                from toontown.pets import DistributedPet
                if isinstance(obj, DistributedPet.DistributedPet):
                    otherAvatars.append((objId, 0))

        if self.panelType == FLPEnemies:
            for ignored in base.cr.avatarFriendsManager.ignoredAvatarList:
                onlineOtherPlayers.append((ignored, 0))

        if self.panelType in [FLPServer, FLPFriends]:
            if base.wantPets and base.localAvatar.hasPet():
                otherAvatars.insert(0, (base.localAvatar.getPetId(), 0))
        for friendPair in list(self.avatars.keys()):
            avatarButton = self.avatars[friendPair]
            self.scrollList.removeItem(avatarButton, refresh=0)
            avatarButton.destroy()
            del self.avatars[friendPair]

        onlineFriends.sort(key = cmp_to_key(compareAvatars))
        onlineOtherPlayers.sort(key = cmp_to_key(compareAvatars))
        offlineFriends.sort(key=cmp_to_key(compareAvatars))
        otherAvatars.sort(key=cmp_to_key(compareAvatars))

        if self.panelType in [FLPZone, FLPServer, FLPFriends]:
            friendPair = (base.localAvatar.doId, 0)
            avatarButton = self.makeAvatarButton(friendPair, ToontownGlobals.ColorAvatar, 1)
            if avatarButton:
                self.scrollList.addItem(avatarButton, refresh = 0)
                self.avatars[friendPair] = avatarButton

        for friendPair in otherAvatars:
            if friendPair not in self.avatars:
                avatarButton = self.makeAvatarButton(friendPair, ToontownGlobals.ColorNoChat, 0)
                if avatarButton:
                    self.scrollList.addItem(avatarButton, refresh=0)
                    self.avatars[friendPair] = avatarButton

        for friendPair in onlineFriends:
            if friendPair not in self.avatars:
                avatarButton = self.makeAvatarButton(friendPair, ToontownGlobals.ColorOnlineFriend, bold = 1)
                if avatarButton:
                    self.scrollList.addItem(avatarButton, refresh=0)
                    self.avatars[friendPair] = avatarButton

        for friendPair in offlineFriends:
            if friendPair not in self.avatars:
                avatarButton = self.makeAvatarButton(friendPair, ToontownGlobals.ColorOfflineFriend, 0)
                if avatarButton:
                    self.scrollList.addItem(avatarButton, refresh=0)
                    self.avatars[friendPair] = avatarButton

        for friendPair in onlineOtherPlayers:
            if friendPair not in self.avatars:
                avatarButton = self.makeAvatarButton(friendPair, ToontownGlobals.ColorSpeedChat, 0)
                if avatarButton:
                    self.scrollList.addItem(avatarButton, refresh=0)
                    self.avatars[friendPair] = avatarButton

        self.scrollList.index = self.listScrollIndex[self.panelType]
        self.scrollList.refresh()

    def __updateTitle(self):
        if self.panelType == FLPFriends:
            self.title['text'] = TTLocalizer.FriendsListPanelAllFriends
        elif self.panelType == FLPPets:
            self.title['text'] = TTLocalizer.FriendsListPanelPets
        elif self.panelType == FLPServer:
            self.title['text'] = TTLocalizer.FriendsListPanelToonsServer
        elif self.panelType == FLPZone:
            self.title['text'] = TTLocalizer.FriendsListPanelToonsZone
        else:
            self.title['text'] = TTLocalizer.FriendsListPanelIgnoredFriends
        self.title.resetFrameSize()

    def __updateArrows(self):
        if self.panelType == self.leftmostPanel:
            self.left['state'] = 'inactive'
        else:
            self.left['state'] = 'normal'
        if self.panelType == self.rightmostPanel:
            self.right['state'] = 'inactive'
        else:
            self.right['state'] = 'normal'

    def __avatarsListChanged(self):
        self.__updateScrollList()

    def __friendsListChanged(self, arg1 = None, arg2 = None):
        if self.panelType != FLPEnemies:
            self.__updateScrollList()
        if len(base.localAvatar.friendsList) == 1:
            friendsText = TTLocalizer.SocialMenuFriendInfoS
        else:
            friendsText = TTLocalizer.SocialMenuFriendInfoP.format(len(base.localAvatar.friendsList))
        self.newFriend['text'] = ('', friendsText, friendsText)

    def __ignoreListChanged(self):
        if self.panelType == FLPEnemies:
            self.__updateScrollList()
