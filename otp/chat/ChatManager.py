from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM
from direct.fsm import State
from direct.showbase import DirectObject

from otp.chat.ChatGlobals import isExclaim, removeExclaimPrefix
from otp.login import SecretFriendsInfoPanel
from otp.otpbase import OTPLocalizer
from otp.otpbase.PythonUtil import deprecated
from toontown.toonbase import HotkeySettings

ChatEvent = 'ChatEvent'
NormalChatEvent = 'NormalChatEvent'
SCChatEvent = 'SCChatEvent'
SCCustomChatEvent = 'SCCustomChatEvent'
SCEmoteChatEvent = 'SCEmoteChatEvent'
OnScreen = 0
OffScreen = 1
Thought = 2
Exclaim = 3
ThoughtPrefix = '.'

def isThought(message):
    if len(message) == 0:
        return 0
    elif message.find(ThoughtPrefix, 0, len(ThoughtPrefix)) >= 0:
        return 1
    else:
        return 0


def removeThoughtPrefix(message):
    if isThought(message):
        return message[len(ThoughtPrefix):]
    else:
        return message


class ChatManager(DirectObject.DirectObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('ChatManager')
    execChat = base.config.GetBool('exec-chat', False)

    def __init__(self, cr, localAvatar):
        self.cr = cr
        self.localAvatar = localAvatar
        self.wantBackgroundFocus = 0
        self.__scObscured = 0
        self.__normalObscured = 0
        self.openChatWarning = None
        self.paidNoParentPassword = None
        self.activateChatGui = None
        self.chatMoreInfo = None
        self.key = None
        self.fsm = ClassicFSM.ClassicFSM('chatManager', [State.State('off', self.enterOff, self.exitOff),
         State.State('mainMenu', self.enterMainMenu, self.exitMainMenu),
         State.State('speedChat', self.enterSpeedChat, self.exitSpeedChat),
         State.State('normalChat', self.enterNormalChat, self.exitNormalChat),
         State.State('whisper', self.enterWhisper, self.exitWhisper),
         State.State('whisperChat', self.enterWhisperChat, self.exitWhisperChat),
         State.State('whisperChatPlayer', self.enterWhisperChatPlayer, self.exitWhisperChatPlayer),
         State.State('whisperSpeedChat', self.enterWhisperSpeedChat, self.exitWhisperSpeedChat),
         State.State('whisperSpeedChatPlayer', self.enterWhisperSpeedChatPlayer, self.exitWhisperSpeedChatPlayer),
         State.State('openChatWarning', self.enterOpenChatWarning, self.exitOpenChatWarning),
         State.State('noFriendsWarning', self.enterNoFriendsWarning, self.exitNoFriendsWarning),
         State.State('otherDialog', self.enterOtherDialog, self.exitOtherDialog),
         State.State('activateChat', self.enterActivateChat, self.exitActivateChat),
         State.State('chatMoreInfo', self.enterChatMoreInfo, self.exitChatMoreInfo),
         State.State('whiteListOpenChat', self.enterWhiteListOpenChat, self.exitWhiteListOpenChat),
         State.State('whiteListAvatarChat', self.enterWhiteListAvatarChat, self.exitWhiteListAvatarChat),
         State.State('whiteListPlayerChat', self.enterWhiteListPlayerChat, self.exitWhiteListPlayerChat)], 'off', 'off')
        self.fsm.enterInitialState()

    def delete(self):
        self.ignoreAll()
        del self.fsm
        if hasattr(self.chatInputNormal, 'destroy'):
            self.chatInputNormal.destroy()
        self.chatInputNormal.delete()
        del self.chatInputNormal
        self.chatInputSpeedChat.delete()
        del self.chatInputSpeedChat
        if self.openChatWarning:
            self.openChatWarning.destroy()
            self.openChatWarning = None
        if self.activateChatGui:
            self.activateChatGui.destroy()
            self.activateChatGui = None
        if self.chatMoreInfo:
            self.chatMoreInfo.destroy()
            self.chatMoreInfo = None
        del self.localAvatar
        del self.cr

    @deprecated("Remove with new Chat bar")
    def obscure(self, normal, sc):
        return
        self.__scObscured = sc
        if self.__scObscured:
            self.scButton.hide()
        self.__normalObscured = normal
        if self.__normalObscured:
            self.normalButton.hide()

    def isObscured(self):
        return (self.__normalObscured, self.__scObscured)

    def stop(self):
        self.fsm.request('off')
        self.ignoreAll()

    def start(self):
        self.fsm.request('mainMenu')

    def announceChat(self):
        messenger.send(ChatEvent)

    def announceSCChat(self):
        messenger.send(SCChatEvent)
        self.announceChat()

    def sendChatString(self, message):
        chatFlags = CFSpeech | CFTimeout
        if base.cr.wantSwitchboardHacks:
            from otp.switchboard import badwordpy
            badwordpy.init('', '')
            message = badwordpy.scrub(message)
        if isThought(message):
            message = removeThoughtPrefix(message)
            chatFlags = CFThought
        elif isExclaim(message):
            message = removeExclaimPrefix(message)
            chatFlags = CFExclaim | CFTimeout
        messenger.send(NormalChatEvent)
        self.announceChat()

    def sendWhisperString(self, message, whisperAvatarId):
        pass

    def sendSCChatMessage(self, msgIndex, displayType=0):
        base.talkAssistant.sendOpenSpeedChat(1, msgIndex, displayType)

    def sendSCWhisperMessage(self, msgIndex, whisperAvatarId):
        base.talkAssistant.sendAvatarWhisperSpeedChat(1, msgIndex, whisperAvatarId)

    def sendSCCustomChatMessage(self, msgIndex, displayType=0):
        base.talkAssistant.sendOpenSpeedChat(3, msgIndex, displayType)

    def sendSCCustomWhisperMessage(self, msgIndex, whisperAvatarId):
        base.talkAssistant.sendAvatarWhisperSpeedChat(3, msgIndex, whisperAvatarId)

    def sendSCEmoteChatMessage(self, emoteId):
        base.talkAssistant.sendOpenSpeedChat(2, emoteId)

    def sendSCEmoteWhisperMessage(self, emoteId, whisperAvatarId):
        base.talkAssistant.sendAvatarWhisperSpeedChat(2, emoteId, whisperAvatarId)

    def enterOff(self):
        self.ignoreAll()

    def exitOff(self):
        pass

    def enterMainMenu(self):
        self.checkObscurred()
        if self.localAvatar.canChat() or self.cr.wantMagicWords:
            if self.wantBackgroundFocus:
                self.chatInputNormal.chatEntry['backgroundFocus'] = 1
            self.acceptOnce('enterNormalChat', self.fsm.request, ['normalChat'])

    def checkObscurred(self):
        if not self.__scObscured and self.qtButton.isHidden():
            self.scButton.show()
            self.chatBar.reparentTo(base.a2dTopLeft)
        if not self.__normalObscured:
            self.normalButton.show()
            self.chatBar.reparentTo(base.a2dTopLeft)

    def exitMainMenu(self):
        self.chatBar.reparentTo(hidden)
        self.ignore('enterNormalChat')
        if self.wantBackgroundFocus:
            self.chatInputNormal.chatEntry['backgroundFocus'] = 0

    def whisperTo(self, avatarName, avatarId, playerId = None, reply = False):
        self.fsm.request('whisper', [avatarName, avatarId, playerId, reply])

    def noWhisper(self):
        self.fsm.request('mainMenu')

    def handleWhiteListSelect(self):
        self.fsm.request('whiteListOpenChat')

    def enterWhiteListOpenChat(self):
        self.checkObscurred()
        if self.wantBackgroundFocus:
            self.chatInputNormal.chatEntry['backgroundFocus'] = 0
        base.localAvatar.chatMgr.chatInputWhiteList.activateByData()

    def exitWhiteListOpenChat(self):
        pass

    def enterWhiteListAvatarChat(self, receiverId):
        if self.wantBackgroundFocus:
            self.chatInputNormal.chatEntry['backgroundFocus'] = 0
        base.localAvatar.chatMgr.chatInputWhiteList.activateByData(receiverId, 0)

    def exitWhiteListAvatarChat(self):
        pass

    def enterWhiteListPlayerChat(self, receiverId):
        if self.wantBackgroundFocus:
            self.chatInputNormal.chatEntry['backgroundFocus'] = 0
        base.localAvatar.chatMgr.chatInputWhiteList.activateByData(receiverId, 1)

    def exitWhiteListPlayerChat(self):
        pass

    def enterWhisper(self, avatarName, avatarId, playerId = None, reply = False):
        if self.chatInputWhiteList.getCurrentOrNextState() == 'AllChat':
            self.chatInputWhiteList.requestMode('Inactive')

        self.whisperScButton['extraArgs'] = [avatarName, avatarId, playerId]
        self.whisperButton['extraArgs'] = [avatarName, avatarId, playerId]
        playerName = None
        chatToToon = 1
        online = base.cr.getAvatarVisibility(avatarId, forceVisibility = reply)
        avatarUnderstandable = config.GetBool('force-avatar-understandable', 0)
        playerUnderstandable = config.GetBool('force-player-understandable', 0)
        av = None
        if avatarId:
            av = self.cr.identifyAvatar(avatarId)
        if av != None:
            avatarUnderstandable = av.isUnderstandable()
        if playerId:
            if playerId in base.cr.playerFriendsManager.playerId2Info:
                playerInfo = base.cr.playerFriendsManager.playerId2Info.get(playerId)
                playerName = playerInfo.playerName
                online = 1
                playerUnderstandable = playerInfo.understandableYesNo
                if playerUnderstandable or not avatarId:
                    chatToToon = 0
        if chatToToon:
            chatName = avatarName
        else:
            chatName = playerName
        normalButtonObscured, scButtonObscured = self.isObscured()
        if (avatarUnderstandable or playerUnderstandable) and online and not normalButtonObscured:
            self.whisperButton['state'] = 'normal'
            self.enablewhisperButton()
        else:
            self.whisperButton['state'] = 'inactive'
            self.disablewhisperButton()
        if online:
            self.whisperScButton['state'] = 'normal'
            self.changeFrameText(OTPLocalizer.ChatManagerWhisperToName % chatName)
        else:
            self.whisperScButton['state'] = 'inactive'
            self.changeFrameText(OTPLocalizer.ChatManagerWhisperOffline % chatName)
        self.whisperFrame.show()
        self.refreshWhisperFrame()
        if avatarUnderstandable or playerUnderstandable:
            if playerId and not chatToToon:
                if self.wantBackgroundFocus:
                    self.chatInputNormal.chatEntry['backgroundFocus'] = 1
                self.acceptOnce('enterNormalChat', self.fsm.request, ['whisperChatPlayer', [avatarName, playerId]])
            elif online and chatToToon:
                if self.wantBackgroundFocus:
                    self.chatInputNormal.chatEntry['backgroundFocus'] = 1
                self.acceptOnce('enterNormalChat', self.fsm.request, ['whisperChat', [avatarName, avatarId]])
        if base.cr.config.GetBool('force-typed-whisper-enabled', 0):
            self.whisperButton['state'] = 'normal'
            self.enablewhisperButton()
        return

    def disablewhisperButton(self):
        pass

    def enablewhisperButton(self):
        pass

    def refreshWhisperFrame(self):
        pass

    def changeFrameText(self, newText):
        self.whisperFrame['text'] = newText

    def exitWhisper(self):
        self.whisperFrame.hide()
        self.ignore('enterNormalChat')
        self.chatInputNormal.chatEntry['backgroundFocus'] = 0

    def enterWhisperSpeedChat(self, avatarId):
        self.whisperFrame.show()
        if self.wantBackgroundFocus:
            self.chatInputNormal.chatEntry['backgroundFocus'] = 0
        self.chatInputSpeedChat.show(avatarId)

    def exitWhisperSpeedChat(self):
        self.whisperFrame.hide()
        self.chatInputSpeedChat.hide()

    def enterWhisperSpeedChatPlayer(self, playerId):
        self.whisperFrame.show()
        if self.wantBackgroundFocus:
            self.chatInputNormal.chatEntry['backgroundFocus'] = 0
        self.chatInputSpeedChat.show(playerId, 1)

    def exitWhisperSpeedChatPlayer(self):
        self.whisperFrame.hide()
        self.chatInputSpeedChat.hide()

    def enterWhisperChat(self, avatarName, avatarId):
        base.controlManager.disableAlphaNumericHotkeys = True
        result = self.chatInputNormal.activateByData(avatarId)
        return result

    def exitWhisperChat(self):
        self.acceptOnce('exitChat', self.deactivateWhisperChat)

    def deactivateWhisperChat(self):
        base.controlManager.disableAlphaNumericHotkeys = False
        self.chatInputNormal.deactivate()

    def enterWhisperChatPlayer(self, avatarName, playerId):
        playerInfo = base.cr.playerFriendsManager.getFriendInfo(playerId)
        if playerInfo:
            avatarName = playerInfo.playerName
        result = self.chatInputNormal.activateByData(playerId, 1)
        return result

    def exitWhisperChatPlayer(self):
        self.chatInputNormal.deactivate()

    def enterSpeedChat(self):
        messenger.send('enterSpeedChat')
        if not self.__scObscured and self.qtButton.isHidden():
            self.scButton.show()
        if not self.__normalObscured:
            self.normalButton.show()
            self.chatBar.reparentTo(base.a2dTopLeft)
        if self.wantBackgroundFocus:
            self.chatInputNormal.chatEntry['backgroundFocus'] = 0
        self.chatInputSpeedChat.show()

    def exitSpeedChat(self):
        self.scButton.hide()
        self.normalButton.hide()
        self.chatInputSpeedChat.hide()

    def enterNormalChat(self):
        base.controlManager.disableAlphaNumericHotkeys = True
        result = self.chatInputNormal.activateByData()
        return result

    def exitNormalChat(self):
        self.acceptOnce('exitChat', self.deactivateNormalChat)

    def deactivateNormalChat(self):
        base.controlManager.disableAlphaNumericHotkeys = False
        self.chatInputNormal.deactivate()
        self.fsm.request('mainMenu')

    def enterOpenChatWarning(self):
        self.notify.error('called enterOpenChatWarning() on parent class')

    def exitOpenChatWarning(self):
        self.notify.error('called exitOpenChatWarning() on parent class')

    def enterNoFriendsWarning(self):
        self.notify.error('called enterNoFriendsWarning() on parent class')

    def exitNoFriendsWarning(self):
        self.notify.error('called exitNoFriendsWarning() on parent class')

    def enterActivateChat(self):
        self.notify.error('called enterActivateChat() on parent class')

    def exitActivateChat(self):
        self.notify.error('called exitActivateChat() on parent class')

    def enterOtherDialog(self):
        pass

    def exitOtherDialog(self):
        pass

    def enterChatMoreInfo(self):
        if self.chatMoreInfo == None:
            self.chatMoreInfo = SecretFriendsInfoPanel.SecretFriendsInfoPanel('secretFriendsInfoDone')
        self.chatMoreInfo.show()
        self.accept('secretFriendsInfoDone', self.__secretFriendsInfoDone)
        return

    def exitChatMoreInfo(self):
        self.chatMoreInfo.hide()
        self.ignore('secretFriendsInfoDone')

    def __handleLeaveToPayCancel(self):
        self.fsm.request('mainMenu')

    def __secretFriendsInfoDone(self):
        self.fsm.request('activateChat')

    def disableBackgroundFocus(self):
        self.wantBackgroundFocus = False
        self.chatInputNormal.chatEntry['backgroundFocus'] = False
        if self.key:
            self.ignore(self.key)

    def setBackgroundFocus(self, state, realtime=False):
        self.wantBackgroundFocus = state
        if realtime:
            self.chatInputNormal.chatEntry['backgroundFocus'] = state
            if not state:
                self.key = HotkeySettings.Chat.getPressed()
                self.accept(self.key, self.openChat)
            else:
                self.ignore(self.key)

    def openChat(self):
        messenger.send('wakeup')
        messenger.send('enterNormalChat')
