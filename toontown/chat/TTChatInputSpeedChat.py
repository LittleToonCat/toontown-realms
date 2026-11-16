from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM
from direct.fsm import State
from direct.gui import DirectGuiGlobals
from direct.showbase import DirectObject
from functools import partial

from direct.gui.DirectGui import *

from otp.otpbase import OTPGlobals
from otp.otpbase import OTPLocalizer
from otp.otpgui import OTPGUIUtils
from otp.speedchat import SpeedChatGlobals
from otp.speedchat.SpeedChat import SpeedChat
from otp.speedchat.SpeedChatTypes import *
from toontown.chat import ResistanceChat
from toontown.speedchat import TTSCIndexedTerminal
from toontown.speedchat import TTSCSingingTerminal
from toontown.speedchat import TTSpeedChatGlobals
from toontown.speedchat.TTSpeedChatTypes import *
from toontown.toonbase import TTLocalizer, ClientSettings
from toontown.toonbase.ToontownSettings import speedChatStyles

retro = not ClientSettings.NewSpeedchatPhrases.get()
if retro:
    stinkyMenuStructure = [OTPLocalizer.SCMenuStinky,
                           {900: 3},
                           {901: 3},
                           {902: 3},
                           {903: 3},
                           904,
                           {905: 3},
                           910]
    playgroundMenuStructure = [OTPLocalizer.SCMenuPlacesPlayground,
                               1100,
                               1101,
                               1105,
                               1106,
                               1107,
                               1108,
                               1109,
                               1110,
                               1111,
                               1117,
                               1125,
                               1126]
    tauntMenuStructure = [OTPLocalizer.SCMenuBattleTaunts,
                          1403,
                          1406,
                          1520,
                          1521,
                          1522,
                          1523,
                          1524,
                          1525,
                          1526,
                          1407,
                          1408]
else:
    stinkyMenuStructure = [OTPLocalizer.SCMenuStinky,
                           {900: 3},
                           {901: 3},
                           {902: 3},
                           {903: 3},
                           904,
                           {905: 3},
                           {906: 3},
                           {907: 3},
                           908,
                           909,
                           910]
    playgroundMenuStructure = [OTPLocalizer.SCMenuPlacesPlayground,
                               1100,
                               1101,
                               1131,
                               1105,
                               1106,
                               1107,
                               1108,
                               1109,
                               1110,
                               1111,
                               1117,
                               1125,
                               1126]
    tauntMenuStructure = [OTPLocalizer.SCMenuBattleTaunts,
                          1403,
                          1406,
                          1520,
                          1521,
                          1522,
                          1523,
                          1524,
                          1525,
                          1526,
                          1527,
                          1407,
                          1408]

scStructure = [[OTPLocalizer.SCMenuHello,
  {100: 0},
  {101: 0},
  {102: 0},
  {103: 0},
  {104: 0},
  {105: 0},
  106,
  107,
  108,
  109],
 [OTPLocalizer.SCMenuBye,
  {200: 0},
  {201: 0},
  {202: 0},
  203,
  204,
  205,
  206,
  208,
  209,
  207],
 [OTPLocalizer.SCMenuHappy,
  {300: 1},
  {301: 1},
  {302: 1},
  303,
  {304: 1},
  305,
  306,
  307,
  308,
  309,
  310,
  311,
  {312: 1},
  {313: 1},
  {314: 1},
  315,
  316],
 [OTPLocalizer.SCMenuSad,
  {400: 2},
  {401: 2},
  {402: 2},
  403,
  404,
  405,
  406,
  407,
  408,
  409,
  410],
 [OTPLocalizer.SCMenuFriendly,
  [OTPLocalizer.SCMenuFriendlyYou,
   600,
   601,
   602,
   603],
  [OTPLocalizer.SCMenuFriendlyILike,
   700,
   701,
   702,
   703,
   704,
   705],
  500,
  501,
  502,
  503,
  504,
  505,
  506,
  507,
  508,
  509,
  510,
  515,
  511,
  512,
  513,
  514],
 [OTPLocalizer.SCMenuSorry,
  801,
  800,
  802,
  803,
  804,
  811,
  814,
  815,
  817,
  812,
  813,
  818,
  805,
  806,
  807,
  816,
  808,
  {809: 5},
  810],
 stinkyMenuStructure,
 [OTPLocalizer.SCMenuPlaces,
  playgroundMenuStructure,
  [OTPLocalizer.SCMenuPlacesCogs,
   1102,
   1103,
   1104,
   1114,
   1115,
   1116,
   1119,
   1120,
   1121,
   1122,
   1123,
   1124,
   1127,
   1128,
   1129,
   1130],
  [OTPLocalizer.SCMenuPlacesEstate,
   1112,
   1113,
   1013,
   1118,
   1016],
  [OTPLocalizer.SCMenuParties,
   5300,
   5301,
   5302,
   5303],
  [OTPLocalizer.SCMenuPlacesWait,
   1015,
   1007,
   1008,
   1010,
   1011,
   1014,
   1017],
  1000,
  1001,
  1002,
  1003,
  1004,
  1005,
  1006,
  1009,
  1012],
 [OTPLocalizer.SCMenuToontasks,
  [TTSCToontaskMenu, OTPLocalizer.SCMenuToontasksMyTasks],
  [OTPLocalizer.SCMenuToontasksYouShouldChoose,
   1300,
   1301,
   1302,
   1303,
   1304],
  [OTPLocalizer.SCMenuToontasksINeedMore,
   1206,
   1210,
   1211,
   1212,
   1207,
   1213,
   1214,
   1215],
  1200,
  1201,
  1202,
  1208,
  1203,
  1209,
  1204,
  1205],
 [OTPLocalizer.SCMenuBattle,
  [OTPLocalizer.SCMenuBattleGags,
   1500,
   1501,
   1502,
   1503,
   1504,
   1505,
   1506,
   1401,
   1402,
   1413],
  tauntMenuStructure,
  [OTPLocalizer.SCMenuBattleStrategy,
   1414,
   1550,
   1551,
   1552,
   1415,
   1553,
   1554,
   1555,
   1556,
   1557,
   1558,
   1559],
  1400,
  1416,
  1404,
  1405,
  1409,
  1410,
  1411,
  1412],
 [OTPLocalizer.SCMenuGagShop,
  1600,
  1601,
  1602,
  1603,
  1604,
  1605,
  1606],
 {1: 16},
 {2: 17},
 3]
