from direct.directnotify import DirectNotifyGlobal
from panda3d.core import *

from direct.fsm.State import State
from direct.gui.DirectGui import *

from otp.chat import ChatManager
from otp.otpbase import OTPGlobals
from otp.otpbase import OTPLocalizer
from otp.otpgui import OTPGUIUtils
from toontown.toonbase import TTLocalizer, ToontownGlobals
from .ChatLog import ChatLog
from .TTChatInputNormal import TTChatInputNormal
from .TTChatInputQuickTalker import TTChatInputQuickTalker
from .TTChatInputSpeedChat import TTChatInputSpeedChat
from .TTChatInputWhiteList import TTChatInputWhiteList
from ..toontowngui.AnimatedButton import AnimatedButton

MENU_SPEEDCHAT = 0
MENU_EMOTES = 1
MENU_UNITES = 2


class HackedDirectRadioButton(DirectCheckButton):

    def __init__(self, parent = None, **kw):
        optiondefs = ()
        self.defineoptions(kw, optiondefs)
        DirectCheckButton.__init__(self, parent)
        self.initialiseoptions(HackedDirectRadioButton)

    def commandFunc(self, event):
        if self['indicatorValue']:
            self['indicatorValue'] = 0
        DirectCheckButton.commandFunc(self, event)


