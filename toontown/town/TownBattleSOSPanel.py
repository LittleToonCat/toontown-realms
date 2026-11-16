from panda3d.core import *
from toontown.toonbase.ToontownGlobals import *
from direct.gui.DirectGui import *
from direct.showbase import DirectObject
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import StateData
from toontown.toonbase import TTLocalizer
from toontown.toon import NPCToons
from toontown.toon import NPCFriendPanel
from toontown.toonbase import ToontownBattleGlobals

class TownBattleSOSPanel(DirectFrame, StateData.StateData):
    notify = DirectNotifyGlobal.directNotify.newCategory('TownBattleSOSPanel')

    def __init__(self, doneEvent):
        DirectFrame.__init__(self, relief=None)
        self.initialiseoptions(TownBattleSOSPanel)
        StateData.StateData.__init__(self, doneEvent)
        self.avatars = {}
        self.NPCFriends = {}
        self.textRolloverColor = Vec4(1, 1, 0, 1)
        self.textDownColor = Vec4(0.5, 0.9, 1, 1)
        self.textDisabledColor = Vec4(0.4, 0.8, 0.4, 1)
        self.bldg = 0
        self.chosenNPCToons = []

    def load(self):
        if self.isLoaded == 1:
            return None
        self.isLoaded = 1
        bgd = loader.loadModel('phase_3.5/models/gui/frame')
        gui = loader.loadModel('phase_3.5/models/gui/frame4names')
        scrollGui = loader.loadModel('phase_3.5/models/gui/friendslist_gui')
        backGui = loader.loadModel('phase_3.5/models/gui/battle_gui')
        self['image'] = bgd
        self['image_pos'] = (0.0, 0.1, -0.08)
        self.setScale(0.3)
        self.title = DirectLabel(parent=self, relief=None, text=TTLocalizer.TownBattleSOSNoFriends, text_scale=0.4, text_fg=(1, 1, 1, 1), text_shadow=(0, 0, 0, 1), pos=(0.0, 0.0, 1.5))
        self.NPCFriendPanel = NPCFriendPanel.NPCFriendPanel(parent=self, doneEvent=self.doneEvent)
        self.NPCFriendPanel.setPos(-0.75, 0, -0.15)
        self.NPCFriendPanel.setScale(0.325)
        self.NPCFriendsLabel = DirectLabel(parent=self, relief=None, text=TTLocalizer.TownBattleSOSNPCFriends, text_scale=0.3, text_fg=(1, 1, 1, 1), text_shadow=(0, 0, 0, 1), pos=(-0.75, 0.0, -2.0))
        self.scrollList = DirectScrolledList(parent=self, relief=None, image=gui.find('**/frame4names'), image_scale=(0.11, 1, 0.1), text=TTLocalizer.FriendsListPanelOnlineFriends, text_scale=0.04, text_pos=(-0.02, 0.275), text_fg=(0, 0, 0, 1), incButton_image=(scrollGui.find('**/FndsLst_ScrollUp'),
         scrollGui.find('**/FndsLst_ScrollDN'),
         scrollGui.find('**/FndsLst_ScrollUp_Rllvr'),
         scrollGui.find('**/FndsLst_ScrollUp')), incButton_relief=None, incButton_pos=(0.0, 0.0, -0.3), incButton_image3_color=Vec4(0.6, 0.6, 0.6, 0.6), incButton_scale=(1.0, 1.0, -1.0), decButton_image=(scrollGui.find('**/FndsLst_ScrollUp'),
         scrollGui.find('**/FndsLst_ScrollDN'),
         scrollGui.find('**/FndsLst_ScrollUp_Rllvr'),
         scrollGui.find('**/FndsLst_ScrollUp')), decButton_relief=None, decButton_pos=(0.0, 0.0, 0.175), decButton_image3_color=Vec4(0.6, 0.6, 0.6, 0.6), itemFrame_pos=(-0.17, 0.0, 0.11), itemFrame_relief=None, numItemsVisible=9, items=[], pos=(2.4, 0.0, 0.025), scale=3.5)
        clipper = PlaneNode('clipper')
        clipper.setPlane(Plane(Vec3(-1, 0, 0), Point3(0.32, 0, 0)))
        clipNP = self.scrollList.component('itemFrame').attachNewNode(clipper)
        self.scrollList.component('itemFrame').setClipPlane(clipNP)
        self.close = DirectButton(parent=self, relief=None, image=(backGui.find('**/PckMn_BackBtn'), backGui.find('**/PckMn_BackBtn_Dn'), backGui.find('**/PckMn_BackBtn_Rlvr')), pos=(2.3, 0.0, -1.65), scale=3, text=TTLocalizer.TownBattleSOSBack, text_scale=0.05, text_pos=(0.01, -0.012), text_fg=Vec4(0, 0, 0.8, 1), command=self.__close)
        gui.removeNode()
        scrollGui.removeNode()
        backGui.removeNode()
        bgd.removeNode()
        self.hide()

    def unload(self):
        if self.isLoaded == 0:
            return None
        self.isLoaded = 0
        self.exit()
        del self.title
        del self.scrollList
        del self.close
        del self.avatars
        del self.NPCFriends
        DirectFrame.destroy(self)

    def makeAvatarButton(self, avatarId):
        handle = base.cr.identifyAvatar(avatarId)
        #if handle == None:
            #base.cr.fillUpFriendsMap()
            #return
        avatarName = handle.getName()
        fg = Vec4(0.0, 0.0, 0.0, 1.0)
        if handle.isPet():
            com = self.__chosePet
        else:
            com = self.__choseAvatar
        return DirectButton(relief=None, text=avatarName, text_scale=0.04, text_align=TextNode.ALeft, text_fg=fg, text1_bg=self.textDownColor, text2_bg=self.textRolloverColor, text3_fg=self.textDisabledColor, command=com, extraArgs=[avatarId, avatarName])

    def makeNPCFriendButton(self, NPCFriendId, numCalls):
        if NPCFriendId not in TTLocalizer.NPCToonNames:
            return None
        friendName = TTLocalizer.NPCToonNames[NPCFriendId]
        friendName += ' %d' % numCalls
        fg = Vec4(0.0, 0.0, 0.0, 1.0)
        return DirectButton(relief=None, text=friendName, text_scale=0.04, text_align=TextNode.ALeft, text_fg=fg, text1_bg=self.textDownColor, text2_bg=self.textRolloverColor, text3_fg=self.textDisabledColor, command=self.__choseNPCFriend, extraArgs=[NPCFriendId])

    def enter(self, canLure = 1, canTrap = 1):
        if self.isEntered == 1:
            return None
        self.isEntered = 1
        if self.isLoaded == 0:
            self.load()
        self.canLure = canLure
        self.canTrap = canTrap
        self.factoryToonIdList = None
        messenger.send('SOSPanelEnter', [self])
        self.__updateScrollList()
        self.__updateNPCFriendsPanel()
        self.__updateTitleText()
        self.show()
        self.accept('onlineAvatarsChanged', self.__onlineAvatarsChanged)

    def exit(self):
        if self.isEntered == 0:
            return None
        self.isEntered = 0
        self.hide()
        self.ignore('avatarOnline')
        self.ignore('avatarOffline')
        self.ignore('onlineAvatarsComplete')
        messenger.send(self.doneEvent)

    def __close(self):
        doneStatus = {}
        doneStatus['mode'] = 'Back'
        messenger.send(self.doneEvent, [doneStatus])

    def __choseAvatar(self, avatarId, avatarName):
        doneStatus = {}
        doneStatus['mode'] = 'Friend'
        doneStatus['friend'] = avatarId
        messenger.send(self.doneEvent, [doneStatus])

    def __chosePet(self, petId, petName):
        doneStatus = {}
        doneStatus['mode'] = 'Pet'
        doneStatus['petId'] = petId
        doneStatus['petName'] = petName
        messenger.send(self.doneEvent, [doneStatus])

    def __choseNPCFriend(self, friendId):
        doneStatus = {}
        doneStatus['mode'] = 'NPCFriend'
        doneStatus['friend'] = friendId
        self.chosenNPCToons.append(friendId)
        messenger.send(self.doneEvent, [doneStatus])

    def setFactoryToonIdList(self, toonIdList):
        self.factoryToonIdList = toonIdList[:]

    def __updateScrollList(self):
        if self.bldg or self.factoryToonIdList:
            return

        for avatarId in list(self.avatars.keys()):
            if not base.cr.getAvatarVisibility(avatarId):
                avatarBtn = self.avatars[avatarId]
                self.scrollList.removeItem(avatarBtn)
                if not avatarBtn.isEmpty():
                    avatarBtn.destroy()
                del self.avatars[avatarId]

        onlineAvatarIds = list(base.cr.onlineAvatars.keys())

        battlePets = base.config.GetBool('want-pets-in-battle', 1)
        # TODO: CHECK IF THE TOON HAS FROZEN INVENTORY, RATHER THAN FROZEN STATUS
        #       THE STATUS, WHEN ADDED SHOULD PROVIDE THE FLAG FOR THE TOON
        frozen = base.localAvatar.hasStatusEffect('ttrealms:frozen')
        if not frozen and base.wantPets and battlePets == 1 and base.localAvatar.hasPet():
            onlineAvatarIds.insert(0, base.localAvatar.getPetId())

        for avatarId in onlineAvatarIds:
            if avatarId != base.localAvatar.doId and avatarId not in self.avatars and base.cr.getAvatarVisibility(avatarId):
                avatarBtn = self.makeAvatarButton(avatarId)
                if avatarBtn:
                    self.scrollList.addItem(avatarBtn)
                    self.avatars[avatarId] = avatarBtn

    def __updateNPCFriendsPanel(self):
        self.NPCFriends = {}
        # TODO: CHECK IF THE TOON HAS FROZEN INVENTORY, RATHER THAN FROZEN STATUS
        #       THE STATUS, WHEN ADDED SHOULD PROVIDE THE FLAG FOR THE TOON
        frozen = base.localAvatar.hasStatusEffect('ttrealms:frozen')
        for friend, count in list(base.localAvatar.NPCFriendsDict.items()):
            track = NPCToons.getNPCTrack(friend)
            if frozen or track == ToontownBattleGlobals.LURE_TRACK and self.canLure == 0 or track == ToontownBattleGlobals.TRAP_TRACK and self.canTrap == 0:
                self.NPCFriends[friend] = 0
            else:
                self.NPCFriends[friend] = count

        self.NPCFriendPanel.update(self.NPCFriends, fCallable=1)

    def __updateTitleText(self):
        isEmpty = (len(self.avatars) == 0 and len(self.NPCFriends) == 0)
        if isEmpty:
            self.title['text'] = TTLocalizer.TownBattleSOSNoFriends
        else:
            self.title['text'] = TTLocalizer.TownBattleSOSWhichFriend

    def __onlineAvatarsChanged(self):
        self.__updateScrollList()
        self.__updateTitleText()