if hasattr(base, 'wantPets') and base.wantPets:
    scPetMenuStructure = [[OTPLocalizer.SCMenuPets,
      [TTSCPetTrickMenu, OTPLocalizer.SCMenuPetTricks],
      21000,
      21001,
      21002,
      21003,
      21004,
      21005,
      21006]]
cfoMenuStructure = [[OTPLocalizer.SCMenuCFOBattleCranes,
  2100,
  2101,
  2102,
  2103,
  2104,
  2105,
  2106,
  2107,
  2108,
  2109,
  2110],
 [OTPLocalizer.SCMenuCFOBattleGoons,
  2120,
  2121,
  2122,
  2123,
  2124,
  2125,
  2126],
 2130,
 2131,
 2132,
 2133,
 1410]
cjMenuStructure = [2200,
 2201,
 2202,
 2203,
 2204,
 2205,
 2206,
 2207,
 2208,
 2209,
 2210]
ceoMenuStructure = [2300,
 2301,
 2302,
 2303,
 2304,
 2305,
 2306,
 2307,
 2312,
 2313,
 2314,
 2315,
 2308,
 2309,
 2310,
 2311,
 2316,
 2317]
lawbotArenaMenuStructure = [2200, 2201, 2202, 2203, 2204, 2205, 2206, 2224, 2225, 2226, 2227, 2228, 2229]
winterVpMenuStructure = [30500, 30501, 30502, 30503, 30504, 30505, 30506, 30507]