class ToontownChatManager(ChatManager.ChatManager):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToontownChatManager')

    def __init__(self, cr, localAvatar):
        gui = loader.loadModel('phase_3.5/models/gui/chat_input_gui')

        self.chatBar = hidden.attachNewNode('actionbar')

        chatBarMdl = loader.loadModel('phase_3.5/models/gui/ttoff_m_gui_chatPanel')
        self.chatBar.setPos(0.41, 0, -0.05)

        self.normalButton = AnimatedButton(
            image = (chatBarMdl.find('**/chatbar_chat_normal'), chatBarMdl.find('**/chatbar_chat_hover'), chatBarMdl.find('**/chatbar_chat_normal')),
            pos = (-0.36, 0, 0), parent = self.chatBar, scale = .08, relief = None,
            text = ('', '', OTPLocalizer.ChatManagerChat,),
            text_align = TextNode.ACenter,
            text_scale = 0.6,
            text_fg = (1.0, 1.0, 1.0, 1.0),
            text_shadow = (0, 0, 0, 0.7),
            text_pos = (0, -1),
            textMayChange = 0,
            sortOrder = DGG.FOREGROUND_SORT_INDEX, command = self.__normalButtonPressed)
        self.openScSfx = loader.loadSfx('phase_3.5/audio/sfx/GUI_quicktalker.ogg')
        self.openScSfx.setVolume(0.6)
        self.scButton = AnimatedButton(
            image = (chatBarMdl.find('**/chatbar_speedchat_normal'), chatBarMdl.find('**/chatbar_speedchat_hover')),
            pos = (-.26, 0, 0), parent = self.chatBar, scale = .08, relief = None,
            text = ('', '', OTPLocalizer.GlobalSpeedChatName),
            text_align = TextNode.ACenter,
            text_scale = 0.6,
            text_fg = (1.0, 1.0, 1.0, 1.0),
            text_shadow = (0, 0, 0, 0.7),
            text_pos = (0, -1),
            textMayChange = 0,
            sortOrder = DGG.FOREGROUND_SORT_INDEX,
            command = self.__scButtonPressed, clickSound = self.openScSfx)

        self.unitesButton = AnimatedButton(
            image = (
                chatBarMdl.find('**/chatbar_unites_normal'), chatBarMdl.find('**/chatbar_unites_hover'),
                chatBarMdl.find('**/chatbar_unites_hover'), chatBarMdl.find('**/chatbar_unites_disabled'),
            ),
            pos = (-.16, 0, 0), parent = self.chatBar, scale = .08, relief = None,
            text = ('', '', TTLocalizer.ChatBarUnites, ''),
            text_align = TextNode.ACenter,
            text_scale = 0.6,
            text_fg = (1.0, 1.0, 1.0, 1.0),
            text_shadow = (0, 0, 0, 0.7),
            text_pos = (0, -1),
            textMayChange = 0,
            sortOrder = DGG.FOREGROUND_SORT_INDEX,
            command = self.__unitesButtonPressed, clickSound = self.openScSfx
        )
        self.emotesButton = AnimatedButton(
            image = (
                chatBarMdl.find('**/chatbar_emote_normal'), chatBarMdl.find('**/chatbar_emote_hover'),
            ),
            pos = (-.06, 0, 0), parent = self.chatBar, scale = .08, relief = None,
            text = ('', '', TTLocalizer.ChatBarEmotes),
            text_align = TextNode.ACenter,
            text_scale = 0.6,
            text_fg = (1.0, 1.0, 1.0, 1.0),
            text_shadow = (0, 0, 0, 0.7),
            text_pos = (0, -1),
            textMayChange = 0,
            sortOrder = DGG.FOREGROUND_SORT_INDEX,
            command = self.__emotesButtonPressed, clickSound = self.openScSfx
        )
        self.logButton = AnimatedButton(
            image = (
                chatBarMdl.find('**/chatbar_chatlog_normal'), chatBarMdl.find('**/chatbar_chatlog_hover'),
            ),
            pos = (0.04, 0, 0), parent = self.chatBar, scale = .08, relief = None,
            text = ('', '', TTLocalizer.ChatBarChatLog),
            text_align = TextNode.ACenter,
            text_scale = 0.6,
            text_fg = (1.0, 1.0, 1.0, 1.0),
            text_shadow = (0, 0, 0, 0.7),
            text_pos = (0, -1),
            textMayChange = 0,
            sortOrder = DGG.FOREGROUND_SORT_INDEX, command = self.__chatLogButtonPressed
        )
        self.whisperFrame = DirectFrame(parent = base.a2dTopLeft, relief = None, image = DGG.getDefaultDialogGeom(),
                                        image_scale = (0.45, 0.45, 0.45), image_color = OTPGlobals.GlobalDialogColor,
                                        pos = (0.933333, 0, -0.246), text = OTPLocalizer.ChatManagerWhisperTo,
                                        text_wordwrap = 7.0, text_scale = TTLocalizer.TCMwhisperFrame,
                                        text_fg = Vec4(0, 0, 0, 1), text_pos = (0, 0.14), textMayChange = 1,
                                        sortOrder = DGG.FOREGROUND_SORT_INDEX)
        self.whisperFrame.hide()
        self.whisperButton = DirectButton(parent = self.whisperFrame, image = (
            gui.find('**/ChtBx_ChtBtn_UP'), gui.find('**/ChtBx_ChtBtn_DN'), gui.find('**/ChtBx_ChtBtn_RLVR')),
                                          pos = (-0.125, 0, -0.1), scale = 1.179, relief = None,
                                          image_color = Vec4(1, 1, 1, 1), text = ('',
                                                                                  OTPLocalizer.ChatManagerChat,
                                                                                  OTPLocalizer.ChatManagerChat,
                                                                                  ''),
                                          image3_color = Vec4(0.6, 0.6, 0.6, 0.6),
                                          text_scale = TTLocalizer.TCMwhisperButton, text_fg = (0, 0, 0, 1),
                                          text_pos = (0, -0.09), textMayChange = 0,
                                          command = self.__whisperButtonPressed)
        self.whisperScButton = DirectButton(parent = self.whisperFrame, image = (
            gui.find('**/ChtBx_ChtBtn_UP'), gui.find('**/ChtBx_ChtBtn_DN'), gui.find('**/ChtBx_ChtBtn_RLVR')),
                                            pos = (0.0, 0, -0.1), scale = 1.179, relief = None,
                                            image_color = Vec4(0.75, 1, 0.6, 1), text = ('',
                                                                                         OTPLocalizer.GlobalSpeedChatName,
                                                                                         OTPLocalizer.GlobalSpeedChatName,
                                                                                         ''),
                                            image3_color = Vec4(0.6, 0.6, 0.6, 0.6),
                                            text_scale = TTLocalizer.TCMwhisperScButton, text_fg = (0, 0, 0, 1),
                                            text_pos = (0, -0.09), textMayChange = 0,
                                            command = self.__whisperScButtonPressed)
        self.whisperCancelButton = DirectButton(parent = self.whisperFrame, image = (
            gui.find('**/CloseBtn_UP'), gui.find('**/CloseBtn_DN'), gui.find('**/CloseBtn_Rllvr')), pos = (0.125, 0, -0.1),
                                                scale = 1.179, relief = None, text = (
                '', OTPLocalizer.ChatManagerCancel, OTPLocalizer.ChatManagerCancel), text_scale = 0.05,
                                                text_fg = (0, 0, 0, 1), text_pos = (0, -0.09), textMayChange = 0,
                                                command = self.__whisperCancelPressed)
        self.qtButton = DirectButton(parent = base.a2dTopLeft,
                                     image = (gui.find('**/ChtBx_ChtBtn_UP'), gui.find('**/ChtBx_ChtBtn_DN'),
                                              gui.find('**/ChtBx_ChtBtn_RLVR')), pos = TTLocalizer.TCMscButtonPos,
                                     scale = 1.179,
                                     relief = None, image_color = Vec4(0.75, 1, 0.75, 1),
                                     text = ('', TTLocalizer.QuickTalkerTitle, TTLocalizer.QuickTalkerTitle),
                                     text_scale = 0.06, text_fg = Vec4(1, 1, 1, 1),
                                     text_shadow = Vec4(0, 0, 0, 1), text_pos = (0, -0.09),
                                     text_font = ToontownGlobals.getInterfaceFont(),
                                     clickSound = DGG.getDefaultClickSound(),
                                     rolloverSound = DGG.getDefaultRolloverSound(),
                                     command = self.__qtButtonPressed)
        self.qtButton.hide()
        self.chatInputQuickTalker = TTChatInputQuickTalker(self)
        gui.removeNode()
        ChatManager.ChatManager.__init__(self, cr, localAvatar)
        self.fsm.addState(State('quickTalker', self.enterQuickTalker, self.exitQuickTalker, [
            'mainMenu']))
        self.defaultToWhiteList = base.config.GetBool('white-list-is-default', 1)
        self.chatInputSpeedChat = TTChatInputSpeedChat(self)
        self.normalPos = Vec3(0.34, 0, -0.144)
        self.whisperPos = Vec3(0.0, 0, 0.71)
        self.speedChatPlusPos = Vec3(-0.1, 0, 0.85)
        self.chatInputWhiteList = TTChatInputWhiteList()
        if self.defaultToWhiteList:
            self.chatInputNormal = self.chatInputWhiteList
            self.chatInputNormal.setPos(self.normalPos)
            self.chatInputNormal.desc = 'chatInputNormal'
        else:
            self.chatInputNormal = TTChatInputNormal(self)
        self.chatInputWhiteList.setPos(self.speedChatPlusPos)
        self.chatInputWhiteList.reparentTo(base.a2dTopLeft)
        self.chatInputWhiteList.desc = 'chatInputWhiteList'
        self.setBackgroundFocus(base.controlManager.getChatDisabled(), True)
        self.chatLogNode = self.chatInputNormal.attachNewNode('chatlog')
        self.chatInputNormal.setBin('gui-popup', 100)
        self.chatLogNode.setBin('gui-popup', 0)
        self.chatLog = ChatLog(self)
        self.chatLog.reparentTo(self.chatLogNode)
        self.chatLogNode.setPos(-.196, 0, .05)
        self.chatLogNode.setScale(1.0)
        chatBarMdl.removeNode()
        self.fsm.addState(State('emotes', self.enterEmotes, self.exitEmotes))
        self.fsm.addState(State('unites', self.enterUnites, self.exitUnites))
        return

    def delete(self):
        ChatManager.ChatManager.delete(self)
        loader.unloadModel('phase_3.5/models/gui/chat_input_gui')
        self.normalButton.destroy()
        del self.normalButton
        self.scButton.destroy()
        del self.scButton
        del self.openScSfx
        self.whisperFrame.destroy()
        del self.whisperFrame
        self.whisperButton.destroy()
        del self.whisperButton
        self.whisperScButton.destroy()
        del self.whisperScButton
        self.whisperCancelButton.destroy()
        del self.whisperCancelButton
        self.chatInputWhiteList.destroy()
        del self.chatInputWhiteList
        self.chatLog.destroy()
        del self.chatLog
        self.chatLogNode.removeNode()
        del self.chatLogNode
        self.chatInputQuickTalker.delete()
        del self.chatInputQuickTalker
        self.qtButton.destroy()
        del self.qtButton
        self.ignoreAll()

    def sendSCResistanceChatMessage(self, textId):
        messenger.send('chatUpdateSCResistance', [textId])
        self.announceSCChat()

    def sendSCSingingChatMessage(self, textId):
        messenger.send('chatUpdateSCSinging', [textId])
        self.announceSCChat()

    def sendSCSingingWhisperMessage(self, textId):
        pass

    def sendSCToontaskChatMessage(self, taskId, toNpcId, toonProgress, msgIndex, displayType = 0):
        messenger.send('chatUpdateSCToontask', [taskId,
                                                toNpcId,
                                                toonProgress,
                                                msgIndex,
                                                displayType])
        self.announceSCChat()

    def sendSCToontaskWhisperMessage(self, taskId, toNpcId, toonProgress, msgIndex, whisperAvatarId):
        messenger.send('whisperUpdateSCToontask', [taskId,
                                                   toNpcId,
                                                   toonProgress,
                                                   msgIndex,
                                                   whisperAvatarId])

    def enterOpenChatWarning(self):
        if self.openChatWarning == None:
            buttons = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
            buttonImage = (
                buttons.find('**/ChtBx_OKBtn_UP'), buttons.find('**/ChtBx_OKBtn_DN'), buttons.find('**/ChtBx_OKBtn_Rllvr'))
            self.openChatWarning = DirectFrame(parent = aspect2dp, pos = (0.0, 0.1, 0.2), relief = None,
                                               image = DGG.getDefaultDialogGeom(),
                                               image_color = OTPGlobals.GlobalDialogColor,
                                               image_scale = (1.2, 1.0, 1.4), text = OTPLocalizer.OpenChatWarning,
                                               text_wordwrap = 19, text_scale = TTLocalizer.TCMopenChatWarning,
                                               text_pos = (0.0, 0.575), textMayChange = 0)
            DirectButton(self.openChatWarning, image = buttonImage, relief = None,
                         text = OTPLocalizer.OpenChatWarningOK, text_scale = 0.05, text_pos = (0.0, -0.1),
                         textMayChange = 0, pos = (0.0, 0.0, -0.55), command = self.__handleOpenChatWarningOK)
            buttons.removeNode()
        self.openChatWarning.show()
        normObs, scObs = self.isObscured()
        if not scObs and self.qtButton.isHidden():
            self.scButton.show()
        if not normObs:
            self.normalButton.show()

    def enterMainMenu(self):
        self.setBackgroundFocus(base.controlManager.getChatDisabled(), True)
        self.chatInputNormal.setPos(self.normalPos)
        self.chatInputWhiteList.reparentTo(base.a2dTopLeft)
        if self.chatInputWhiteList.isActive():
            self.notify.debug('enterMainMenu calling checkObscured')
            ChatManager.ChatManager.checkObscurred(self)
        else:
            ChatManager.ChatManager.enterMainMenu(self)

    def exitOpenChatWarning(self):
        self.openChatWarning.hide()
        self.scButton.hide()

    def __chatLogButtonPressed(self):
        if not base.localAvatar.tutorialAck:
            return
        self.__normalButtonPressed()
        base.controlManager.disableAlphaNumericHotkeys = False
        self.chatInputNormal.chatEntry['focus'] = 0

    def __normalButtonPressed(self):
        if base.config.GetBool('want-qa-regression', 0):
            self.notify.info('QA-REGRESSION: CHAT: Speedchat Plus')
        messenger.send('wakeup')
        if not base.localAvatar.tutorialAck:
            return
        if base.cr.productName in ['DisneyOnline-US', 'ES']:
            if base.cr.whiteListChatEnabled:
                self.fsm.request('normalChat')
            elif not base.localAvatar.canChat():
                self.fsm.request('openChatWarning')
            else:
                self.fsm.request('normalChat')
        elif base.cr.productName == 'Terra-DMC':
            if not base.localAvatar.canChat():
                self.fsm.request('openChatWarning')
            else:
                self.fsm.request('normalChat')
        elif base.cr.productName in ['DisneyOnline-UK',
                                     'DisneyOnline-AP',
                                     'JP',
                                     'BR',
                                     'FR']:
            if base.cr.whiteListChatEnabled:
                self.fsm.request('normalChat')
            elif not base.localAvatar.canChat():
                self.fsm.request('openChatWarning')
            else:
                self.fsm.request('normalChat')
        else:
            print('ChatManager: productName: %s not recognized' % base.cr.productName)

    def __scButtonPressed(self):
        messenger.send('wakeup')
        if not base.localAvatar.tutorialAck:
            return
        if self.fsm.getCurrentState().getName() == 'speedChat':
            self.fsm.request('mainMenu')
        else:
            self.fsm.request('speedChat')

    def __emotesButtonPressed(self):
        messenger.send('wakeup')
        if not base.localAvatar.tutorialAck:
            return
        if self.fsm.getCurrentState().getName() == 'emotes':
            self.fsm.request('mainMenu')
        else:
            self.fsm.request('emotes')

    def __unitesButtonPressed(self):
        messenger.send('wakeup')
        if not base.localAvatar.tutorialAck:
            return
        if self.fsm.getCurrentState().getName() == 'unites':
            self.fsm.request('mainMenu')
        else:
            self.fsm.request('unites')

    def enterEmotes(self):
        messenger.send('enterSpeedChat')
        if not self._ChatManager__scObscured and self.qtButton.isHidden():
            self.scButton.show()
        if not self._ChatManager__normalObscured:
            self.normalButton.show()
            self.chatBar.reparentTo(base.a2dTopLeft)
        if self.wantBackgroundFocus:
            self.chatInputNormal.chatEntry['backgroundFocus'] = 0
        self.chatInputSpeedChat.show(menu = MENU_EMOTES)

    def exitEmotes(self):
        self.chatInputSpeedChat.hide()

    def enterUnites(self):
        messenger.send('enterSpeedChat')
        if not self._ChatManager__scObscured and self.qtButton.isHidden():
            self.scButton.show()
        if not self._ChatManager__normalObscured:
            self.normalButton.show()
            self.chatBar.reparentTo(base.a2dTopLeft)
        if self.wantBackgroundFocus:
            self.chatInputNormal.chatEntry['backgroundFocus'] = 0
        self.chatInputSpeedChat.show(menu = MENU_UNITES)

    def exitUnites(self):
        self.chatInputSpeedChat.hide()

    def __whisperButtonPressed(self, avatarName, avatarId, playerId):
        messenger.send('wakeup')
        playerInfo = None
        if playerId:
            playerInfo = base.cr.playerFriendsManager.getFriendInfo(playerId)
        if playerInfo:
            if playerInfo.understandableYesNo:
                self.fsm.request('whisperChatPlayer', [avatarName, playerId])
                return
        if avatarId:
            self.fsm.request('whisperChat', [avatarName, avatarId])
        return

    def enterNormalChat(self):
        result = ChatManager.ChatManager.enterNormalChat(self)
        self.chatBar.reparentTo(hidden)

        OTPGUIUtils.Animations.slideDown(self.chatInputNormal, finalZ = -0.146, startZ = .1, intensity = 0.1).start()
        if result is None:
            self.notify.warning('something went wrong in enterNormalChat, falling back to main menu')
            self.fsm.request('mainMenu')
        return

    def enterWhisperChatPlayer(self, avatarName, playerId):
        result = ChatManager.ChatManager.enterWhisperChatPlayer(self, avatarName, playerId)
        self.chatInputNormal.setPos(self.whisperPos)
        self.chatInputWhiteList.reparentTo(aspect2dp)
        if result == None:
            self.notify.warning('something went wrong in enterWhisperChatPlayer, falling back to main menu')
            self.fsm.request('mainMenu')
        return

    def enterWhisperChat(self, avatarName, avatarId):
        result = ChatManager.ChatManager.enterWhisperChat(self, avatarName, avatarId)
        self.chatInputNormal.setPos(self.whisperPos)
        self.chatInputWhiteList.reparentTo(aspect2dp)
        if result == None:
            self.notify.warning('something went wrong in enterWhisperChat, falling back to main menu')
            self.fsm.request('mainMenu')

    def __whisperScButtonPressed(self, avatarName, avatarId, playerId):
        if base.config.GetBool('want-qa-regression', 0):
            self.notify.info('QA-REGRESSION: CHAT: Whisper')
        messenger.send('wakeup')
        hasManager = hasattr(base.cr, 'playerFriendsManager')
        transientFriend = 0
        if hasManager:
            transientFriend = base.cr.playerFriendsManager.askTransientFriend(avatarId)
            if transientFriend:
                playerId = base.cr.playerFriendsManager.findPlayerIdFromAvId(avatarId)
        if avatarId and not transientFriend:
            if self.fsm.getCurrentState().getName() == 'whisperSpeedChat':
                self.fsm.request('whisper', [avatarName, avatarId, playerId])
            else:
                self.fsm.request('whisperSpeedChat', [avatarId])
        elif playerId:
            if self.fsm.getCurrentState().getName() == 'whisperSpeedChatPlayer':
                self.fsm.request('whisper', [avatarName, avatarId, playerId])
            else:
                self.fsm.request('whisperSpeedChatPlayer', [playerId])

    def __whisperCancelPressed(self):
        self.fsm.request('mainMenu')
        messenger.send('exitChat')

    def __handleOpenChatWarningOK(self):
        self.fsm.request('mainMenu')

    def messageSent(self):
        pass

    def deactivateChat(self):
        pass

    def showQuickTalkerButton(self):
        self.qtButton.show()

    def hideQuickTalkerButton(self):
        self.qtButton.hide()

    def enterQuickTalker(self):
        if base.localAvatar.canChat():
            self.chatInputNormal.chatEntry['backgroundFocus'] = 0

        self.hideQuickTalkerButton()
        self.chatInputQuickTalker.show()

    def exitQuickTalker(self):
        if self.scButton.isHidden():
            self.showQuickTalkerButton()
        self.chatInputQuickTalker.hide()

    def __qtButtonPressed(self):
        self.fsm.request('quickTalker')

    def sendQTChatMessage(self, QTmessage):
        messenger.send('chatUpdateQT', [QTmessage])
