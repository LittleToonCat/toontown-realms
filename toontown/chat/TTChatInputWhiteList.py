from typing import Tuple, List, Optional, Dict, Any

from direct.gui import DirectGuiGlobals

from otp.chat.ChatInputWhiteListFrame import ChatInputWhiteListFrame
from otp.otpbase import OTPGlobals
from direct.gui.DirectGui import *
from panda3d.core import *
from otp.otpbase import OTPLocalizer
from direct.directnotify import DirectNotifyGlobal

from otp.otpgui import OTPGUIUtils
from toontown.spellbook.MagicWordIndex import magicWordIndex
from toontown.toonbase import ToontownGlobals, ClientSettings
from toontown.toontowngui.AnimatedButton import AnimatedButton
from toontown.toontowngui.ToontownScrolledFrame import ToontownScrolledFrame

SUGGESTION_FRAME_MAINPOS = (0.27, 0, -0.975)
SUGGESTION_FRAME_ARGPOS = (0.67, 0, -0.975)

class TTChatInputWhiteList(ChatInputWhiteListFrame):
    notify = DirectNotifyGlobal.directNotify.newCategory('TTChatInputWhiteList')
    TFToggleKey = base.config.GetString('true-friend-toggle-key', 'alt')
    TFToggleKeyUp = TFToggleKey + '-up'

    def __init__(self, parent = None, **kw):
        entryOptions = {'parent': self,
                        'relief': DGG.SUNKEN,
                        'scale': 0.045,
                        'frameColor': (0.9, 0.9, 0.85, 0),
                        'overflow': 1,
                        'pos': (-0.16, 0, -0.572),
                        'entryFont': OTPGlobals.getInterfaceFont(),
                        'width': 19,
                        'numLines': 1,
                        'cursorKeys': 1,
                        'backgroundFocus': 0,
                        'suppressKeys': 0,
                        'suppressMouse': 1,
                        'command': self.sendChat,
                        'failedCommand': self.sendFailed,
                        'focusInCommand': self.__focus,
                        'focusOutCommand': self.__unfocus,
                        'focus': 0,
                        'text': '',
                        'text_fg': (1, 1, 1, 1),
                        'sortOrder': DGG.FOREGROUND_SORT_INDEX
                        }
        ChatInputWhiteListFrame.__init__(self, entryOptions, parent, **kw)
        base.ttwl = self
        self.autoOff = 1
        self.sendBy = 'Data'
        self.prefilter = 0
        self.promoteWhiteList = 1
        self.typeGrabbed = 0
        self.globalState = 0
        self.muted = 0
        self.cachedArgs = None
        self.deactivate()
        gui = loader.loadModel('phase_3.5/models/gui/chat_input_gui')
        newGui = loader.loadModel('phase_3.5/models/gui/ttoff_m_gui_chatPanel')
        avPanelGui = loader.loadModel('phase_3.5/models/gui/avatar_panel_gui')
        self.chatButton = DirectButton(parent = self, image = (gui.find('**/ChtBx_ChtBtn_UP'),
                                                               gui.find('**/ChtBx_ChtBtn_DN'),
                                                               gui.find('**/ChtBx_ChtBtn_RLVR')),
                                       pos = (0.172, 0, -0.228), scale = 1.1, relief = None,
                                       text = (
                                           '', OTPLocalizer.ChatInputNormalSayIt, OTPLocalizer.ChatInputNormalSayIt),
                                       text_scale = 0.06, text_fg = Vec4(1, 1, 1, 1), text_shadow = Vec4(0, 0, 0, 1),
                                       text_pos = (0, -0.09), textMayChange = 0, command = self.chatButtonPressed)
        # TEMPORARY: HIDE CHAT BUTTON AND JUST REPLACE IT WITH THE EMOJIS BUTTON UNTIL THE TEXTURE ITSELF IS CHANGED
        # TO MAKE ROOM FOR THE EMOJI BUTTON. THIS IS ALSO OK BC THE SEND CHAT BUTTON IS BROKEN
        # (https://github.com/ttoff/issue-tracker/issues/6)
        self.chatButton.hide()
        self.cancelButton = AnimatedButton(parent = self, image = newGui.find('**/chatpanel_close'),
                                           image_scale = 0.1,
                                           pos = (-0.245, 0, -0.562), scale = 1, relief = None,
                                           text = ('', OTPLocalizer.ChatInputNormalCancel,
                                                   OTPLocalizer.ChatInputNormalCancel), text_scale = 0.06,
                                           text_fg = Vec4(1, 1, 1, 1), text_shadow = Vec4(0, 0, 0, 1),
                                           text_pos = (0, -0.09), sortOrder = 200,
                                           textMayChange = 0, command = self.cancelButtonPressed)
        self.emojisButton = AnimatedButton(parent = self, relief = None,
                                           text = ('', OTPLocalizer.ChatInputNormalEmojis), text_scale = 0.06,
                                           text_fg = Vec4(1, 1, 1, 1), text_shadow = Vec4(0, 0, 0, 1),
                                           text_pos = (0, -0.09), textMayChange = 0,
                                           pos = (0.78, 0, -0.555), image_scale = 0.1,
                                           image = (
                                               newGui.find('**/chatpanel_emojis'),
                                               newGui.find('**/chatpanel_emojis_hover')),
                                           command = self.__toggleEmojiPanel,
                                           sortOrder = 200,
                                           )
        colorPickerGui = loader.loadModel("phase_3/models/gui/ttoff_m_gui_opts_colorpicker")
        self.emojiFrame = DirectFrame(parent = self, relief = None, pos = (1.3, 0, -0.3),
                                      scale = 0.5, geom_scale = 1.1,
                                      geom = colorPickerGui.find('**/temp_bg'))
        self.emojiFrame.hide()
        self.emojiButtons = []
        emojiIcons = loader.loadModel('phase_3/models/gui/ttrm_m_gui_chat_emojis')
        pos = Point3(-.4, 0, .4)
        for emoji in base.emojis:
            emojiButton = AnimatedButton(parent = self.emojiFrame, relief = None,
                                         image = emojiIcons.find(f'**/{emoji}'),
                                         pos = pos, image_scale = 0.18, command = self.__insertEmoji,
                                         extraArgs = [emoji])
            emojiButton.bind(DirectGuiGlobals.WITHIN, self.__hoverEmoji, extraArgs = [emoji])
            emojiButton.bind(DirectGuiGlobals.WITHOUT, self.__unhoverEmoji)
            self.emojiButtons.append(emojiButton)
            pos.addX(0.2)
            if not (base.emojis.index(emoji) + 1) % 5:
                pos.setX(-.4)
                pos.addZ(-0.2)

        self.emojiLabel = DirectLabel(parent = self.emojiFrame, pos = (0, 0, -0.7), relief = DGG.FLAT,
                                      frameColor = (1, 1, 0.5, 1), frameSize = (-0.23, 0.23, -0.08, 0.1),
                                      text = '', text_scale = 0.1,
                                      text_pos = (0, -0.025, 0.02), text_fg = Vec4(0, 0, 0, 1))
        self.emojiLabel.hide()

        gui.removeNode()
        avPanelGui.removeNode()
        self.infoLabel = DirectLabel(parent = self, pos = (0.06, 0, -0.88), relief = DGG.FLAT,
                                     frameColor = (1, 1, 0.5, 1), frameSize = (-0.23, 0.23, -0.07, 0.05),
                                     text = OTPLocalizer.ChatInputNormalGlobalNotice, text_scale = 0.045,
                                     text_pos = (0, -0.025, 0.02), text_fg = Vec4(0, 0, 0, 1))
        self.infoLabel.hide()
        self.mwInfoLabel = DirectLabel(parent = self, pos = (-.119, 0, -0.975), relief = None,
                                       image = newGui.find('**/magicwordlist_usageframe'),
                                       image_scale = OTPGUIUtils.getImageScale(869, 1465, .671),
                                       text_align = TextNode.ALeft,
                                       scale = 1,
                                       text = "", text_scale = 0.03, text_wordwrap = 35,
                                       text_shadow = Vec4(0.0, 0.0, 0.0, 0.8),
                                       text_pos = (-.16, .24), text_fg = Vec4(1.0))
        self.mwInfoLabel.hide()

        self.mwSuggestionFrame = ToontownScrolledFrame(parent = self,
                                                       geom = newGui.find('**/magicwordlist_bg'),
                                                       geom_scale = OTPGUIUtils.getImageScale(2574, 1464, 1.1),
                                                       width = .93,
                                                       height = .48,
                                                       itemPadding = 0.18,
                                                       itemMargin = (0.015, 0),
                                                       pos = SUGGESTION_FRAME_MAINPOS, scale = 0.61,
                                                       verticalScroll_frameColor = (0, 0, 0, 0),
                                                       verticalScroll_manageButtons = False,
                                                       verticalScroll_thumb_geom = (
                                                           newGui.find('**/magicwordlist_scrollbar_normal'),
                                                           newGui.find('**/magicwordlist_scrollbar_press'),
                                                           newGui.find('**/magicwordlist_scrollbar_hover')),
                                                       verticalScroll_thumb_geom_scale = (0.2, 1, .2),
                                                       verticalScroll_thumb_relief = None,
                                                       verticalScroll_resizeThumb = False,
                                                       )
        self.mwSuggestionFrame.hide()

        self.whisperLabel = DirectLabel(parent = self, pos = (0.06, 0, 0.83), relief = DGG.FLAT,
                                        frameColor = (1, 1, 0.5, 1), frameSize = (-0.23, 0.23, -0.07, 0.05),
                                        text = OTPLocalizer.ChatInputNormalWhisper, text_scale = 0.045,
                                        text_pos = (0, -0.01, 0), text_fg = Vec4(0, 0, 0, 1), text_wordwrap = 9.5,
                                        textMayChange = 1)
        # self.chatEntry.bind(DGG.OVERFLOW, self.chatOverflow)
        self.chatEntry.bind(DGG.TYPE, self.typeCallback)
        self.trueFriendChat = 0
        if base.config.GetBool('whisper-to-nearby-true-friends', 1):
            self.accept(self.TFToggleKey, self.shiftPressed)

    def __toggleEmojiPanel(self, forceHide = False):
        if self.emojiFrame.isHidden() and not forceHide:
            self.emojiFrame.show()
        else:
            self.emojiFrame.hide()

    def __hoverEmoji(self, emoji, e):
        self.emojiLabel.show()
        self.emojiLabel['text'] = f':{emoji}:'

    def __unhoverEmoji(self, e):
        self.emojiLabel.hide()

    def __insertEmoji(self, emoji):
        self.chatEntry.enterText(self.chatEntry.get() + f':{emoji}:')

    def shiftPressed(self):
        self.ignore(self.TFToggleKey)
        self.trueFriendChat = 1
        self.accept(self.TFToggleKeyUp, self.shiftReleased)

    def shiftReleased(self):
        self.ignore(self.TFToggleKeyUp)
        self.trueFriendChat = 0
        self.accept(self.TFToggleKey, self.shiftPressed)

    def handleTypeGrab(self):
        self.ignore('typeEntryGrab')
        self.accept('typeEntryRelease', self.handleTypeRelease)
        self.typeGrabbed = 1

    def handleTypeRelease(self):
        self.ignore('typeEntryRelease')
        self.accept('typeEntryGrab', self.handleTypeGrab)
        self.typeGrabbed = 0

    def typeCallback(self, extraArgs):
        if not base.localAvatar.tutorialAck or base.cr.episodeManager.getEpisode():
            return

        if self.typeGrabbed:
            return
        self.applyFilter(extraArgs)
        messenger.send('wakeup')
        if localAvatar.chatMgr.chatInputWhiteList.isActive():
            return
        else:
            messenger.send('enterNormalChat')

    def destroy(self):
        self.chatEntry.destroy()
        self.ignoreAll()
        ChatInputWhiteListFrame.destroy(self)

    def delete(self):
        ChatInputWhiteListFrame.delete(self)

    def sendChat(self, text, overflow = False):
        if self.typeGrabbed:
            return
        else:
            state = self.getCurrentOrNextState()
            if state == 'Off' and ToontownGlobals.HotkeyChatlog not in \
                    base.controlManager.changedHotkeys.get(ToontownGlobals.HotkeyInteraction):
                base.localAvatar.chatMgr.chatLog.openChatlog()
            chatString = self.chatEntry.get()
            for chat in base.emojis:
                chatString = chatString.replace(f':{chat}:', f'\x01white\x01\5{chat}\5\x02')
            ChatInputWhiteListFrame.sendChat(self, self.chatEntry.get())

    def sendChatByData(self, text):
        state = self.getCurrentOrNextState()
        for chat in base.emojis:
            text = text.replace(f':{chat}:', f'\x01white\x01\5{chat}\5\x02')
        if self.trueFriendChat:
            for friendId, flags in base.localAvatar.friendsList:
                if flags & ToontownGlobals.FriendChat:
                    self.sendWhisperByFriend(friendId, text)

        elif self.globalState and state != 'AvatarWhisper':
            base.talkAssistant.sendGlobalTalk(text)
        elif not self.receiverId:
            base.talkAssistant.sendOpenTalk(text)
        elif self.receiverId and not self.toPlayer:
            base.talkAssistant.sendWhisperTalk(text, self.receiverId)
        elif self.receiverId and self.toPlayer:
            base.talkAssistant.sendAccountTalk(text, self.receiverId)

    def sendWhisperByFriend(self, avatarId, text):
        online = 0
        if avatarId in base.cr.doId2do:
            online = 1
        avatarUnderstandable = 0
        av = None
        if avatarId:
            av = base.cr.identifyAvatar(avatarId)
        if av != None:
            avatarUnderstandable = av.isUnderstandable()
        if avatarUnderstandable and online:
            base.talkAssistant.sendWhisperTalk(text, avatarId)

    def chatButtonPressed(self):
        if self.okayToSubmit:
            self.sendChat(self.chatEntry.get())
        else:
            self.sendFailed(self.chatEntry.get())

    def cancelButtonPressed(self):
        self.requestMode('Off')
        messenger.send('exitChat')

    def enterInactive(self):
        base.controlManager.disableAlphaNumericHotkeys = True
        self.deactivate()

    def exitInactive(self):
        pass

    def enterOff(self):
        ChatInputWhiteListFrame.enterOff(self)
        self.__toggleEmojiPanel(forceHide = True)

    def enterAllChat(self):
        ChatInputWhiteListFrame.enterAllChat(self)
        self.whisperLabel.hide()
        self.mwInfoLabel.hide()
        self.mwSuggestionFrame.hide()

    def exitAllChat(self):
        ChatInputWhiteListFrame.exitAllChat(self)

    def enterPlayerWhisper(self):
        ChatInputWhiteListFrame.enterPlayerWhisper(self)
        self.labelWhisper()

    def exitPlayerWhisper(self):
        ChatInputWhiteListFrame.exitPlayerWhisper(self)
        self.whisperLabel.hide()

    def enterAvatarWhisper(self):
        ChatInputWhiteListFrame.enterAvatarWhisper(self)
        self.labelWhisper()
        self.infoLabel.hide()

    def exitAvatarWhisper(self):
        ChatInputWhiteListFrame.exitAvatarWhisper(self)
        self.whisperLabel.hide()
        if self.globalState or self.muted:
            self.infoLabel.show()

    def labelWhisper(self):
        if self.receiverId:
            self.whisperName = base.talkAssistant.findName(self.receiverId, self.toPlayer)
            self.whisperLabel['text'] = OTPLocalizer.ChatInputWhisperLabel % self.whisperName
            self.whisperLabel.show()
        else:
            self.whisperLabel.hide()

    def applyFilter(self, keyArgs, strict = False):
        text = self.chatEntry.get(plain = True)

        if len(text) > OTPGlobals.MaxChatLength:  # Are we over the limit?
            text = text[:256]
        magicWordPrefix = '~'
        magicWordActivatorIndex = ClientSettings.MagicWordActivator.get()
        MW_PREFIX_ALLOWED = ['~', '?', '/', '<', ':', ';']
        if config.GetBool('exec-chat', False):
            MW_PREFIX_ALLOWED.append('>')
        if 0 <= magicWordActivatorIndex <= (len(MW_PREFIX_ALLOWED) - 1):
            magicWordPrefix = MW_PREFIX_ALLOWED[magicWordActivatorIndex]
        if len(text) > 0 and text[0] == magicWordPrefix:
            self.okayToSubmit = True
            words = text.split(' ')
            newwords = []
            for word in words:
                newwords.append('\x01WLMagicWord\x01' + word + '\x02')

            self.handleMagicWords(magicWordPrefix, words)

            newtext = ' '.join(newwords)
            self.chatEntry.set(newtext)
        else:
            words = text.split(' ')
            newwords = []
            self.okayToSubmit = True
            flag = 0
            if (self.whisperId, 1) in base.localAvatar.friendsList:
                flag = 1

            for word in words:
                if word == '' or base.cr.getChatFilterMode() == OTPGlobals.CHAT_FILTER_DEFAULT: # or base.whiteList.isWord(word) or not base.cr.allowWhiteListChat():
                    newwords.append(word)
                elif base.cr.getChatFilterMode() == OTPGlobals.CHAT_FILTER_CENSOR:
                    if base.profanityFilter.contains_profanity(word) and not flag:
                        newwords.append('\x01WLEnter\x01' + word + '\x02')
                    else:
                        newwords.append(word)

                else:
                    if self.checkBeforeSend:
                        self.okayToSubmit = False
                    else:
                        self.okayToSubmit = True
                    if flag:
                        # whisper - true friends
                        newwords.append(word)
                    else:
                        newwords.append('\x01WLEnter\x01' + word + '\x02')

            if not strict:
                lastword = words[-1]
                if lastword == '' or base.whiteList.isPrefix(lastword) or flag or not base.cr.allowWhiteListChat():
                    newwords[-1] = lastword
                else:
                    newwords[-1] = '\x01WLEnter\x01' + lastword + '\x02'
            newtext = ' '.join(newwords)
            self.chatEntry.set(newtext)
        self.chatEntry.guiItem.setAcceptEnabled(self.okayToSubmit)

    def handleMagicWords(self, magicWordPrefix: str, words: List[str]):
        activeMagicWord: Optional[Dict[str, Any]] = None
        mwName = words[0].replace(magicWordPrefix, "")
        for wordName in magicWordIndex:
            word = magicWordIndex[wordName]
            if base.localAvatar.getAccessLevel() < OTPGlobals.AccessLevelName2Int.get(word['access']):
                continue
            if mwName.lower() in word['aliases'] or mwName.lower() == word['classname'].lower():
                activeMagicWord = word
                break
        searchMW: List[Tuple[str, str]] = []
        if not activeMagicWord:
            if len(mwName) >= 1:
                for wordName in magicWordIndex:
                    wordName = wordName.lower()
                    if base.localAvatar.getAccessLevel() < OTPGlobals.AccessLevelName2Int.get(magicWordIndex[wordName]['access']):
                        continue
                    if wordName in magicWordIndex:
                        wordAliases = magicWordIndex[wordName]['aliases']
                        word = any(alias.startswith(mwName.lower()) for alias in wordAliases)
                        if word:
                            if magicWordIndex[wordName]['classname'] not in [x[0] for x in searchMW]:
                                searchMW.append(
                                        (magicWordIndex[wordName]['classname'], magicWordIndex[wordName]['desc'])
                                )
        if activeMagicWord:
            self.mwInfoLabel.show()
            self.mwSuggestionFrame.hide()
            wordArgs = activeMagicWord['args']
            argsList = []
            for arg in wordArgs:
                # arg indexes: 0:NAME,1:TYPE,2:REQUIRED,3:DEFAULT
                if len(arg) == 4:
                    # len 4 args mean ts optional, italicize it and add brackets around it
                    argsList.append(f'\x01WLDisplay\x01[{arg[0]}:{arg[1].__name__}]\x02')
                else:
                    # len 3 args mean its required to be entered
                    argsList.append(f'{arg[0]}:{arg[1].__name__}')

            # validation!

            for arg in argsList:
                ind = argsList.index(arg)
                if ind <= len(words) - 2:
                    valid = False
                    #if len(words[ind + 1]) == 0 and ind == len(words) - 2:
                    #    # If its the currently selected word, we don't need to say its invalid if nothings
                    #    # in it yet
                    #    valid = True
                    if words[ind + 1].strip() == "":
                        # If its a prior arg to the selected one, validate if its empty
                        valid = False
                    else:
                        valid = activeMagicWord['class'].validateArg(ind, words[ind+1], words[1:])
                    if valid:
                        # Valid: Pink
                        argsList[argsList.index(arg)] = f'\x01WLMagicWordArg\x01{arg}\x02'
                    else:
                        # Invalid: Red
                        argsList[argsList.index(arg)] = f'\x01WLEnter\x01{arg}\x02'
                    if ind == len(words) - 2:
                        if activeMagicWord['class'].getValidValuesForArg(ind):
                            self.mwSuggestionFrame.show()
                            self.populateArgSuggestions(activeMagicWord, ind)

            self.mwInfoLabel['text'] = f"{magicWordPrefix}\x01WLMagicWord\x01" \
                                       f"{activeMagicWord['classname']}\x02\n\n\n\n" + '\n\n'.join(argsList)
        elif searchMW:
            self.mwInfoLabel.hide()
            self.cachedArgs = None
            self.mwSuggestionFrame.show()
            self.mwSuggestionFrame.setPos(SUGGESTION_FRAME_MAINPOS)
            self.mwSuggestionFrame.clearItems()
            mwl = []

            newGui: NodePath = loader.loadModel('phase_3.5/models/gui/ttoff_m_gui_chatPanel', allowInstance = True)
            for name, desc in searchMW[:20]:
                btn = DirectButton(
                        relief = None,
                        image = (
                            newGui.find('**/magicwordlist_item_normal'),
                            newGui.find('**/magicwordlist_item_press'),
                            newGui.find('**/magicwordlist_item_hover'),
                        ),
                        image0_color = (0, 0, 0, 0),
                        scale = 0.174,
                        pressEffect = False,
                        image_scale = OTPGUIUtils.getImageScale(1257, 128),
                        text = desc,
                        text_scale = 0.2,
                        text_wordwrap = 45,
                        text_align = TextNode.ALeft,
                        text_pos = (-4.4, -.15),
                        command = self.setCommand,
                        extraArgs = [name]
                )
                OnscreenText(text = name,
                             pos = (-4.7, .2),
                             scale = 0.3, align = TextNode.ALeft, parent = btn)

                mwl.append(btn)
            newGui.removeNode()
            self.mwSuggestionFrame.addItems(*mwl)
        else:
            self.mwInfoLabel['text'] = ''
            self.mwInfoLabel.hide()
            self.mwSuggestionFrame.hide()

    def populateArgSuggestions(self, activeMagicWord, ind):
        newGui: NodePath = loader.loadModel('phase_3.5/models/gui/ttoff_m_gui_chatPanel', allowInstance = True)
        self.mwSuggestionFrame.setPos(SUGGESTION_FRAME_ARGPOS)
        validValues = activeMagicWord['class'].getValidValuesForArg(ind)
        if self.cachedArgs == validValues:
            return
        self.mwSuggestionFrame.clearItems()
        argList = []
        for _arg, _desc in validValues:
            textHeight = -0.08 if _desc is None else 0.08
            text = f'{_arg}\n\x01WLMagicWordArgDesc\x01    {_desc}\x02' if _desc is not None else _arg
            argList.append(
                    DirectButton(
                            relief = None,
                            image = (
                                newGui.find('**/magicwordlist_item_normal'),
                                newGui.find('**/magicwordlist_item_press'),
                                newGui.find('**/magicwordlist_item_hover'),
                            ),
                            image0_color = (0, 0, 0, 0),
                            scale = 0.174,
                            pressEffect = False,
                            image_scale = OTPGUIUtils.getImageScale(1257, 128),
                            text = text,
                            text_scale = 0.40,
                            text_wordwrap = 45,
                            text_align = TextNode.ALeft,
                            text_pos = (-4.4, textHeight),
                            command = self.setArg,
                            extraArgs = [_arg, ind + 1]
                    )
            )
        self.mwSuggestionFrame.addItems(*argList)

        # Save these args so we don't regenerate the menu if we don't need to
        self.cachedArgs = validValues

    def setCommand(self, command: str):
        magicWordPrefix = '~'
        magicWordActivatorIndex = ClientSettings.MagicWordActivator.get()
        MW_PREFIX_ALLOWED = ['~', '?', '/', '<', ':', ';']
        if config.GetBool('exec-chat', False):
            MW_PREFIX_ALLOWED.append('>')
        if 0 <= magicWordActivatorIndex <= (len(MW_PREFIX_ALLOWED) - 1):
            magicWordPrefix = MW_PREFIX_ALLOWED[magicWordActivatorIndex]

        self.chatEntry.enterText(f'{magicWordPrefix}{command} ')
        self.typeCallback(None)

    def setArg(self, arg: str, ind: int):
        command = self.chatEntry.get().split(' ')
        command[ind] = arg
        self.chatEntry.enterText(' '.join(command)+' ')
        self.typeCallback(None)

    def toggleMute(self, state):
        self.muted = state

        if self.muted:
            self.infoLabel.setText(OTPLocalizer.ChatInputNormalMutedNotice)
            self.infoLabel.show()
        else:
            self.infoLabel.setText(OTPLocalizer.ChatInputNormalGlobalNotice)
            if not self.globalState:
                self.infoLabel.hide()

    def __focus(self):
        base.controlManager.disableAlphaNumericHotkeys = True

    def __unfocus(self):
        base.controlManager.disableAlphaNumericHotkeys = False