class TTChatInputSpeedChat(DirectObject.DirectObject):
    DefaultSCColorScheme = SCColorScheme()
    notify = DirectNotifyGlobal.directNotify.newCategory('TTChatInputSpeedChat')

    def __init__(self, chatMgr):
        DirectObject.DirectObject.__init__(self)
        self.chatMgr = chatMgr
        self.whisperAvatarId = None
        self.toPlayer = 0 # TODO: fully cleanup
        buttons = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
        okButtonImage = (
            buttons.find('**/ChtBx_OKBtn_UP'), 
            buttons.find('**/ChtBx_OKBtn_DN'), 
            buttons.find('**/ChtBx_OKBtn_Rllvr')
            )
        self.emoteNoAccessPanel = DirectFrame(
            parent=hidden, 
            relief=None, 
            state='normal', 
            text=OTPLocalizer.SCEmoteNoAccessMsg, 
            frameSize=(-1, 1, -1, 1), 
            geom=DGG.getDefaultDialogGeom(), 
            geom_color=OTPGlobals.GlobalDialogColor, 
            geom_scale=(0.92, 1, 0.6), 
            geom_pos=(0, 0, -.08), 
            text_scale=0.08
            )
        self.okButton = DirectButton(
            parent=self.emoteNoAccessPanel, 
            image=okButtonImage, 
            relief=None, 
            text=OTPLocalizer.SCEmoteNoAccessOK, 
            text_scale=0.05, 
            text_pos=(0.0, -0.1), 
            textMayChange=0, 
            pos=(0.0, 0.0, -0.2), 
            command=self.handleEmoteNoAccessDone
            )

        self.currentColorScheme = TTChatInputSpeedChat.DefaultSCColorScheme
        self.insidePartiesMenu = None

        self.createSpeedChat()
        self.createEmotesMenu()
        self.createUnitesMenu()

        self.whiteList = None
        self.allowWhiteListSpeedChat = base.config.GetBool('white-list-speed-chat', 0)
        if self.allowWhiteListSpeedChat:
            self.addWhiteList()
        self.factoryMenu = None
        self.countryClubMenu = None
        self.kartRacingMenu = None
        self.cogMenu = None
        self.cfoMenu = None
        self.cjMenu = None
        self.ceoMenu = None
        self.lawbotArenaMenu = None
        self.golfMenu = None
        self.boardingGroupMenu = None
        self.singingGroupMenu = None
        self.aprilToonsMenu = None
        self.victoryPartiesMenu = None
        self.sillyPhaseOneMenu = None
        self.sillyPhaseTwoMenu = None
        self.sillyPhaseThreeMenu = None
        self.sillyPhaseFourMenu = None
        self.sillyPhaseFiveMenu = None
        self.sellbotNerfMenu = None
        self.jellybeanJamMenu = None
        self.halloweenMenu = None
        self.winterMenu = None
        self.sellbotInvasionMenu = None
        self.sellbotFieldOfficeMenu = None
        self.idesOfMarchMenu = None
        self.winterVpMenu = None

        # Magic Word list- for non Legit Mode only
        # Don't show the Magic Words Menu if we are in legit mode
        if not base.cr.legitMode and not retro:
            self.magicWordsMenu = None
            self.addMagicWordsMenu()

        def listenForSCEvent(eventBaseName, handler, scMenu = self.speedChat, self = self):
            eventName = scMenu.getEventName(eventBaseName)
            self.accept(eventName, handler)

        listenForSCEvent(SpeedChatGlobals.SCTerminalLinkedEmoteEvent, self.handleLinkedEmote)
        listenForSCEvent(SpeedChatGlobals.SCStaticTextMsgEvent, self.handleStaticTextMsg)
        listenForSCEvent(SpeedChatGlobals.SCCustomMsgEvent, self.handleCustomMsg)
        listenForSCEvent(SpeedChatGlobals.SCEmoteMsgEvent, self.handleEmoteMsg, self.emoteMenu)
        listenForSCEvent(SpeedChatGlobals.SCEmoteNoAccessEvent, self.handleEmoteNoAccess, self.emoteMenu)
        listenForSCEvent(TTSpeedChatGlobals.TTSCToontaskMsgEvent, self.handleToontaskMsg)
        listenForSCEvent(TTSpeedChatGlobals.TTSCCogMsgEvent, self.handleCogMsg)
        listenForSCEvent(TTSpeedChatGlobals.TTSCResistanceMsgEvent, self.handleResistanceMsg, self.unitesMenu)
        listenForSCEvent(TTSCSingingTerminal.TTSCSingingMsgEvent, self.handleSingingMsg)
        listenForSCEvent('SpeedChatStyleChange', self.handleSpeedChatStyleChange)
        listenForSCEvent(TTSCIndexedTerminal.TTSCIndexedMsgEvent, self.handleStaticTextMsg)
        self.accept('resistanceMessagesChanged', self.createUnitesMenu)
        self.accept('emotesChanged', self.createEmotesMenu)
        self.fsm = ClassicFSM.ClassicFSM(
                'SpeedChat',
                [
                    State.State('off', self.enterOff, self.exitOff, ['scActive', 'unitesActive', 'emotesActive']),
                    State.State('scActive', self.enterActive, self.exitActive, ['off', 'unitesActive', 'emotesActive']),
                    State.State('emotesActive', self.enterEmotesActive, self.exitEmotesActive, ['off', 'scActive', 'unitesActive']),
                    State.State('unitesActive', self.enterUnitesActive, self.exitUnitesActive, ['off', 'scActive', 'emotesActive']),
                ], 'off', 'off')
        self.fsm.enterInitialState()

        trolley = TTSCJellybeanJamMenu.JellybeanJamPhases.TROLLEY
        fishing = TTSCJellybeanJamMenu.JellybeanJamPhases.FISHING
        parties = TTSCJellybeanJamMenu.JellybeanJamPhases.PARTIES
        self.holidayMenus = {
            'winter': [self.addWinterMenu, self.removeWinterMenu],
            'carol': [self.addCarolMenu, self.removeCarolMenu],
            'halloween': [self.addHalloweenMenu, self.removeHalloweenMenu],
            'aprilToons': [self.addAprilToonsMenu, self.removeAprilToonsMenu],
            'sillyMenuOne': [self.addSillyPhaseOneMenu, self.removeSillyPhaseOneMenu],
            'sillyMenuTwo': [self.addSillyPhaseTwoMenu, self.removeSillyPhaseTwoMenu],
            'sillyMenuThree': [self.addSillyPhaseThreeMenu, self.removeSillyPhaseThreeMenu],
            'sillyMenuFour': [self.addSillyPhaseFourMenu, self.removeSillyPhaseFourMenu],
            'sillyMenuFive': [self.addSillyPhaseFiveMenu, self.removeSillyPhaseFiveMenu],
            'victoryParties': [self.addVictoryPartiesMenu, self.removeVictoryPartiesMenu],
            'sellbotNerf': [self.addSellbotNerfMenu, self.removeSellbotNerfMenu],
            'jellybeanTrolley': [partial(self.addJellybeanJamMenu, trolley), self.removeJellybeanJamMenu],
            'jellybeanFishing': [partial(self.addJellybeanJamMenu, fishing), self.removeJellybeanJamMenu],
            'jellybeanParties': [partial(self.addJellybeanJamMenu, parties), self.removeJellybeanJamMenu],
            'sellbotInvasion': [self.addSellbotInvasionMenu, self.removeSellbotInvasionMenu],
            'sellbotFieldOffice': [self.addSellbotFieldOfficeMenu, self.removeSellbotFieldOfficeMenu],
            'idesOfMarch': [self.addIdesOfMarchMenu, self.removeIdesOfMarchMenu]
        }
        return

    def delete(self):
        self.ignoreAll()
        self.removeWhiteList()
        self.okButton.destroy()
        self.emoteNoAccessPanel.destroy()
        del self.emoteNoAccessPanel
        self.speedChat.destroy()
        del self.speedChat
        del self.fsm
        del self.chatMgr

    def show(self, whisperAvatarId = None, toPlayer = 0, menu = 0):
        self.whisperAvatarId = whisperAvatarId
        self.fsm.request(('scActive', 'emotesActive', 'unitesActive')[menu])

    def hide(self):
        self.fsm.request('off')

    def createSpeedChat(self):
        structure = []
        if launcher and not launcher.isTestServer() or __dev__:
            structure.append([TTSCPromotionalMenu, OTPLocalizer.SCMenuPromotion])
        structure.append([SCCustomMenu, OTPLocalizer.SCMenuCustom])
        if hasattr(base, 'wantPets') and base.wantPets:
            structure += scPetMenuStructure
        structure += scStructure
        self.createSpeedChatObject(structure)

    def createEmotesMenu(self):
        structure = [{'menuObjects': []}]
        if hasattr(base, 'localAvatar'):
            for i in range(len(base.localAvatar.emoteAccess)):
                if base.localAvatar.emoteAccess[i]:
                    structure[0]['menuObjects'].append(SCEmoteTerminal(i))
        self.createEmotesObject(structure)

    def createUnitesMenu(self):
        structure = [{'menuObjects': []}]
        hasUnites = False
        if hasattr(base, 'localAvatar'):
            for menuIndex in ResistanceChat.resistanceMenu:
                resMenu = SCMenu()
                for itemIndex in ResistanceChat.getItems(menuIndex):
                    textId = ResistanceChat.encodeId(menuIndex, itemIndex)
                    charges = base.localAvatar.getResistanceMessageCharges(textId)
                    if charges > 0:
                        resMenu.append(TTSCResistanceTerminal(textId, charges))
                        hasUnites = True

                textId = ResistanceChat.encodeId(menuIndex, 0)
                menuName = ResistanceChat.getMenuName(textId)
                structure[0]['menuObjects'].append(SCMenuHolder(menuName, resMenu))
            if hasUnites:
                self.chatMgr.unitesButton['state'] = DirectGuiGlobals.NORMAL
            else:
                self.chatMgr.unitesButton['state'] = DirectGuiGlobals.DISABLED
        self.createUnitesObject(structure)

    def enterOff(self):
        pass

    def exitOff(self):
        pass

    def enterActive(self):

        def handleCancel(self = self):
            self.chatMgr.fsm.request('mainMenu')

        self.accept('mouse1', handleCancel)

        def selectionMade(self = self):
            self.chatMgr.fsm.request('mainMenu')

        self.terminalSelectedEvent = self.speedChat.getEventName(SpeedChatGlobals.SCTerminalSelectedEvent)
        if base.config.GetBool('want-sc-auto-hide', 1):
            self.accept(self.terminalSelectedEvent, selectionMade)
        self.speedChat.reparentTo(base.a2dpTopLeft, DGG.FOREGROUND_SORT_INDEX)
        scZ = -0.12
        self.speedChat.setPos(0.1, 0, scZ)
        OTPGUIUtils.Animations.slideUp(self.speedChat, finalZ = scZ, startZ = -.3, intensity = 0.5).start()
        self.speedChat.setWhisperMode(self.whisperAvatarId != None)
        self.speedChat.enter()
        return

    def exitActive(self):
        self.ignore('mouse1')
        self.ignore(self.terminalSelectedEvent)
        self.speedChat.exit()
        self.speedChat.reparentTo(hidden)
        self.emoteNoAccessPanel.reparentTo(hidden)

    def enterEmotesActive(self):

        def handleCancel(self = self):
            self.chatMgr.fsm.request('mainMenu')

        self.accept('mouse1', handleCancel)

        def selectionMade(self = self):
            self.chatMgr.fsm.request('mainMenu')

        self.terminalSelectedEvent = self.emoteMenu.getEventName(SpeedChatGlobals.SCTerminalSelectedEvent)
        if base.config.GetBool('want-sc-auto-hide', 1):
            self.accept(self.terminalSelectedEvent, selectionMade)
        self.emoteMenu.reparentTo(base.a2dpTopLeft, DGG.FOREGROUND_SORT_INDEX)
        scZ = -0.12
        self.emoteMenu.setPos(0.28, 0, scZ)
        OTPGUIUtils.Animations.slideUp(self.emoteMenu, finalZ = scZ, startZ = -.3, intensity = 0.5).start()
        self.emoteMenu.setWhisperMode(self.whisperAvatarId != None)
        self.emoteMenu.enter()
        return

    def exitEmotesActive(self):
        self.ignore('mouse1')
        self.ignore(self.terminalSelectedEvent)
        self.emoteMenu.exit()
        self.emoteMenu.reparentTo(hidden)
        self.emoteNoAccessPanel.reparentTo(hidden)

    def enterUnitesActive(self):

        def handleCancel(self = self):
            self.chatMgr.fsm.request('mainMenu')

        self.accept('mouse1', handleCancel)

        def selectionMade(self = self):
            self.chatMgr.fsm.request('mainMenu')

        self.terminalSelectedEvent = self.unitesMenu.getEventName(SpeedChatGlobals.SCTerminalSelectedEvent)
        if base.config.GetBool('want-sc-auto-hide', 1):
            self.accept(self.terminalSelectedEvent, selectionMade)
        self.unitesMenu.reparentTo(base.a2dpTopLeft, DGG.FOREGROUND_SORT_INDEX)
        scZ = -0.12
        self.unitesMenu.setPos(0.18, 0, scZ)
        OTPGUIUtils.Animations.slideUp(self.unitesMenu, finalZ = scZ, startZ = -.3, intensity = 0.5).start()
        self.unitesMenu.setWhisperMode(self.whisperAvatarId != None)
        self.unitesMenu.enter()
        return

    def exitUnitesActive(self):
        self.ignore('mouse1')
        self.ignore(self.terminalSelectedEvent)
        self.unitesMenu.exit()
        self.unitesMenu.reparentTo(hidden)

    def handleLinkedEmote(self, emoteId, displayType=0):
        if self.whisperAvatarId is None and displayType != 2:
            lt = base.localAvatar
            lt.b_setEmoteState(emoteId, animMultiplier=lt.animMultiplier)
        return

    def handleStaticTextMsg(self, textId, displayType=0):
        if self.whisperAvatarId is None:
            self.chatMgr.sendSCChatMessage(textId, displayType)
        else:
            self.chatMgr.sendSCWhisperMessage(textId, self.whisperAvatarId)

    def handleSingingMsg(self, textId):
        if self.whisperAvatarId is None:
            self.chatMgr.sendSCSingingChatMessage(textId)
        else:
            self.chatMgr.sendSCSingingWhisperMessage(textId)

    def handleCustomMsg(self, textId, displayType=0):
        if self.whisperAvatarId is None:
            self.chatMgr.sendSCCustomChatMessage(textId, displayType)
        else:
            self.chatMgr.sendSCCustomWhisperMessage(textId, self.whisperAvatarId)

    def handleEmoteMsg(self, emoteId):
        if self.whisperAvatarId is None:
            self.chatMgr.sendSCEmoteChatMessage(emoteId)
        else:
            self.chatMgr.sendSCEmoteWhisperMessage(emoteId, self.whisperAvatarId)

    def handleEmoteNoAccess(self):
        if self.whisperAvatarId is None:
            self.emoteNoAccessPanel.setPos(0, 0, 0)
        else:
            self.emoteNoAccessPanel.setPos(0.37, 0, 0)
        self.emoteNoAccessPanel.reparentTo(aspect2d)

    def handleEmoteNoAccessDone(self):
        self.emoteNoAccessPanel.reparentTo(hidden)

    def handleToontaskMsg(self, taskId, toNpcId, toonProgress, msgIndex, displayType=0):
        if self.whisperAvatarId is None:
            self.chatMgr.sendSCToontaskChatMessage(taskId, toNpcId, toonProgress, msgIndex, displayType)
        else:
            self.chatMgr.sendSCToontaskWhisperMessage(taskId, toNpcId, toonProgress, msgIndex, self.whisperAvatarId)

    def handleCogMsg(self, cogType, quoteTypeIndex, quoteIndex, displayType = 0):
        if self.whisperAvatarId:
            base.cr.chatManager.sendWhisperCogMessage(cogType, quoteTypeIndex, quoteIndex, self.whisperAvatarId)
        else:
            base.cr.chatManager.sendCogMessage(cogType, quoteTypeIndex, quoteIndex, displayType)

    def handleResistanceMsg(self, textId):
        self.chatMgr.sendSCResistanceChatMessage(textId)

    def handleSpeedChatStyleChange(self):
        nameKey, arrowColor, rolloverColor, frameColor = speedChatStyles[base.localAvatar.getSpeedChatStyleIndex()]
        newSCColorScheme = SCColorScheme(arrowColor=arrowColor, rolloverColor=rolloverColor, frameColor=frameColor)
        self.currentColorScheme = newSCColorScheme
        self.speedChat.setColorScheme(newSCColorScheme)
        self.emoteMenu.setColorScheme(newSCColorScheme)
        self.unitesMenu.setColorScheme(newSCColorScheme)

    def createSpeedChatObject(self, structure):
        if hasattr(self, 'speedChat'):
            self.speedChat.exit()
            self.speedChat.destroy()
            del self.speedChat
        self.speedChat = SpeedChat(structure = structure)
        self.speedChat.setScale(TTLocalizer.TTCISCspeedChat)
        self.speedChat.setBin('gui-popup', 0)
        self.speedChat.setTopLevelOverlap(TTLocalizer.TTCISCtopLevelOverlap)
        self.speedChat.setColorScheme(self.currentColorScheme)
        self.speedChat.finalizeAll()

    def createEmotesObject(self, structure):
        if hasattr(self, 'emoteMenu'):
            self.emoteMenu.exit()
            self.emoteMenu.destroy()
            del self.emoteMenu
        self.emoteMenu = SpeedChat(structure = structure)
        self.emoteMenu.setScale(TTLocalizer.TTCISCspeedChat)
        self.emoteMenu.setBin('gui-popup', 0)
        self.emoteMenu.setTopLevelOverlap(TTLocalizer.TTCISCtopLevelOverlap)
        self.emoteMenu.setColorScheme(self.currentColorScheme)
        self.emoteMenu.finalizeAll()

    def createUnitesObject(self, structure):
        if hasattr(self, 'unitesMenu'):
            self.unitesMenu.exit()
            self.unitesMenu.destroy()
            del self.unitesMenu
        self.unitesMenu = SpeedChat(structure = structure)
        self.unitesMenu.setScale(TTLocalizer.TTCISCspeedChat)
        self.unitesMenu.setBin('gui-popup', 0)
        self.unitesMenu.setTopLevelOverlap(TTLocalizer.TTCISCtopLevelOverlap)
        self.unitesMenu.setColorScheme(self.currentColorScheme)
        self.unitesMenu.finalizeAll()

    def addFactoryMenu(self):
        if self.factoryMenu == None:
            menu = TTSCFactoryMenu()
            self.factoryMenu = SCMenuHolder(OTPLocalizer.SCMenuFactory, menu=menu)
            self.speedChat[2:2] = [self.factoryMenu]

    def removeFactoryMenu(self):
        if self.factoryMenu:
            i = self.speedChat.index(self.factoryMenu)
            del self.speedChat[i]
            self.factoryMenu.destroy()
            self.factoryMenu = None

    def addCountryClubMenu(self):
        if self.countryClubMenu == None:
            menu = TTSCCountryClubMenu()
            self.countryClubMenu = SCMenuHolder(OTPLocalizer.SCMenuCountryClub, menu=menu)
            self.speedChat[2:2] = [self.countryClubMenu]

    def removeCountryClubMenu(self):
        if self.countryClubMenu:
            i = self.speedChat.index(self.countryClubMenu)
            del self.speedChat[i]
            self.countryClubMenu.destroy()
            self.countryClubMenu = None

    def addKartRacingMenu(self):
        if self.kartRacingMenu == None:
            menu = TTSCKartRacingMenu()
            self.kartRacingMenu = SCMenuHolder(OTPLocalizer.SCMenuKartRacing, menu=menu)
            self.speedChat[2:2] = [self.kartRacingMenu]
        return

    def removeKartRacingMenu(self):
        if self.kartRacingMenu:
            i = self.speedChat.index(self.kartRacingMenu)
            del self.speedChat[i]
            self.kartRacingMenu.destroy()
            self.kartRacingMenu = None
        return

    def addCogMenu(self, cogType):
        if self.cogMenu == None:
            menu = TTSCCogMenu(cogType)
            self.cogMenu = SCMenuHolder(OTPLocalizer.SCMenuCog, menu=menu)
            self.speedChat[2:2] = [self.cogMenu]

    def removeCogMenu(self):
        if self.cogMenu:
            i = self.speedChat.index(self.cogMenu)
            del self.speedChat[i]
            self.cogMenu.destroy()
            self.cogMenu = None
        return

    def addCFOMenu(self):
        if self.cfoMenu == None:
            menu = SCMenu()
            menu.rebuildFromStructure(cfoMenuStructure)
            self.cfoMenu = SCMenuHolder(OTPLocalizer.SCMenuCFOBattle, menu=menu)
            self.speedChat[2:2] = [self.cfoMenu]
        return

    def removeCFOMenu(self):
        if self.cfoMenu:
            i = self.speedChat.index(self.cfoMenu)
            del self.speedChat[i]
            self.cfoMenu.destroy()
            self.cfoMenu = None
        return

    def addCJMenu(self, bonusWeight = -1):
        if self.cjMenu == None:
            menu = SCMenu()
            myMenuCopy = cjMenuStructure[:]
            if bonusWeight >= 0:
                myMenuCopy.append(2211 + bonusWeight)
            menu.rebuildFromStructure(myMenuCopy)
            self.cjMenu = SCMenuHolder(OTPLocalizer.SCMenuCJBattle, menu=menu)
            self.speedChat[2:2] = [self.cjMenu]
        return

    def removeCJMenu(self):
        if self.cjMenu:
            i = self.speedChat.index(self.cjMenu)
            del self.speedChat[i]
            self.cjMenu.destroy()
            self.cjMenu = None
        return

    def addCEOMenu(self):
        if self.ceoMenu == None:
            menu = SCMenu()
            menu.rebuildFromStructure(ceoMenuStructure)
            self.ceoMenu = SCMenuHolder(OTPLocalizer.SCMenuCEOBattle, menu=menu)
            self.speedChat[2:2] = [self.ceoMenu]
        return

    def removeCEOMenu(self):
        if self.ceoMenu:
            i = self.speedChat.index(self.ceoMenu)
            del self.speedChat[i]
            self.ceoMenu.destroy()
            self.ceoMenu = None
        return

    def addLawbotArenaMenu(self,):
        if self.lawbotArenaMenu == None:
            menu = SCMenu()
            menu.rebuildFromStructure(lawbotArenaMenuStructure)
            self.lawbotArenaMenu = SCMenuHolder(OTPLocalizer.SCMenuLawbotArena, menu=menu)
            self.speedChat[2:2] = [self.lawbotArenaMenu]
        return

    def removeLawbotArenaMenu(self):
        if self.lawbotArenaMenu:
            i = self.speedChat.index(self.lawbotArenaMenu)
            del self.speedChat[i]
            self.lawbotArenaMenu.destroy()
            self.lawbotArenaMenu = None
        return

    def addInsidePartiesMenu(self):

        def isActivityInParty(activityIdList):
            activityList = base.distributedParty.partyInfo.activityList
            for activity in activityList:
                if activity.activityId in activityIdList:
                    return True

            return False

        def isDecorInParty(decorIdList):
            decorList = base.distributedParty.partyInfo.decors
            for decor in decorList:
                if decor.decorId in decorIdList:
                    return True

            return False

        insidePartiesMenuStructure = [5305,
         5306,
         5307,
         5308,
         5309]
        if self.insidePartiesMenu == None:
            menu = SCMenu()
            if hasattr(base, 'distributedParty') and base.distributedParty:
                if base.distributedParty.partyInfo.hostId == localAvatar.doId:
                    insidePartiesMenuStructure.insert(0, 5304)
                if isActivityInParty([0, 8, 9, 18, 19, 20]):
                    insidePartiesMenuStructure.extend([5310, 5311])
                if isActivityInParty([1]):
                    insidePartiesMenuStructure.append(5312)
                if isActivityInParty([2, 12, 14, 21]):
                    insidePartiesMenuStructure.extend([5313, 5314])
                if isActivityInParty([3, 13]):
                    insidePartiesMenuStructure.append(5315)
                if isActivityInParty([4, 10, 16, 17]):
                    insidePartiesMenuStructure.extend([5316, 5317])
                if isActivityInParty([5]):
                    insidePartiesMenuStructure.append(5318)
                if isActivityInParty([6]):
                    insidePartiesMenuStructure.extend([5319, 5320])
                if isActivityInParty([11, 15]):
                    insidePartiesMenuStructure.extend([30355, 30356])
                if len(base.distributedParty.partyInfo.decors):
                    insidePartiesMenuStructure.append(5321)
                    if isDecorInParty([3]):
                        insidePartiesMenuStructure.append(5322)
                    if isDecorInParty([16, 23]):
                        insidePartiesMenuStructure.append(30357)
                    if isDecorInParty([19, 24]):
                        insidePartiesMenuStructure.append(30358)
                    if isDecorInParty([21, 22]):
                        insidePartiesMenuStructure.append(30359)
                    if isDecorInParty([20]):
                        insidePartiesMenuStructure.append(30360)
            menu.rebuildFromStructure(insidePartiesMenuStructure)
            self.insidePartiesMenu = SCMenuHolder(OTPLocalizer.SCMenuParties, menu=menu)
            self.speedChat[2:2] = [self.insidePartiesMenu]
        return

    def addHolidayMenu(self, menuName):
        if menuName in self.holidayMenus:
            self.holidayMenus[menuName][0]()
        else:
            self.notify.warning(f"addHolidayMenu() - menuName {menuName} is not in self.holidayMenus!")

    def removeHolidayMenu(self, menuName):
        if menuName in self.holidayMenus:
            self.holidayMenus[menuName][1]()
        else:
            self.notify.warning(f"removeHolidayMenu() - menuName {menuName} is not in self.holidayMenus!")
            
    def removeInsidePartiesMenu(self):
        if self.insidePartiesMenu:
            i = self.speedChat.index(self.insidePartiesMenu)
            del self.speedChat[i]
            self.insidePartiesMenu.destroy()
            self.insidePartiesMenu = None
        return

    def addGolfMenu(self):
        if self.golfMenu == None:
            menu = TTSCGolfMenu()
            self.golfMenu = SCMenuHolder(OTPLocalizer.SCMenuGolf, menu=menu)
            self.speedChat[2:2] = [self.golfMenu]
        return

    def removeGolfMenu(self):
        if self.golfMenu:
            i = self.speedChat.index(self.golfMenu)
            del self.speedChat[i]
            self.golfMenu.destroy()
            self.golfMenu = None
        return

    def addBoardingGroupMenu(self, zoneId):
        if self.boardingGroupMenu == None:
            menu = TTSCBoardingMenu(zoneId)
            self.boardingGroupMenu = SCMenuHolder(OTPLocalizer.SCMenuBoardingGroup, menu=menu)
            self.speedChat[2:2] = [self.boardingGroupMenu]
        return

    def removeBoardingGroupMenu(self):
        if self.boardingGroupMenu:
            i = self.speedChat.index(self.boardingGroupMenu)
            del self.speedChat[i]
            self.boardingGroupMenu.destroy()
            self.boardingGroupMenu = None
        return

    def addSingingGroupMenu(self):
        if self.singingGroupMenu == None:
            menu = TTSCSingingMenu()
            self.singingGroupMenu = SCMenuHolder(OTPLocalizer.SCMenuSingingGroup, menu=menu)
            self.speedChat[2:2] = [self.singingGroupMenu]
        return

    def removeSingingMenu(self):
        if self.singingGroupMenu:
            i = self.speedChat.index(self.singingGroupMenu)
            del self.speedChat[i]
            self.singingGroupMenu.destroy()
            self.singingGroupMenu = None
        return

    def addAprilToonsMenu(self):
        if self.aprilToonsMenu == None:
            menu = TTSCAprilToonsMenu()
            self.aprilToonsMenu = SCMenuHolder(OTPLocalizer.SCMenuAprilToons, menu=menu)
            self.speedChat[3:3] = [self.aprilToonsMenu]
        return

    def removeAprilToonsMenu(self):
        if self.aprilToonsMenu:
            i = self.speedChat.index(self.aprilToonsMenu)
            del self.speedChat[i]
            self.aprilToonsMenu.destroy()
            self.aprilToonsMenu = None
        return

    def addSillyPhaseOneMenu(self):
        if self.sillyPhaseOneMenu == None:
            menu = TTSCSillyPhaseOneMenu()
            self.sillyPhaseOneMenu = SCMenuHolder(OTPLocalizer.SCMenuSillyHoliday, menu=menu)
            self.speedChat[3:3] = [self.sillyPhaseOneMenu]
        return

    def removeSillyPhaseOneMenu(self):
        if self.sillyPhaseOneMenu:
            i = self.speedChat.index(self.sillyPhaseOneMenu)
            del self.speedChat[i]
            self.sillyPhaseOneMenu.destroy()
            self.sillyPhaseOneMenu = None
        return

    def addSillyPhaseTwoMenu(self):
        if self.sillyPhaseTwoMenu == None:
            menu = TTSCSillyPhaseTwoMenu()
            self.sillyPhaseTwoMenu = SCMenuHolder(OTPLocalizer.SCMenuSillyHoliday, menu=menu)
            self.speedChat[3:3] = [self.sillyPhaseTwoMenu]
        return

    def removeSillyPhaseTwoMenu(self):
        if self.sillyPhaseTwoMenu:
            i = self.speedChat.index(self.sillyPhaseTwoMenu)
            del self.speedChat[i]
            self.sillyPhaseTwoMenu.destroy()
            self.sillyPhaseTwoMenu = None
        return

    def addSillyPhaseThreeMenu(self):
        if self.sillyPhaseThreeMenu == None:
            menu = TTSCSillyPhaseThreeMenu()
            self.sillyPhaseThreeMenu = SCMenuHolder(OTPLocalizer.SCMenuSillyHoliday, menu=menu)
            self.speedChat[3:3] = [self.sillyPhaseThreeMenu]
        return

    def removeSillyPhaseThreeMenu(self):
        if self.sillyPhaseThreeMenu:
            i = self.speedChat.index(self.sillyPhaseThreeMenu)
            del self.speedChat[i]
            self.sillyPhaseThreeMenu.destroy()
            self.sillyPhaseThreeMenu = None
        return

    def addSillyPhaseFourMenu(self):
        if self.sillyPhaseFourMenu == None:
            menu = TTSCSillyPhaseFourMenu()
            self.sillyPhaseFourMenu = SCMenuHolder(OTPLocalizer.SCMenuSillyHoliday, menu=menu)
            self.speedChat[3:3] = [self.sillyPhaseFourMenu]
        return

    def removeSillyPhaseFourMenu(self):
        if self.sillyPhaseFourMenu:
            i = self.speedChat.index(self.sillyPhaseFourMenu)
            del self.speedChat[i]
            self.sillyPhaseFourMenu.destroy()
            self.sillyPhaseFourMenu = None
        return

    def addSillyPhaseFiveMenu(self):
        if self.sillyPhaseFiveMenu == None:
            menu = TTSCSillyPhaseFiveMenu()
            self.sillyPhaseFiveMenu = SCMenuHolder(OTPLocalizer.SCMenuSillyHoliday, menu=menu)
            self.speedChat[3:3] = [self.sillyPhaseFiveMenu]
        return

    def removeSillyPhaseFiveMenu(self):
        if self.sillyPhaseFiveMenu:
            i = self.speedChat.index(self.sillyPhaseFiveMenu)
            del self.speedChat[i]
            self.sillyPhaseFiveMenu.destroy()
            self.sillyPhaseFiveMenu = None
        return

    def addVictoryPartiesMenu(self):
        if self.victoryPartiesMenu == None:
            menu = TTSCVictoryPartiesMenu()
            self.victoryPartiesMenu = SCMenuHolder(OTPLocalizer.SCMenuVictoryParties, menu=menu)
            self.speedChat[3:3] = [self.victoryPartiesMenu]
        return

    def removeVictoryPartiesMenu(self):
        if self.victoryPartiesMenu:
            i = self.speedChat.index(self.victoryPartiesMenu)
            del self.speedChat[i]
            self.victoryPartiesMenu.destroy()
            self.victoryPartiesMenu = None
        return

    def addSellbotNerfMenu(self):
        if self.sellbotNerfMenu == None:
            menu = TTSCSellbotNerfMenu()
            self.sellbotNerfMenu = SCMenuHolder(OTPLocalizer.SCMenuSellbotNerf, menu=menu)
            self.speedChat[2:2] = [self.sellbotNerfMenu]
        return

    def removeSellbotNerfMenu(self):
        if self.sellbotNerfMenu:
            i = self.speedChat.index(self.sellbotNerfMenu)
            del self.speedChat[i]
            self.sellbotNerfMenu.destroy()
            self.sellbotNerfMenu = None
        return

    def addJellybeanJamMenu(self, phase):
        if self.jellybeanJamMenu == None:
            menu = TTSCJellybeanJamMenu.TTSCJellybeanJamMenu(phase)
            self.jellybeanJamMenu = SCMenuHolder(OTPLocalizer.SCMenuJellybeanJam, menu=menu)
            self.speedChat[2:2] = [self.jellybeanJamMenu]
        return

    def removeJellybeanJamMenu(self):
        if self.jellybeanJamMenu:
            i = self.speedChat.index(self.jellybeanJamMenu)
            del self.speedChat[i]
            self.jellybeanJamMenu.destroy()
            self.jellybeanJamMenu = None
        return

    def addHalloweenMenu(self):
        if self.halloweenMenu == None:
            menu = TTSCHalloweenMenu()
            self.halloweenMenu = SCMenuHolder(OTPLocalizer.SCMenuHalloween, menu=menu)
            self.speedChat[2:2] = [self.halloweenMenu]
        return

    def removeHalloweenMenu(self):
        if self.halloweenMenu:
            i = self.speedChat.index(self.halloweenMenu)
            del self.speedChat[i]
            self.halloweenMenu.destroy()
            self.halloweenMenu = None
        return

    def addWinterMenu(self, carol = False):
        if self.winterMenu == None:
            menu = TTSCWinterMenu(carol)
            self.winterMenu = SCMenuHolder(OTPLocalizer.SCMenuWinter, menu=menu)
            self.speedChat[2:2] = [self.winterMenu]
        return

    def removeWinterMenu(self):
        if self.winterMenu:
            i = self.speedChat.index(self.winterMenu)
            del self.speedChat[i]
            self.winterMenu.destroy()
            self.winterMenu = None
        return

    def addCarolMenu(self):
        self.removeWinterMenu()
        self.addWinterMenu(carol=True)

    def removeCarolMenu(self):
        self.removeWinterMenu()

    def addWhiteList(self):
        if self.whiteList == None:
            from toontown.chat.TTSCWhiteListTerminal import TTSCWhiteListTerminal
            self.whiteList = TTSCWhiteListTerminal(4, self)
            self.speedChat[1:1] = [self.whiteList]
        return

    def removeWhiteList(self):
        if self.whiteList:
            i = self.speedChat.index(self.whiteList)
            del self.speedChat[i]
            self.whiteList.destroy()
            self.whiteList = None
        return

    def addSellbotInvasionMenu(self):
        if self.sellbotInvasionMenu == None:
            menu = TTSCSellbotInvasionMenu()
            self.sellbotInvasionMenu = SCMenuHolder(OTPLocalizer.SCMenuSellbotInvasion, menu=menu)
            self.speedChat[2:2] = [self.sellbotInvasionMenu]
        return

    def removeSellbotInvasionMenu(self):
        if self.sellbotInvasionMenu:
            i = self.speedChat.index(self.sellbotInvasionMenu)
            del self.speedChat[i]
            self.sellbotInvasionMenu.destroy()
            self.sellbotInvasionMenu = None
        return

    def addSellbotFieldOfficeMenu(self):
        if self.sellbotFieldOfficeMenu == None:
            menu = TTSCSellbotFieldOfficeMenu()
            self.sellbotFieldOfficeMenu = SCMenuHolder(OTPLocalizer.SCMenuFieldOffice, menu=menu)
            self.speedChat[2:2] = [self.sellbotFieldOfficeMenu]
        return

    def removeSellbotFieldOfficeMenu(self):
        if self.sellbotFieldOfficeMenu:
            i = self.speedChat.index(self.sellbotFieldOfficeMenu)
            del self.speedChat[i]
            self.sellbotFieldOfficeMenu.destroy()
            self.sellbotFieldOfficeMenu = None
        return

    def addIdesOfMarchMenu(self):
        if self.idesOfMarchMenu == None:
            menu = TTSCIdesOfMarchMenu()
            self.idesOfMarchMenu = SCMenuHolder(OTPLocalizer.SCMenuIdesOfMarch, menu=menu)
            self.speedChat[2:2] = [self.idesOfMarchMenu]
        return

    def removeIdesOfMarchMenu(self):
        if self.idesOfMarchMenu:
            i = self.speedChat.index(self.idesOfMarchMenu)
            del self.speedChat[i]
            self.idesOfMarchMenu.destroy()
            self.idesOfMarchMenu = None
        return

    def addMagicWordsMenu(self):
        if self.magicWordsMenu == None:
            menu = TTSCMagicWordsMenu()
            self.magicWordsMenu = SCMenuHolder(OTPLocalizer.SCMenuMagicWords, menu=menu)
            self.speedChat[2:2] = [self.magicWordsMenu]
        return

    def addWinterVPMenu(self):
        # Don't create menu in retro mode
        if not retro and self.winterVpMenu == None:
            menu = SCMenu()
            menu.rebuildFromStructure(winterVpMenuStructure)
            self.winterVpMenu = SCMenuHolder(OTPLocalizer.SCMenuWinterVPBattle, menu=menu)
            self.speedChat[2:2] = [self.winterVpMenu]
        return

    def removeWinterVPMenu(self):
        if self.winterVpMenu:
            i = self.speedChat.index(self.winterVpMenu)
            del self.speedChat[i]
            self.winterVpMenu.destroy()
            self.winterVpMenu = None
        return
