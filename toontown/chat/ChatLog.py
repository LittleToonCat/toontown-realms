from direct.gui import DirectGuiGlobals
from direct.gui.DirectGui import *
from panda3d.core import *
from panda3d.toontown import NametagGlobals
from panda3d.toontown import WhisperPopup

from otp.otpbase import OTPLocalizer, OTPGlobals
from otp.otpgui import OTPGUIUtils
from toontown.toonbase import ToontownGlobals, TTLocalizer, ClientSettings


class ChatLog(DirectFrame):
    gui = loader.loadModel('phase_3.5/models/gui/ttoff_m_gui_chatPanel')

    def __init__(self, chatMgr, **kwargs):
        self.chatMgr = chatMgr

        args = {'parent': base.a2dBottomCenter, 'relief': None, 'geom': ChatLog.gui.find('**/chatpanel_new_normal'),
                'geom_scale': OTPGUIUtils.getImageScale(3221, 1937, .75),
                'geom_pos': (0.5, 0, -0.298), 'sortOrder': DGG.FOREGROUND_SORT_INDEX
                }
        kwargs.update(args)
        DirectFrame.__init__(self, **kwargs)
        self.initialiseoptions(ChatLog)

        base.chatlog = self
        self.currentTab = 0
        self.chatTabs = []
        tabs = (
            (
                ChatLog.gui.find('**/chatpanel_tab_normal'),
                ChatLog.gui.find('**/chatpanel_tab_d_normal'),
                ChatLog.gui.find('**/chatpanel_tab_h_normal'),
                None
            ),
            (
                ChatLog.gui.find('**/chatpanel_tab_whisper'),
                ChatLog.gui.find('**/chatpanel_tab_d_whisper'),
                ChatLog.gui.find('**/chatpanel_tab_h_whisper'),
                None
            ),
            (
                ChatLog.gui.find('**/chatpanel_tab_global_'),
                ChatLog.gui.find('**/chatpanel_tab_d_global_'),
                ChatLog.gui.find('**/chatpanel_tab_h_global_'),
                None
            ),
            (
                ChatLog.gui.find('**/chatpanel_tab_system'),
                ChatLog.gui.find('**/chatpanel_tab_d_system'),
                ChatLog.gui.find('**/chatpanel_tab_h_system'),
                None
            ),
        )
        # we keep this, but invisible so we can still easily capture mouse scrolling
        self.chatInside = DirectFrame(
                state = DGG.NORMAL,
                pos = (0.5, 0, -0.29),
                frameColor = (0,0,0,0),
                frameSize = (-0.75, 0.75, -.375, .375)
        )
        x = 1.08
        z = -.0257
        zdiff = .1815

        self.chatInside.reparentTo(self.chatMgr.chatLogNode, -12)
        mainTab = DirectButton(parent = self, relief = None, geom = tabs[0], geom_scale = OTPGUIUtils.getImageScale(214, 445, 1.0),
                               text = ('', '', TTLocalizer.ChatLogTabMain, ''), text_align = TextNode.ALeft, text_fg = (1.0, 1.0, 1.0, 1.0),
                               text_scale = 0.25, text_pos = (.3, -0.055), scale = 0.17,
                               pos = (x, 0.0, z-.002),
                               command = self.__toggleButton, extraArgs = [0])
        whisperTab = DirectButton(parent = self, relief = None, geom = tabs[1], geom_scale = OTPGUIUtils.getImageScale(214, 445, 1.0),
                                  text = ('', '', TTLocalizer.ChatLogTabWhispers, ''), text_align = TextNode.ALeft,
                                  text_scale = 0.25, text_pos = (.3, -0.055), text_fg = (1.0, 1.0, 1.0, 1.0), scale = 0.17,
                                  pos = (x, 0.0, z-(zdiff*2)), command = self.__toggleButton,
                                  extraArgs = [1])
        globalTab = DirectButton(parent = self, relief = None, geom = tabs[2], geom_scale = OTPGUIUtils.getImageScale(214, 445, 1.0),
                                 text = ('', '', TTLocalizer.ChatLogTabGlobal, ''), text_align = TextNode.ALeft,
                                 text_scale = 0.25, text_pos = (.3, -0.055), text_fg = (1.0, 1.0, 1.0, 1.0), scale = 0.17,
                                 pos = (x, 0.0, z-(zdiff*1)), command = self.__toggleButton,
                                 extraArgs = [2])
        systemTab = DirectButton(parent = self, relief = None, geom = tabs[3], geom_scale = OTPGUIUtils.getImageScale(214, 445, 1.0),
                                 text = ('', '', TTLocalizer.ChatLogTabSystem, ''), text_align = TextNode.ALeft,
                                 text_scale = 0.25, text_pos = (.3, -0.055), text_fg = (1.0, 1.0, 1.0, 1.0), scale = 0.17,
                                 pos = (x, 0.0, z-(zdiff*3)), command = self.__toggleButton,
                                 extraArgs = [3])
        self.chatTabs.append(mainTab)
        self.chatTabs.append(whisperTab)
        self.chatTabs.append(globalTab)
        self.chatTabs.append(systemTab)

        self.logs = []
        self.avIds = []
        self.realLogs = []
        self.currents = []
        self.texts = []
        self.textNodes = []
        for x in range(len(self.chatTabs)):
            chatTab = self.chatTabs[x]
            chatTab.reparentTo(self.chatMgr.chatLogNode)
            chatTab.setBin('gui-popup', 104)
            log = []
            realLog = []
            current = 0
            text = TextNode('text')
            text.setWordwrap(26)
            text.setAlign(TextNode.ALeft)
            text.setTextColor(1, 1, 1, 1)
            text.setFont(ToontownGlobals.getToonFont())
            textNode = self.attachNewNode(text, 0)
            textNode.setPos(-.06, 0.0, 0)
            textNode.setScale(0.04)
            self.logs.append(log)
            self.avIds.append([])
            self.realLogs.append(realLog)
            self.currents.append(current)
            self.texts.append(text)
            self.textNodes.append(textNode)

        self.autoScroll = True
        self.closed = False

        self.accept('addToLog', self.__addChatHistory)
        self.accept('playerBanned', self.__removeChatHistory)
        self.accept(f'press-wheel_up-{self.chatInside.guiId}', self.__wheel, extraArgs = [-1])
        self.accept(f'press-wheel_down-{self.chatInside.guiId}', self.__wheel, extraArgs = [1])
        self.__toggleButton(0)

    def destroy(self):
        if not hasattr(self, 'logs'):
            return

        for log in self.logs:
            del log
        self.avIds = []
        for text in self.texts:
            del text
        for textNode in self.textNodes:
            textNode.removeNode()
            del textNode

        DirectButton.destroy(self)
        self.ignoreAll()

    def show(self):
        if self.closed:
            return

        DirectButton.show(self)
        node = self.chatMgr.chatLogNode
        node.show()
        self.__updateSpeedChatStyle()
        self.computeRealLog(0)

    def hide(self):
        DirectButton.hide(self)
        node = self.chatMgr.chatLogNode
        node.hide()
        self.ignoreWheelMovements()

    def closeChatlog(self):
        self.closed = True
        self.hide()

    def openChatlog(self):
        if not self.closed:
            return

        if not base.localAvatar.tutorialAck or base.cr.episodeManager.getEpisode():
            return

        self.closed = False
        self.show()

    def scrollToCurrent(self, tab):
        minimum = max(0, self.currents[tab] - 12)
        self.texts[tab].setText('\n'.join(self.realLogs[tab][minimum:self.currents[tab]]))

    def computeRealLog(self, tab):
        oldText = self.texts[tab].getText()
        self.texts[tab].setText('\n'.join(self.logs[tab]))
        self.realLogs[tab] = self.texts[tab].getWordwrappedText().split('\n')

        if self.autoScroll:
            self.currents[tab] = len(self.realLogs[tab])
            self.scrollToCurrent(tab)
        else:
            self.texts[tab].setText(oldText)

    def __addChatHistory(self, name, avId, font, speechFont, color, chat, type = WhisperPopup.WTNormal):
        tab = 0
        colon = ':'

        if name and not font and not speechFont:
            tab = 1
        if not speechFont:
            speechFont = OTPGlobals.getInterfaceFont()
        if font == ToontownGlobals.getSuitFont():
            color = 5
        if not name:
            if ":" in chat:
                name, chat = chat.split(":", 1)
            else:
                name = 'System'
        if not font:
            font = OTPGlobals.getInterfaceFont()

        if type in (WhisperPopup.WTSystem, WhisperPopup.WTMagicWord, WhisperPopup.WTAnnouncement):
            tab = 3
            if isinstance(color, int):
                color = Vec4(0.8, 0.3, 0.6, 1)
        elif type == WhisperPopup.WTGlobal:
            tab = 2
        elif type == WhisperPopup.WTQuickTalker:
            tab = 1
            if name == base.localAvatar.getName():
                name = OTPLocalizer.MeToReceiver % name
            else:
                name = OTPLocalizer.ReceiverToMe % name

        if isinstance(color, int):
            color = NametagGlobals.getArrowColor(color)

        self.logs[tab].append(
            '\x01%s\x01\x01%s\x01%s%s\x02\x02 \x01%s\x01%s\x02' % (OTPLocalizer.getPropertiesForFont(font),
                                                                   OTPLocalizer.getPropertiesForColor(color),
                                                                   name, colon,
                                                                   OTPLocalizer.getPropertiesForFont(speechFont),
                                                                   chat))
        self.avIds[tab].append(avId)

        while len(self.logs[tab]) > 250:
            del self.logs[tab][0]
            del self.avIds[tab][0]

        self.computeRealLog(tab)

    def __removeChatHistory(self, avId):
        for tab in range(len(self.logs)):
            if tab >= 3:
                continue
            while avId in self.avIds[tab]:
                i = self.avIds[tab].index(avId)
                del self.logs[tab][i]
                del self.avIds[tab][i]

            self.computeRealLog(tab)

    def __wheel(self, amount, event = None):
        oldCurrent = self.currents[self.currentTab]
        minimum = min(12, len(self.realLogs[self.currentTab]))
        self.currents[self.currentTab] += amount
        self.autoScroll = self.currents[self.currentTab] >= len(self.realLogs[self.currentTab])

        if self.autoScroll:
            self.currents[self.currentTab] = len(self.realLogs[self.currentTab])
        if self.currents[self.currentTab] < minimum:
            self.currents[self.currentTab] = minimum

        if oldCurrent != self.currents[self.currentTab]:
            self.scrollToCurrent(self.currentTab)

    def __toggleButton(self, index):
        self.currentTab = index

        if base.cr.wantGlobalChat:
            # Set to global chat if we're in the tab
            self.chatMgr.chatInputNormal.globalState = index == 2

        for x in range(len(self.chatTabs)):
            self.chatTabs[x]['state'] = DirectGuiGlobals.NORMAL
            self.chatTabs[x].reparentTo(self.chatMgr.chatLogNode, -10)
            self.textNodes[x].hide()
        self.chatTabs[index]['state'] = DirectGuiGlobals.DISABLED
        self.chatTabs[index].reparentTo(self.chatMgr.chatLogNode, 100)
        self.textNodes[index].show()
        self.scrollToCurrent(index)

        self['geom'] = (
            ChatLog.gui.find('**/chatpanel_new_normal'),
            ChatLog.gui.find('**/chatpanel_new_whisper'),
            ChatLog.gui.find('**/chatpanel_new_global'),
            ChatLog.gui.find('**/chatpanel_new_system'),
        )[index]

