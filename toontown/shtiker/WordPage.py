from panda3d.core import *
from direct.directnotify import DirectNotifyGlobal
from direct.interval.IntervalGlobal import *
from direct.distributed import DistributedObject
from direct.gui.DirectGui import *
from otp.otpbase import PythonUtil
from toontown.toonbase import ToontownGlobals, ClientSettings
from toontown.toonbase import TTLocalizer
from toontown.toon import Toon
from toontown.toon import ToonDNA
from toontown.spellbook.MagicWordIndex import *
from otp.speedchat import SCStaticTextTerminal
from otp.speedchat import SpeedChat
from . import ShtikerPage
from ..toon.ToonDNA import getClothingColorFromLegacyIndex

magicWordActivators = [2400, 2401, 2402, 2403, 2405, 2406]
if config.GetBool('exec-chat', False):
    magicWordActivators.append(2404)

class PageMode(IntEnum):
    Words = 0
    IDs = 1
    Acc1 = 2
    Acc2 = 3


class WordPage(ShtikerPage.ShtikerPage):
    notify = DirectNotifyGlobal.directNotify.newCategory('WordPage')

    def __init__(self):
        ShtikerPage.ShtikerPage.__init__(self)

    def load(self):
        ShtikerPage.ShtikerPage.load(self)

        self.wordsTabPage = WordsTabPage(self)
        self.clothingTabPage = ClothingTabPage(self)
        self.acc1Page = AccTabPage1(self)
        self.acc2Page = AccTabPage2(self)
        self.wordPages = (self.wordsTabPage, self.clothingTabPage, self.acc1Page, self.acc2Page)

        # hide pages
        for page in self.wordPages:
            page.hide()

        titleHeight = 0.61
        self.title = DirectLabel(parent=self, relief=None, text=TTLocalizer.SpellbookPageTitle, text_scale=0.12, pos=(0, 0, titleHeight))
        normalColor = (1, 1, 1, 1)
        clickColor = (0.8, 0.8, 0, 1)
        rolloverColor = (0.15, 0.82, 1.0, 1)
        diabledColor = (1.0, 0.98, 0.15, 1)
        gui = loader.loadModel('phase_3.5/models/gui/fishingBook')
        self.wordsTab = DirectButton(parent=self, relief=None, text=TTLocalizer.WordPageTabTitle, text_scale=0.063,
                                     text_align=TextNode.ALeft, text_pos=(0.0, 0.0, 0.0),
                                     image=gui.find('**/tabs/polySurface1'), image_pos=(0.55, 1, -0.91),
                                     image_hpr=(0, 0, -90), image_scale=(0.033, 0.033, 0.035), image_color=normalColor,
                                     image1_color=clickColor, image2_color=rolloverColor, image3_color=diabledColor,
                                     text_fg=Vec4(0.2, 0.1, 0, 1), command=self.setMode, extraArgs=[PageMode.Words],
                                     pos=(-0.83, 0, 0.77))
        self.idsTab = DirectButton(parent=self, relief=None, text=TTLocalizer.ClothingPageTitle, text_scale=0.065,
                                   text_align=TextNode.ALeft, text_pos=(0.0, 0.0, 0.0),
                                   image=gui.find('**/tabs/polySurface2'), image_pos=(0.12, 1, -0.91),
                                   image_hpr=(0, 0, -90), image_scale=(0.033, 0.033, 0.035), image_color=normalColor,
                                   image1_color=clickColor, image2_color=rolloverColor, image3_color=diabledColor,
                                   text_fg=Vec4(0.2, 0.1, 0, 1), command=self.setMode, extraArgs=[PageMode.IDs],
                                   pos=(-0.36, 0, 0.77))
        self.acc1Tab = DirectButton(parent=self, relief=None, text=TTLocalizer.AccessoriesPageHeadTab, text_scale=0.045,
                                   text_align=TextNode.ACenter, text_pos=(0.125, 0.035, 0.0),
                                   image=gui.find('**/tabs/polySurface2'), image_pos=(0.12, 1, -0.91),
                                   image_hpr=(0, 0, -90), image_scale=(0.033, 0.033, 0.035), image_color=normalColor,
                                   image1_color=clickColor, image2_color=rolloverColor, image3_color=diabledColor,
                                   text_fg=Vec4(0.2, 0.1, 0, 1), command=self.setMode, extraArgs=[PageMode.Acc1],
                                   pos=(0.11, 0, 0.77))
        self.acc2Tab = DirectButton(parent=self, relief=None, text=TTLocalizer.AccessoriesPageBodyTab, text_scale=0.045,
                                    text_align=TextNode.ACenter, text_pos=(0.125, 0.035, 0.0),
                                    image=gui.find('**/tabs/polySurface2'), image_pos=(0.12, 1, -0.91),
                                    image_hpr=(0, 0, -90), image_scale=(0.033, 0.033, 0.035), image_color=normalColor,
                                    image1_color=clickColor, image2_color=rolloverColor, image3_color=diabledColor,
                                    text_fg=Vec4(0.2, 0.1, 0, 1), command=self.setMode, extraArgs=[PageMode.Acc2],
                                    pos=(0.58, 0, 0.77))
        return

    def enter(self):
        self.setMode(PageMode.Words, updateAnyways=1)
        ShtikerPage.ShtikerPage.enter(self)

    def exit(self):
        for page in self.wordPages:
            page.exit()
        ShtikerPage.ShtikerPage.exit(self)

    def unload(self):
        for page in self.wordPages:
            page.unload()
        del self.title
        ShtikerPage.ShtikerPage.unload(self)

    def setMode(self, mode, updateAnyways = 0):
        messenger.send('wakeup')
        if not updateAnyways:
            if self.mode == mode:
                return
            else:
                self.mode = mode

        # pass the various conditions of the pages to the modeChanges function
        titles = (TTLocalizer.WordPageTabTitle, TTLocalizer.ClothingPageTitle, TTLocalizer.AccessoriesPageHead,
                  TTLocalizer.AccessoriesPageBody)
        if mode == PageMode.Words:
            self.modeChanges(PageMode.Words, titles[0], DGG.DISABLED, DGG.NORMAL, DGG.NORMAL, DGG.NORMAL, 1, 0, 0, 0)
        elif mode == PageMode.IDs:
            self.modeChanges(PageMode.IDs, titles[1], DGG.NORMAL, DGG.DISABLED, DGG.NORMAL, DGG.NORMAL, 0, 1, 0, 0)
        elif mode == PageMode.Acc1:
            self.modeChanges(PageMode.Acc1, titles[2], DGG.NORMAL, DGG.NORMAL, DGG.DISABLED, DGG.NORMAL, 0, 0, 1, 0)
        elif mode == PageMode.Acc2:
            self.modeChanges(PageMode.Acc2, titles[3], DGG.NORMAL, DGG.NORMAL, DGG.NORMAL, DGG.DISABLED, 0, 0, 0, 1)
        else:
            raise Exception('WordPage::setMode - Invalid Mode %s' % mode)

    # apply the mode changes
    def modeChanges(self, mode, title, wordsState, idsState, acc1State, acc2State, wordsEnter, clothingEnter,
                    acc1Enter,
                    acc2Enter):
        self.mode = mode
        self.title['text'] = title

        self.wordsTab['state'] = wordsState
        self.idsTab['state'] = idsState
        self.acc1Tab['state'] = acc1State
        self.acc2Tab['state'] = acc2State

        i = 0
        for entry in (wordsEnter, clothingEnter, acc1Enter, acc2Enter):
            # check if it should enter or exit
            if entry:
                self.wordPages[i].enter()
            else:
                self.wordPages[i].exit()
            i += 1


class WordsTabPage(DirectFrame):
    notify = DirectNotifyGlobal.directNotify.newCategory('WordsTabPage')

    def __init__(self, parent = aspect2d):
        self._parent = parent
        self.currentSizeIndex = None
        DirectFrame.__init__(self, parent=self._parent, relief=None, pos=(0.0, 0.0, 0.0), scale=(1.0, 1.0, 1.0))
        self.magicWordMoreInfoLabelNode = None
        self.load()

    def load(self):
        self.magicWords = []
        self.hiddenMagicWords = []
        self.shownMagicWords = []
        self.setupWords()

        gui = loader.loadModel('phase_3.5/models/gui/friendslist_gui')
        coolbutton = loader.loadModel('phase_3/models/gui/pick_a_toon_gui')
        guiButton = loader.loadModel('phase_3/models/gui/quit_button')
        cdrGui = loader.loadModel('phase_3.5/models/gui/tt_m_gui_sbk_codeRedemptionGui')
        guiClose = loader.loadModel('phase_3.5/models/gui/avatar_panel_gui')
        self.helpLabel = DirectLabel(parent=self, relief=None, text=TTLocalizer.WordPageHelp, text_scale=0.06,
                                     text_wordwrap=12, text_align=TextNode.ALeft, textMayChange=1,
                                     pos=(0.058, 0, 0.503))
        self.searchLabel = DirectLabel(parent=self, relief=None, text=TTLocalizer.WordPageSearch, text_scale=0.06,
                                       text_wordwrap=12, text_align=TextNode.ACenter, textMayChange=1,
                                       pos=(0.439, 0, -0.2))
        self.searchBarFrame = DirectFrame(parent=self, relief=None, image=cdrGui.find('**/tt_t_gui_sbk_cdrCodeBox'),
                                          pos=(0.439, 0.0, -0.3225), scale=0.7)
        self.searchBarEntry = DirectEntry(parent=self, relief=None, text_scale=0.06, width=7.75, textMayChange=1,
                                          pos=(0.209, 0, -0.3325), text_align=TextNode.ALeft, backgroundFocus=0,
                                          focusInCommand=self.toggleSpeedchat, focusInExtraArgs=[False],
                                          focusOutCommand=self.toggleSpeedchat, focusOutExtraArgs=[True])
        self.searchBarEntry.bind(DGG.TYPE, self.updateWordSearch)
        self.searchBarEntry.bind(DGG.ERASE, self.updateWordSearch)
        self.activatorLabel = DirectLabel(parent=self, relief=None,
                                          text=TTLocalizer.WordPageActivator,
                                          text_scale=0.06, text_wordwrap=12, text_align=TextNode.ALeft, textMayChange=1,
                                          pos=(0.058, 0, 0.25))
        self.totalLabel = DirectLabel(parent=self, relief=None,
                                      text=TTLocalizer.WordPageTotal + str(len(self.shownMagicWords)), text_scale=0.06,
                                      text_wordwrap=12, text_align=TextNode.ALeft, textMayChange=1,
                                      pos=(0.058, 0, 0.05))
        self.currentLabel = DirectLabel(parent=self, relief=None,
                                        text=TTLocalizer.WordPageCurrent + TTLocalizer.WordPageNA, text_scale=0.06,
                                        text_wordwrap=12, text_align=TextNode.ALeft, textMayChange=1,
                                        pos=(0.058, 0, -0.05))
        accessLevel = OTPGlobals.AccessLevelDebug2Name.get(OTPGlobals.AccessLevelInt2Name.get(base.localAvatar.getAccessLevel()))
        self.accessLabel = DirectLabel(parent=self, relief=None, text=TTLocalizer.WordPageAccess % (accessLevel, base.localAvatar.getAccessLevel()),
                                       text_scale=0.06, text_wordwrap=18, text_align=TextNode.ALeft, textMayChange=1,
                                       pos=(0.058, 0, 0.15))
        self.magicWordActivatorLeftArrow = DirectButton(parent=self, relief=None, image=(gui.find('**/Horiz_Arrow_UP'),
                                                                                         gui.find('**/Horiz_Arrow_DN'),
                                                                                         gui.find(
                                                                                             '**/Horiz_Arrow_Rllvr'),
                                                                                         gui.find('**/Horiz_Arrow_UP')),
                                                        image3_color=Vec4(1, 1, 1, 0.5), scale=(-1.0, 1.0, 1.0),
                                                        pos=(0.4, 0, 0.28),
                                                        command=self.__doMagicWordActivatorLeft)
        self.magicWordActivatorRightArrow = DirectButton(parent=self, relief=None, image=(gui.find('**/Horiz_Arrow_UP'),
                                                                                          gui.find('**/Horiz_Arrow_DN'),
                                                                                          gui.find(
                                                                                              '**/Horiz_Arrow_Rllvr'),
                                                                                          gui.find(
                                                                                              '**/Horiz_Arrow_UP')),
                                                         image3_color=Vec4(1, 1, 1, 0.5),
                                                         pos=(0.65, 0, 0.28),
                                                         command=self.__doMagicWordActivatorRight)
        self.magicWordActivatorText = SpeedChat.SpeedChat(name = 'ExtraOptionsPageMagicWordActivator', structure = [2400])
        self.magicWordActivatorText.setScale(0.055)
        self.magicWordActivatorText.setPos(0.525, 0, 0.31)
        self.magicWordActivatorText.reparentTo(self, DGG.FOREGROUND_SORT_INDEX)
        self.copyToChatButton = DirectButton(parent=self, relief=None, image=(guiButton.find('**/QuitBtn_UP'),
                                                                              guiButton.find('**/QuitBtn_DN'),
                                                                              guiButton.find('**/QuitBtn_RLVR')),
                                             image_scale=(0.7, 1, 1), text=TTLocalizer.WordPageCopyToChat,
                                             text_scale=0.04, text_pos=(0, -0.01), pos=(0.629, 0.0, -0.5325),
                                             command=self.copyToChat)
        self.infoButton = DirectButton(parent=self, relief=None, image=(guiButton.find('**/QuitBtn_UP'),
                                                                        guiButton.find('**/QuitBtn_DN'),
                                                                        guiButton.find('**/QuitBtn_RLVR')),
                                       image_scale=(0.7, 1, 1), text=TTLocalizer.WordPageInfo,
                                       text_scale=0.04, text_pos=(0, -0.01), pos=(0.249, 0.0, -0.5325),
                                       command=self.showInfoPanel)
        self.scrollList = DirectScrolledList(parent=self, forceHeight=0.07, pos=(-0.5, 0, 0),
                                             incButton_image=(gui.find('**/FndsLst_ScrollUp'),
                                                              gui.find('**/FndsLst_ScrollDN'),
                                                              gui.find('**/FndsLst_ScrollUp_Rllvr'),
                                                              gui.find('**/FndsLst_ScrollUp')),
                                             incButton_relief=None, incButton_scale=(1.3, 1.3, -1.3),
                                             incButton_pos=(0.08, 0, -0.60), incButton_image3_color=Vec4(1, 1, 1, 0.2),
                                             decButton_image=(gui.find('**/FndsLst_ScrollUp'),
                                                              gui.find('**/FndsLst_ScrollDN'),
                                                              gui.find('**/FndsLst_ScrollUp_Rllvr'),
                                                              gui.find('**/FndsLst_ScrollUp')),
                                             decButton_relief=None,  decButton_scale=(1.3, 1.3, 1.3),
                                             decButton_pos=(0.08, 0, 0.52), decButton_image3_color=Vec4(1, 1, 1, 0.2),
                                             itemFrame_pos=(-0.237, 0, 0.41), itemFrame_scale=1.0,
                                             itemFrame_relief=DGG.SUNKEN,
                                             itemFrame_frameSize=(-0.05, 0.66, -0.98, 0.07),
                                             itemFrame_frameColor=(0.85, 0.95, 1, 1),
                                             itemFrame_borderWidth=(0.01, 0.01),
                                             numItemsVisible=14, items=self.shownMagicWords)
        self.slider = DirectSlider(parent=self, range=(len(self.shownMagicWords), 0),
                                   scale=(0.7, 0.7, 0.515), pos=(-0.1, 0, -0.045),
                                   pageSize=1, orientation=DGG.VERTICAL, command=self.scrollListTo,
                                   thumb_geom=(coolbutton.find('**/QuitBtn_UP'),
                                                coolbutton.find('**/QuitBtn_DN'),
                                                coolbutton.find('**/QuitBtn_RLVR_default'),
                                                coolbutton.find('**/QuitBtn_UP')),
                                   thumb_relief=None, thumb_geom_hpr=(0, 0, -90), thumb_geom_scale=(0.5, 1, 0.5))
        self.magicWordInfo = DirectFrame(parent=self, relief=None, pos=(0.0, 0.0, -0.05), scale=0.9,
                                         geom=DGG.getDefaultDialogGeom(), geom_scale=(1.4, 1, 1.25),
                                         geom_color=ToontownGlobals.GlobalDialogColor)
        self.magicWordInfo.reparentTo(self, DGG.FOREGROUND_SORT_INDEX)
        self.magicWordInfo.setBin('gui-popup', 0)
        self.magicWordInfo.hide()
        self.magicWordTitle = DirectLabel(parent=self.magicWordInfo, relief=None, text=TTLocalizer.WordPageNA,
                                          text_scale=0.12,  textMayChange=1, pos=(0, 0, 0.5))
        self.magicWordInfoLabel = DirectLabel(parent=self.magicWordInfo, relief=None, text=TTLocalizer.WordPageNA,
                                              text_scale=0.06, text_wordwrap=20, text_align=TextNode.ALeft,
                                              textMayChange=1, pos=(-0.6, 0, 0.35))
        self.magicWordQuitButton = DirectButton(parent=self.magicWordInfo,
                                                image=(guiClose.find('**/CloseBtn_UP'),
                                                       guiClose.find('**/CloseBtn_DN'),
                                                       guiClose.find('**/CloseBtn_Rllvr'),
                                                       guiClose.find('**/CloseBtn_UP')),
                                                relief=None, scale=1.5, pos=(0.6, 0, -0.5),
                                                command=self.hideInfoPanel)
        self.magicWordMoreInfoButton = DirectButton(parent=self.magicWordInfo, relief=None,
                                                    image=(guiButton.find('**/QuitBtn_UP'),
                                                           guiButton.find('**/QuitBtn_DN'),
                                                           guiButton.find('**/QuitBtn_RLVR')),
                                                    image_scale=(0.7, 1, 1), text=TTLocalizer.WordPageMoreInfo,
                                                    text_scale=0.04, text_pos=(0, -0.01), pos=(-0.499, 0.0, -0.5025),
                                                    command=self.showMoreInfoPanel)
        self.magicWordMoreInfoButton.hide()
        self.magicWordMoreInfo = DirectFrame(parent=self, relief=None, pos=(0.7, 0.0, 0.0), scale=(1.4, 1, 1),
                                             geom=DGG.getDefaultDialogGeom(),
                                             geom_color=ToontownGlobals.GlobalDialogColor)
        self.magicWordMoreInfo.setBin('gui-popup', 0)
        self.magicWordMoreInfo.hide()
        self.magicWordMoreInfoLabel = DirectLabel(parent=self, relief=None, text=TTLocalizer.WordPageNA,
                                                  text_scale=0.06, text_wordwrap=19, text_align=TextNode.ALeft,
                                                  textMayChange=1, pos=(0.1, 0, 0))
        self.magicWordMoreInfoLabel.setBin('gui-popup', 0)

        for gui in (gui, coolbutton, guiButton, cdrGui, guiClose):
            gui.removeNode()

    def unload(self):
        for word in self.magicWords + self.hiddenMagicWords + self.shownMagicWords:
            word.destroy()
            del word

        gui = [self.helpLabel, self.searchLabel, self.searchBarFrame, self.searchBarEntry, self.activatorLabel,
               self.totalLabel, self.currentLabel, self.magicWordActivatorLeftArrow, self.magicWordActivatorLeftArrow,
               self.magicWordActivatorText, self.copyToChatButton, self.infoButton, self.scrollList, self.slider,
               self.magicWordTitle, self.magicWordInfoLabel, self.magicWordQuitButton, self.magicWordMoreInfoButton,
               self.magicWordMoreInfoLabel, self.magicWordMoreInfoLabelNode, self.magicWordMoreInfo, self.magicWordInfo]

        for dgui in gui:
            if dgui:
                dgui.destroy()
                del dgui

    def exit(self):
        for word in self.magicWords:
            if word['state'] != DGG.NORMAL:
                word['state'] = DGG.NORMAL

        self.magicWordActivatorText.exit()
        self.currentLabel['text'] = TTLocalizer.WordPageCurrent + TTLocalizer.WordPageNA
        self.ignore('mouse1')
        self.updateWordSearch()
        self.hideInfoPanel()
        self.searchBarEntry['focus'] = 0
        self.searchBarEntry.setFocus()
        self.hide()

    def enter(self):
        for word in self.magicWords:
            if self._parent.book.safeMode:
                word['state'] = DGG.DISABLED
            elif word['state'] != DGG.NORMAL:
                word['state'] = DGG.NORMAL

        self.magicWordActivatorText.enter()
        self.magicWordActivatorIndex = MagicWordConfig.PREFIX_ALLOWED.index(base.cr.magicWordManager.chatPrefix)
        self.updateMagicWordActivator()
        self.currentLabel['text'] = TTLocalizer.WordPageCurrent + TTLocalizer.WordPageNA
        self.accept('mouse1', self.toggleEntryFocus, extraArgs=[True])
        self.updateWordSearch()
        self.hideInfoPanel()
        self.show()

        if self._parent.book.safeMode:
            self.copyToChatButton['state'] = DGG.DISABLED
            self.magicWordMoreInfoButton['state'] = DGG.DISABLED
        else:
            self.copyToChatButton['state'] = DGG.NORMAL
            self.magicWordMoreInfoButton['state'] = DGG.NORMAL

    def scrollListTo(self):
        messenger.send('wakeup')
        self.scrollList.scrollTo(int(self.slider['value']))

    def toggleEntryFocus(self, state):
        if state:
            self.searchBarEntry['focus'] = 0
            self.searchBarEntry.setFocus()

    def toggleSpeedchat(self, state):
        if not state:
            localAvatar.chatMgr.setBackgroundFocus(False, True)

            # Prevent page switching when in the box (useful for ppl with wasd)
            base.controlManager.addDisabledHotkey(ToontownGlobals.HotkeyMovement, ToontownGlobals.HotkeyLeft)
            base.controlManager.addDisabledHotkey(ToontownGlobals.HotkeyMovement, ToontownGlobals.HotkeyRight)
        else:
            localAvatar.chatMgr.setBackgroundFocus(base.controlManager.getChatDisabled(), True)

            # re enable the page switching keys
            base.controlManager.removeDisabledHotkey(ToontownGlobals.HotkeyMovement, ToontownGlobals.HotkeyLeft)
            base.controlManager.removeDisabledHotkey(ToontownGlobals.HotkeyMovement, ToontownGlobals.HotkeyRight)

    def setupWords(self, returnWords=False):
        words = []

        for wordName in magicWordIndex:
            word = magicWordIndex[wordName]
            if word['classname'] not in words:
                if not word['hidden']:
                    words.append(word['classname'])

        sortedWords = sorted(words)

        numWords = len(sortedWords)
        if returnWords:
            return numWords

        currentWordIndex = 0
        while currentWordIndex < numWords:
            newWordButton = DirectButton(parent=self, relief=None, text=sortedWords[currentWordIndex],
                                         text_align=TextNode.ALeft, text_scale=0.05, text1_bg=Vec4(0.5, 0.9, 1, 1),
                                         text2_bg=Vec4(1, 1, 0, 1), text3_fg=Vec4(0.4, 0.8, 0.4, 1), textMayChange=0,
                                         command=self.showWordInfo, extraArgs=[currentWordIndex])
            self.magicWords.append(newWordButton)
            self.shownMagicWords.append(newWordButton)
            currentWordIndex += 1

    def showWordInfo(self, wordNum):
        messenger.send('wakeup')
        for word in self.magicWords:
            if word['state'] != DGG.NORMAL:
                word['state'] = DGG.NORMAL

        wordName = self.magicWords[wordNum]
        wordName['state'] = DGG.DISABLED
        self.currentLabel['text'] = TTLocalizer.WordPageCurrent + wordName['text']

    def updateWordSearch(self, extraArgs=None):
        messenger.send('wakeup')
        self.hiddenMagicWords = []
        searchTerm = self.searchBarEntry.get().lower()
        for word in self.magicWords + self.hiddenMagicWords:
            wordLabel = word['text'].lower()
            try:
                # First alias is the same as the word itself so we don't use that
                wordAliases = magicWordIndex[wordLabel]['aliases'][1:]
                wordIsAlias = any(searchTerm in alias for alias in wordAliases)
            except KeyError:
                wordIsAlias = False
            if (searchTerm not in wordLabel and not wordIsAlias) and word in self.magicWords:
                self.hiddenMagicWords.append(word)
                if word['state'] != DGG.NORMAL:
                    self.currentLabel['text'] = TTLocalizer.WordPageCurrent + TTLocalizer.WordPageNA
                    word['state'] = DGG.NORMAL
                word.hide()
            elif (searchTerm in wordLabel or wordIsAlias) and word in self.hiddenMagicWords:
                self.hiddenMagicWords.remove(word)
                word.show()

        self.shownMagicWords = []
        for word in self.magicWords:
            if word not in self.hiddenMagicWords:
                self.shownMagicWords.append(word)

        magicWordCount = len(self.shownMagicWords)
        if magicWordCount == 0:
            magicWordCount = 1

        self.totalLabel['text'] = TTLocalizer.WordPageTotal + str(len(self.shownMagicWords))
        self.scrollList['items'] = self.shownMagicWords
        self.slider['range'] = (magicWordCount, 0)

    def copyToChat(self):
        messenger.send('wakeup')
        wordName = None
        for word in self.magicWords:
            if word['state'] != DGG.NORMAL:
                wordName = word['text']
                break

        if not wordName:
            return

        phrase = base.cr.magicWordManager.chatPrefix + wordName + ' '
        localAvatar.book.closeBook()
        localAvatar.chatMgr.setBackgroundFocus(base.controlManager.getChatDisabled(), True)
        localAvatar.chatMgr.chatInputNormal.typeCallback(None)
        localAvatar.chatMgr.chatInputNormal.chatEntry.enterText(phrase)

    def showInfoPanel(self):
        messenger.send('wakeup')

        wordName = None
        for word in self.magicWords:
            if word['state'] != DGG.NORMAL:
                wordName = word['text']
                break

        if not wordName:
            return

        base.transitions.fadeScreen(0.5)

        wordInfo = magicWordIndex[wordName.lower()]
        wordText = TTLocalizer.WordPageDescription + wordInfo['desc']
        prefix = base.cr.magicWordManager.chatPrefix
        if not wordInfo['example']:
            exampleText = TTLocalizer.WordPageExample + prefix + wordName.lower()
        else:
            exampleText = TTLocalizer.WordPageExample + prefix + wordName.lower() + ' ' + wordInfo['example']
        aliasText = TTLocalizer.WordPageAliases
        for alias in wordInfo['aliases']:
            aliasText += alias
            if wordInfo['aliases'].index(alias) != len(wordInfo['aliases']) - 1:
                aliasText += ', '
        accessLevelText = TTLocalizer.WordPageAccessLevel % (OTPGlobals.AccessLevelDebug2Name.get(wordInfo['access']), OTPGlobals.AccessLevelName2Int.get(wordInfo['access']))
        if wordInfo['cooldown'] and not base.localAvatar.getAccessLevel() < OTPGlobals.AccessLevelName2Int.get(base.cr.magicWordManager.bypassLevel):
            if wordInfo['cooldown'] == 1:
                coolDownVal = TTLocalizer.WordPageCooldownSecond
            else:
                coolDownVal = TTLocalizer.WordPageCooldownSeconds % wordInfo['cooldown']
        else:
            coolDownVal = TTLocalizer.WordPageCooldownNone
        coolDownText = TTLocalizer.WordPageCooldown % coolDownVal

        anyTarget = TTLocalizer.WordPageAnyTarget.format(wordInfo['anyTarget'])

        lineBreak = '\n\n'
        infoText = wordText + lineBreak + exampleText + lineBreak + aliasText + lineBreak + accessLevelText + lineBreak + coolDownText + lineBreak + anyTarget

        if wordInfo.get('advancedDesc') != MagicWordConfig.MAGIC_WORD_DEFAULT_ADV_DESC:
            self.magicWordMoreInfoButton.show()

        self.magicWordTitle['text'] = wordName
        self.magicWordInfoLabel['text'] = infoText

        self.magicWordInfo.show()

    def hideInfoPanel(self):
        messenger.send('wakeup')
        base.transitions.noTransitions()

        self.magicWordTitle['text'] = TTLocalizer.WordPageNA
        self.magicWordInfoLabel['text'] = TTLocalizer.WordPageNA

        self.magicWordInfo.hide()
        self.magicWordInfo.setPos(0.0, 0.0, -0.05)
        self.magicWordMoreInfo.hide()
        self.magicWordMoreInfo.hide()
        self.magicWordMoreInfoLabel.hide()
        if hasattr(self, 'magicWordMoreInfoLabelNode') and self.magicWordMoreInfoLabelNode:
            self.magicWordMoreInfoLabelNode.removeNode()
            self.magicWordMoreInfoLabelNode = None
        self.magicWordMoreInfoButton.setText(TTLocalizer.WordPageMoreInfo)
        self.magicWordMoreInfoButton.hide()

    def showMoreInfoPanel(self):
        messenger.send('wakeup')

        if self.magicWordMoreInfoButton['text'] == TTLocalizer.WordPageMoreInfo:
            wordName = None
            for word in self.magicWords:
                if word['state'] != DGG.NORMAL:
                    wordName = word['text']
                    break

            if not wordName:
                return

            wordInfo = magicWordIndex[wordName.lower()]
            advancedDescription = wordInfo['advancedDesc']

            self.magicWordInfo.setPos(-0.7, 0.0, -0.05)
            self.magicWordMoreInfoLabel.setText(advancedDescription)

            self.magicWordMoreInfoLabelNode = NodePath(self.magicWordMoreInfoLabel.component('text0').textNode.generate())
            self.magicWordMoreInfoLabelNode.setBin('gui-popup', 0)
            size = self.magicWordMoreInfoLabelNode.getBounds()
            center = size.getCenter()
            self.magicWordMoreInfoLabelNode.set_pos(-center)
            self.magicWordMoreInfoLabelNode.setX(0.125)
            self.magicWordMoreInfoLabelNode.reparentTo(self)

            zScale = 0.075 * 0.9 * self.magicWordMoreInfoLabel.component('text0').textNode.getNumRows()
            self.magicWordMoreInfo.setScale(1.26, 0.9, zScale)
            self.magicWordMoreInfo.show()

            self.magicWordMoreInfoButton.setText(TTLocalizer.WordPageLessInfo)
        else:
            self.magicWordInfo.setPos(0.0, 0.0, -0.05)
            self.magicWordMoreInfoLabel.setText(TTLocalizer.WordPageNA)
            self.magicWordMoreInfoLabel.hide()
            self.magicWordMoreInfo.hide()

            if hasattr(self, 'magicWordMoreInfoLabelNode') and self.magicWordMoreInfoLabelNode:
                self.magicWordMoreInfoLabelNode.removeNode()
                self.magicWordMoreInfoLabelNode = None

            self.magicWordMoreInfoButton.setText(TTLocalizer.WordPageMoreInfo)

    def __doMagicWordActivatorLeft(self):
        if self.magicWordActivatorIndex > 0:
            self.magicWordActivatorIndex = self.magicWordActivatorIndex - 1
            self.updateMagicWordActivator()

    def __doMagicWordActivatorRight(self):
        if self.magicWordActivatorIndex < len(magicWordActivators) - 1:
            self.magicWordActivatorIndex = self.magicWordActivatorIndex + 1
            self.updateMagicWordActivator()

    def updateMagicWordActivator(self):
        messenger.send('wakeup')
        activatorId = magicWordActivators[self.magicWordActivatorIndex]
        self.magicWordActivatorText.clearMenu()
        activatorId = SCStaticTextTerminal.SCStaticTextTerminal(activatorId)
        self.magicWordActivatorText.append(activatorId)
        self.magicWordActivatorText.finalize()
        self.magicWordActivatorText.setPos(0.525 - self.magicWordActivatorText.getWidth() * 0.055 / 2, 0, self.magicWordActivatorText.getPos()[2])
        if self.magicWordActivatorIndex > 0:
            self.magicWordActivatorLeftArrow['state'] = DGG.NORMAL
        else:
            self.magicWordActivatorLeftArrow['state'] = DGG.DISABLED
        if self.magicWordActivatorIndex < len(magicWordActivators) - 1:
            self.magicWordActivatorRightArrow['state'] = DGG.NORMAL
        else:
            self.magicWordActivatorRightArrow['state'] = DGG.DISABLED
        base.cr.magicWordManager.setChatPrefix(MagicWordConfig.PREFIX_ALLOWED[self.magicWordActivatorIndex])
        ClientSettings.MagicWordActivator.set(self.magicWordActivatorIndex)


class ClothingTabPage(DirectFrame):
    notify = DirectNotifyGlobal.directNotify.newCategory('ClothingTabPage')

    # TODO Clean Up if possible

    def __init__(self, parent = aspect2d):
        self.textRolloverColor = Vec4(1, 1, 0, 1)
        self.textDownColor = Vec4(0.5, 0.9, 1, 1)
        self.textDisabledColor = Vec4(0.4, 0.8, 0.4, 1)
        self._parent = parent
        self.currentSizeIndex = None
        DirectFrame.__init__(self, parent=self._parent, relief=None, pos=(0.0, 0.0, 0.0), scale=(1.0, 1.0, 1.0))
        self.load()

    def load(self):
        self.model = None
        self.turnSeq = Sequence()
        self.word1Desc = DirectLabel(parent=hidden, relief=None, text='', text_align=TextNode.ALeft, text_scale=0.06, text_wordwrap=12, pos=(0.058, 0, 0))
        self.shirtList = []
        self.shirtIDs = []
        self.sleeveList = []
        self.sleeveIDs = []
        self.boyPantList = []
        self.boyPantIDs = []
        self.girlPantList = []
        self.girlPantIDs = []
        self.girlPantTypes = []
        self.colorList = []
        self.colorIDs = []
        av = base.cr.doId2do.get(base.localAvatar.doId)
        self.shirt = av.style.topTex
        self.shirtColor = av.style.topTexColor
        self.sleeve = av.style.sleeveTex
        self.sleeveColor = av.style.sleeveTexColor
        self.pant = av.style.botTex
        self.pantColor = av.style.botTexColor
        genderList = ['m', 'f']
        self.gender = genderList.index(av.style.gender)
        self.color = 0
        self.torsoSize = av.style.torso[0]
        self.torsoType = 's'
        if len(av.style.torso) > 1:
            self.torsoType = av.style.torso[1]
        self.l = locals()
        self.makeList()
        self.shirtWords = list(self.shirtList)
        self.sleeveWords = list(self.sleeveList)
        self.boyPantWords = list(self.boyPantList)
        self.girlPantWords = list(self.girlPantList)
        self.colorWords = list(self.colorIDs)
        self.rainbowEffect = Sequence()

        self.makeScrollLists()
        self.createModel()
        self.makeButtons()

    def scrollListTo(self, scrollList, slider):
        messenger.send('wakeup')
        if slider == 'shirt':
            slider = self.shirtslider
        elif slider == 'sleeve':
            slider = self.sleeveslider
        elif slider == 'boypants':
            slider = self.pantslider1
        elif slider == 'girlpants':
            slider = self.pantslider2
        elif slider == 'color':
            slider = self.colorslider
        scrollList.scrollTo(int(slider['value']))

    def makeList(self):
        for x in range(len(ToonDNA.Shirts)):
            self.l['self.shirts' + str(x)] = DirectButton(parent=self, relief=None, text=str(x) + " - " + ToonDNA.Shirts[x].split('/', 1)[-1].split('/', 1)[-1].replace(".png", ""), text_align=TextNode.ALeft, text_scale=0.05, text1_bg=self.textDownColor, text2_bg=self.textRolloverColor, text3_fg=self.textDisabledColor, textMayChange=1, command=self.showWordInfo, extraArgs=[x, self.word1Desc, 'shirt'])
            #--disposing of long labels--

            if ToonDNA.Shirts[x].split('/', 1)[-1].split('/', 1)[-1].startswith('apparel/') or ToonDNA.Shirts[x].split('/', 1)[-1].split('/', 1)[-1].startswith('tiers/'):
                self.l['self.shirts' + str(x)]["text"] = str(x) + " - " + ToonDNA.Shirts[x].split('/', 1)[-1].split('/', 1)[-1].split('/', 1)[-1].replace(".png", "")
            elif ToonDNA.Shirts[x].split('/', 1)[-1].split('/', 1)[-1].startswith('tt_t_chr_'):
                self.l['self.shirts' + str(x)]["text"] = str(x) + " - " + ToonDNA.Shirts[x].split('/', 1)[-1].split('/', 1)[-1].split('_', 1)[-1].split('_', 1)[-1].split('_', 1)[-1].split('_', 1)[-1].split('_', 1)[-1].replace(".png", "")

            self.shirtList.append(self.l['self.shirts' + str(x)])
            self.shirtIDs.append( x )
        for x in range(len(ToonDNA.Sleeves)):
            self.l['self.sleeves' + str(x)] = DirectButton(parent=self, relief=None, text=str(x) + " - " + ToonDNA.Sleeves[x].split('/', 1)[-1].split('/', 1)[-1].replace(".png", ""), text_align=TextNode.ALeft, text_scale=0.05, text1_bg=self.textDownColor, text2_bg=self.textRolloverColor, text3_fg=self.textDisabledColor, textMayChange=1, command=self.showWordInfo, extraArgs=[x, self.word1Desc, 'sleeve'])

            if ToonDNA.Sleeves[x].split('/', 1)[-1].split('/', 1)[-1].startswith('apparel/') or ToonDNA.Sleeves[x].split('/', 1)[-1].split('/', 1)[-1].startswith('tiers/'):
                self.l['self.sleeves' + str(x)]["text"] = str(x) + " - " + ToonDNA.Sleeves[x].split('/', 1)[-1].split('/', 1)[-1].split('/', 1)[-1].replace(".png", "")
            elif ToonDNA.Sleeves[x].split('/', 1)[-1].split('/', 1)[-1].startswith('tt_t_chr_'):
                self.l['self.sleeves' + str(x)]["text"] = str(x) + " - " + ToonDNA.Sleeves[x].split('/', 1)[-1].split('/', 1)[-1].split('_', 1)[-1].split('_', 1)[-1].split('_', 1)[-1].split('_', 1)[-1].split('_', 1)[-1].replace(".png", "")

            self.sleeveList.append(self.l['self.sleeves' + str(x)])
            self.sleeveIDs.append( x )
        for x in range(len(ToonDNA.BoyShorts)):
            self.l['self.boypants' + str(x)] = DirectButton(parent=self, relief=None, text=str(x) + " - " + ToonDNA.BoyShorts[x].split('/', 1)[-1].split('/', 1)[-1].replace(".png", ""), text_align=TextNode.ALeft, text_scale=0.05, text1_bg=self.textDownColor, text2_bg=self.textRolloverColor, text3_fg=self.textDisabledColor, textMayChange=1, command=self.showWordInfo, extraArgs=[x, self.word1Desc, 'pants'])

            if ToonDNA.BoyShorts[x].split('/', 1)[-1].split('/', 1)[-1].startswith('apparel/') or ToonDNA.BoyShorts[x].split('/', 1)[-1].split('/', 1)[-1].startswith('tiers/'):
                self.l['self.boypants' + str(x)]["text"] = str(x) + " - " + ToonDNA.BoyShorts[x].split('/', 1)[-1].split('/', 1)[-1].split('/', 1)[-1].replace(".png", "")
            elif ToonDNA.BoyShorts[x].split('/', 1)[-1].split('/', 1)[-1].startswith('tt_t_chr_'):
                self.l['self.boypants' + str(x)]["text"] = str(x) + " - " + ToonDNA.BoyShorts[x].split('/', 1)[-1].split('/', 1)[-1].split('_', 1)[-1].split('_', 1)[-1].split('_', 1)[-1].split('_', 1)[-1].split('_', 1)[-1].replace(".png", "")

            self.boyPantList.append(self.l['self.boypants' + str(x)])
            self.boyPantIDs.append( x )
        for x in range(len(ToonDNA.GirlBottoms)):
            pantsTypes = ['s', 'd']
            self.l['self.girlpants' + str(x)] = DirectButton(parent=self, relief=None, text=str(x) + " - " + ToonDNA.GirlBottoms[x][0].split('/', 1)[-1].split('/', 1)[-1].replace(".png", ""), text_align=TextNode.ALeft, text_scale=0.05, text1_bg=self.textDownColor, text2_bg=self.textRolloverColor, text3_fg=self.textDisabledColor, textMayChange=1, command=self.showWordInfo, extraArgs=[x, self.word1Desc, 'pants'])

            if ToonDNA.GirlBottoms[x][0].split('/', 1)[-1].split('/', 1)[-1].startswith('apparel/') or ToonDNA.GirlBottoms[x][0].split('/', 1)[-1].split('/', 1)[-1].startswith('tiers/'):
                self.l['self.girlpants' + str(x)]["text"] = str(x) + " - " + ToonDNA.GirlBottoms[x][0].split('/', 1)[-1].split('/', 1)[-1].split('/', 1)[-1].replace(".png", "")
            elif ToonDNA.GirlBottoms[x][0].split('/', 1)[-1].split('/', 1)[-1].startswith('tt_t_chr_'):
                self.l['self.girlpants' + str(x)]["text"] = str(x) + " - " + ToonDNA.GirlBottoms[x][0].split('/', 1)[-1].split('/', 1)[-1].split('_', 1)[-1].split('_', 1)[-1].split('_', 1)[-1].split('_', 1)[-1].split('_', 1)[-1].replace(".png", "")

            #--end of eye-bleeding code--
            self.girlPantList.append(self.l['self.girlpants' + str(x)])
            self.girlPantIDs.append( x )
            self.girlPantTypes.append(pantsTypes[ToonDNA.GirlBottoms[x][1]])
        for x in range(len(ToonDNA.ClothesColors)):
            self.l['self.colors' + str(x)] = DirectButton(parent=self, relief=None, text=str(x), text_align=TextNode.ALeft, text_scale=0.05, text1_bg=self.textDownColor, text2_bg=self.textRolloverColor, text3_fg=self.textDisabledColor, textMayChange=0, command=self.showWordInfo, extraArgs=[x, self.word1Desc, 'color'])
            self.colorList.append(self.l['self.colors' + str(x)])
            self.colorIDs.append(x)

        self.shirtLabel = DirectLabel(parent=self, relief=None,
                                     text="Shirt ID: " + str(self.shirt),
                                     text_align=TextNode.ALeft, text_scale=0.06, text_wordwrap=12, pos=(-0.75, 0, 0.5))
        self.sleeveLabel = DirectLabel(parent=self, relief=None,
                                     text="Sleeve ID: " + str(self.sleeve),
                                     text_align=TextNode.ALeft, text_scale=0.06, text_wordwrap=12, pos=(-0.2, 0, 0.5))
        self.pantLabel = DirectLabel(parent=self, relief=None,
                                     text="Pants ID: " + str(self.pant),
                                     text_align=TextNode.ALeft, text_scale=0.06, text_wordwrap=12, pos=(0.35, 0, 0.5))
        self.colorSelectedLabel = DirectLabel(parent=self, relief=None,
                                              text="Color Selected: " + str(self.color),
                                              text_align=TextNode.ALeft, text_scale=0.06, text_wordwrap=12, pos=(0.35, 0, -0.65))
        pickAToonGui = loader.loadModel('phase_3.5/models/gui/matching_game_gui')

        self.colorTest = DirectButton(parent=self, relief=None, image=pickAToonGui.find('**/minnieCircle'),
                                      image_scale=0.375, image2_scale=0.4375, pos=(0.3, 0, -0.635), text_scale=0.04,
                                      text_align=TextNode.ACenter, text_pos=(-0.00625, 0.00625), text="Color\nAll", text_fg=Vec4(0, 0, 0, 0),
                                      text1_fg=Vec4(0, 0, 0, 0), text2_fg=Vec4(0, 0, 0, 1), text3_fg=Vec4(0, 0, 0, 0), command=self.showWordInfo,
                                      extraArgs=[8008135, 'huh', 'all', True])

        pickAToonGui.removeNode()
        self.colorTest.setColor(ToonDNA.ClothesColors[self.color])
        self.colorTest['text2_fg'] = Vec4(0, 0, 0, 1) + Vec4(ToonDNA.ClothesColors[self.color][0], ToonDNA.ClothesColors[self.color][1],
                                                             ToonDNA.ClothesColors[self.color][2], 1)/3

    def unload(self):
        # BEGONE, THOT!
        for x in range(len(ToonDNA.Shirts)):
            del self.l['self.shirts' + str(x)]
        for x in range(len(ToonDNA.Sleeves)):
            del self.l['self.sleeves' + str(x)]
        for x in range(len(ToonDNA.BoyShorts)):
            del self.l['self.boypants' + str(x)]
        for x in range(len(ToonDNA.GirlBottoms)):
            del self.l['self.girlpants' + str(x)]
        for x in range(len(ToonDNA.ClothesColors)):
            del self.l['self.colors' + str(x)]

        # Labels deletion
        del self.shirtLabel, self.sleeveLabel, self.pantLabel, self.colorSelectedLabel, self.colorTest

        # Destroy lists
        for list in (self.shirtScrollList, self.sleeveScrollList, self.pantScrollList1, self.pantScrollList2,
                     self.colorScrollList):
            list.destroy()
        del self.shirtScrollList, self.sleeveScrollList, self.pantScrollList1, self.pantScrollList2, self.colorScrollList

        # Destroy sliders
        for slider in (self.shirtslider, self.sleeveslider, self.pantslider1, self.pantslider2, self.colorslider):
            slider.destroy()
        del self.shirtslider, self.sleeveslider, self.pantslider1, self.pantslider2, self.colorslider

        # Destroy DNA
        for dna in (self.toggleGender, self.toggleBody, self.colorShirt, self.colorSleeve,
                    self.colorPant, self.setClothes):
            dna.destroy()
        del self.toggleGender, self.toggleBody, self.colorShirt, self.colorSleeve, self.colorPant
        del self.setClothes

        # Stopping the movie to get more popcorn
        if self.turnSeq.isPlaying():
            self.turnSeq.finish()
        del self.turnSeq
        if self.rainbowEffect.isPlaying():
            self.rainbowEffect.finish()
        del self.rainbowEffect
        self.model.removeNode()
        del self.model

    def exit(self):
        self.ignore('confirmDone')
        self.hide()

    def enter(self):
        self.ignore('confirmDone')
        self.show()

        itemTuple = (self.colorTest, self.toggleGender, self.toggleBody, self.colorSleeve,
                     self.colorShirt, self.colorPant, self.setClothes)

        if self._parent.book.safeMode:
            for item in itemTuple:
                item['state'] = DGG.DISABLED
        else:
            for item in itemTuple:
                item['state'] = DGG.NORMAL

    def createModel(self):
        if self.turnSeq.isPlaying():
            self.turnSeq.finish()
        if self.rainbowEffect.isPlaying():
            self.rainbowEffect.finish()
            self.rainbowEffect = Sequence()
        magicParallel = Parallel()
        if self.model:
            self.model.removeNode()
            del self.model
        toon = Toon.Toon()
        dna = ToonDNA.ToonDNA()
        if self.gender == 1:
            gender = 'f'
        else:
            gender = 'm'
        dna.newToon(('dls', self.torsoSize + self.torsoType, 'm', gender))
        if self.torsoType != '':
            dna.topTex = self.shirt
            dna.topTexColor = self.shirtColor
            dna.botTex = self.pant
            dna.botTexColor = self.pantColor
            dna.sleeveTex = self.sleeve
            dna.sleeveTexColor = self.sleeveColor
        toon.setDNA(dna)
        self.model = NodePath('clothing')
        if self.torsoType != '':
            pieceNames = ('**/1000/**/torso-top', '**/1000/**/sleeves', '**/1000/**/torso-bot',)
            for name in pieceNames:
                for piece in toon.findAllMatches(name):
                    piece.wrtReparentTo(self.model)
        else:
            for piece in toon.findAllMatches('**/1000/**/torso'):
                piece.wrtReparentTo(self.model)
                magicParallel.append(Sequence(
                    LerpColorInterval(piece, duration=1, color=VBase4(0.996094, 0.898438, 0.320312, 1.0)),
                    LerpColorInterval(piece, duration=1, color=VBase4(0.304688, 0.96875, 0.402344, 1.0)),
                    LerpColorInterval(piece, duration=1, color=VBase4(0.191406, 0.5625, 0.773438, 1.0)),
                    LerpColorInterval(piece, duration=0.5, color=VBase4(0.546875, 0.28125, 0.75, 1.0)),
                    LerpColorInterval(piece, duration=0.5, color=VBase4(0.933594, 0.265625, 0.28125, 1.0))
                ))
            self.rainbowEffect.append(magicParallel)
            self.rainbowEffect.loop()

        toon.delete()
        self.model.setH(180)
        self.model.reparentTo(self)
        self.model.setScale(0.125)
        self.model.setPos(0.2, 0, -0.425)
        self.model.setBin('unsorted', 0, 1)
        self.model.setDepthTest(True)
        self.model.setDepthWrite(True)
        self.turnSeq = LerpHprInterval(self.model, duration=5, hpr=(540, 0, 0), startHpr=(180, 0, 0))
        self.turnSeq.loop()

    def makeButtons(self):
        if self.torsoSize == 'l':
            b = "Long"
        elif self.torsoSize == 'm':
            b = "Med"
        else:
            b = "Short"
        if self.gender == 0:
            a = "Male"
        else:
            a = "Female"
        gui = loader.loadModel('phase_3/models/gui/pick_a_toon_gui')
        self.toggleGender = DirectButton(parent=self,
            image=(gui.find('**/QuitBtn_UP'), gui.find('**/QuitBtn_DN'), gui.find('**/QuitBtn_RLVR_default'), gui.find('**/QuitBtn_RLVR_default')), relief=None,
            text='Toggle Gender (%s)' % a, text_scale=0.04, text_pos=(0, -0.0125), scale=0.8, pos=(0.2, 0, -0.4), command=self.changeBody, extraArgs=['gender'])
        self.toggleBody = DirectButton(parent=self,
            image=(gui.find('**/QuitBtn_UP'), gui.find('**/QuitBtn_DN'), gui.find('**/QuitBtn_RLVR_default')), relief=None,
            text='Toggle Body (%s)' % b, text_scale=0.04, text_pos=(0, -0.0125), scale=0.8, pos=(0.2, 0, -0.5), command=self.changeBody, extraArgs=['body'])

        self.colorShirt = DirectButton(parent=self,
                                       image=(gui.find('**/QuitBtn_UP'), gui.find('**/QuitBtn_DN'),
                                              gui.find('**/QuitBtn_RLVR_default'), gui.find('**/QuitBtn_RLVR_default')), relief=None,
                                       text='Color Shirt', text_scale=0.065, text_pos=(0, -0.0125), scale=0.6,
                                       pos=(-0.7, 0, -0.55), command=self.showWordInfo, extraArgs=[self.color, 'huh', 'shirt', True])
        self.colorSleeve = DirectButton(parent=self,
                                       image=(gui.find('**/QuitBtn_UP'), gui.find('**/QuitBtn_DN'),
                                              gui.find('**/QuitBtn_RLVR_default'), gui.find('**/QuitBtn_RLVR_default')), relief=None,
                                       text='Color Sleeve', text_scale=0.065, text_pos=(0, -0.0125), scale=0.6,
                                       pos=(-0.45, 0, -0.55), command=self.showWordInfo,
                                       extraArgs=[self.color, 'huh', 'sleeve', True])
        self.colorPant = DirectButton(parent=self,
                                        image=(gui.find('**/QuitBtn_UP'), gui.find('**/QuitBtn_DN'),
                                               gui.find('**/QuitBtn_RLVR_default'), gui.find('**/QuitBtn_RLVR_default')), relief=None,
                                        text='Color Pants', text_scale=0.065, text_pos=(0, -0.0125), scale=0.6,
                                        pos=(-0.2, 0, -0.55), command=self.showWordInfo,
                                        extraArgs=[8008135, 'huh', 'pants', True])
        self.setClothes = DirectButton(parent=self,
                                      image=(gui.find('**/QuitBtn_UP'), gui.find('**/QuitBtn_DN'),
                                             gui.find('**/QuitBtn_RLVR_default'), gui.find('**/QuitBtn_DN')), relief=None,
                                      text='Set As Outfit', text_scale=0.05, text_pos=(0, -0.0125), scale=0.8,
                                      pos=(0, 0, -0.65), command=self.setAsClothing)
        av = base.cr.doId2do.get(base.localAvatar.doId)

    def setAsClothing(self):
        messenger.send('wakeup')
        av = base.cr.doId2do.get(base.localAvatar.doId)
        genderList = ['m', 'f']
        if av.style.gender != genderList[self.gender] and self.torsoType != '':
            self.changeBody('gender')
        newDNA = ToonDNA.ToonDNA()
        newDNA.makeFromNetString(av.style.makeNetString())
        newDNA.torso = av.style.torso[0] + self.torsoType
        newDNA.topTex = self.shirt
        newDNA.topTexColor = self.shirtColor
        newDNA.botTex = self.pant
        newDNA.botTexColor = self.pantColor
        newDNA.sleeveTex = self.sleeve
        newDNA.sleeveTexColor = self.sleeveColor
        av.updateDNA(dna=newDNA.makeNetString(), spellbook=True)

    def changeBody(self, type):
        if type == 'gender':
            if self.gender == 0:
                self.gender = 1
                try:
                    self.torsoType = self.girlPantTypes[self.pant]
                except:
                    self.torso = self.girlPantIDs[-1]
                    self.torsoType = self.girlPantTypes[-1]
                self.pantScrollList1.hide()
                self.pantslider1.hide()
                self.pantScrollList2.show()
                self.pantslider2.show()
                self.toggleGender['text'] = 'Toggle Gender (Female)'
            else:
                self.gender = 0
                self.torsoType = 's'
                self.pantScrollList2.hide()
                self.pantslider2.hide()
                self.pantScrollList1.show()
                self.pantslider1.show()
                self.toggleGender['text'] = 'Toggle Gender (Male)'
        elif type == 'body':
            if self.torsoSize == 'm':
                self.torsoSize = 'l'
                self.toggleBody['text'] = 'Toggle Body (Long)'
            elif self.torsoSize == 'l':
                self.torsoSize = 's'
                self.toggleBody['text'] = 'Toggle Body (Short)'
            else:
                self.torsoSize = 'm'
                self.toggleBody['text'] = 'Toggle Body (Med)'
        self.createModel()

    def showWordInfo(self, wordNum, desc, clothType, isColorChange=False):
        if isColorChange:
            wordNum = self.color
        if clothType == 'sleeve':
            clothList = self.sleeveList
        elif clothType == 'pants' and self.gender == 0:
            clothList = self.boyPantList
        elif clothType == 'pants' and self.gender == 1:
            clothList = self.girlPantList
        elif clothType == 'color':
            clothList = self.colorList
        elif clothType == 'all':
            pass
        else:
            clothList = self.shirtList
        if not isColorChange:
            for word in clothList:
                if word['state'] != DGG.NORMAL:
                    word['state'] = DGG.NORMAL

            wordName = clothList[wordNum]
            wordName['state'] = DGG.DISABLED

        if clothType == 'all':
            if isColorChange:
                self.sleeveColor = wordNum
                self.model.find('**/sleeves').setColor(ToonDNA.ClothesColors[wordNum], 1)
                self.pantColor = wordNum
                self.model.find('**/torso-bot').setColor(ToonDNA.ClothesColors[wordNum], 1)
                self.shirtColor = wordNum
                self.model.find('**/torso-top').setColor(ToonDNA.ClothesColors[wordNum], 1)
                self.shirtLabel['text'] = "Shirt ID: " + str(self.shirt) + ' / ' + str(self.shirtColor)
                self.sleeveLabel['text'] = "Sleeve ID: " + str(self.sleeve) + ' / ' + str(self.sleeveColor)
                self.pantLabel['text'] = "Pants ID: " + str(self.pant) + ' / ' + str(self.pantColor)

        if clothType == 'sleeve':
            if isColorChange:
                self.sleeveColor = wordNum
                self.model.find('**/sleeves').setColor(ToonDNA.ClothesColors[wordNum], 1)
            else:
                self.sleeve = wordNum
                self.model.find('**/sleeves').setTexture(loader.loadTexture(ToonDNA.Sleeves[wordNum]), 1)
        elif clothType == 'pants':
            if isColorChange:
                self.pantColor = wordNum
            else:
                self.pant = wordNum
            if self.gender == 1 and self.girlPantTypes[wordNum] != self.torsoType:
                self.torsoType = self.girlPantTypes[wordNum]
                self.createModel()
            elif self.gender == 0 and self.torsoType != 's':
                self.torsoType = 's'
                self.createModel()
            else:
                if isColorChange:
                    self.model.find('**/torso-bot').setColor(ToonDNA.ClothesColors[wordNum], 1)
                else:
                    if self.gender == 1:
                        self.model.find('**/torso-bot').setTexture(loader.loadTexture(ToonDNA.GirlBottoms[wordNum][0]), 1)
                    else:
                        self.model.find('**/torso-bot').setTexture(loader.loadTexture(ToonDNA.BoyShorts[wordNum]), 1)
        elif clothType == 'color':
            self.color = wordNum
        else:
            if isColorChange:
                self.shirtColor = wordNum
                self.model.find('**/torso-top').setColor(ToonDNA.ClothesColors[wordNum], 1)
            else:
                self.shirt = wordNum
                self.model.find('**/torso-top').setTexture(loader.loadTexture(ToonDNA.Shirts[wordNum]), 1)

        if clothType == 'shirt':
            self.shirtLabel['text'] = "Shirt ID: " + str(self.shirt)
        elif clothType == 'sleeve':
            self.sleeveLabel['text'] = "Sleeve ID: " + str(self.sleeve)
        elif clothType == 'pants':
            self.pantLabel['text'] = "Pants ID: " + str(self.pant)
        elif clothType == 'color':
            self.colorSelectedLabel['text'] = "Color Selected: " + str(self.color)
            self.colorTest.setColor(ToonDNA.ClothesColors[self.color])
            self.colorTest['text2_fg'] = Vec4(0, 0, 0, 1) + Vec4(ToonDNA.ClothesColors[self.color][0],
                                                                 ToonDNA.ClothesColors[self.color][1],
                                                                 ToonDNA.ClothesColors[self.color][2], 1)/3

    def makeScrollLists(self):
        gui = loader.loadModel('phase_3.5/models/gui/friendslist_gui')
        coolbutton = loader.loadModel('phase_3/models/gui/pick_a_toon_gui')
        self.shirtScrollList = DirectScrolledList(parent=self, relief=None, forceHeight=0.07, pos=(-0.5, 0, 0),
                                                  itemFrame_pos=(-0.237, 0, 0.41), itemFrame_scale=1.0,
                                                  itemFrame_relief=DGG.SUNKEN, itemFrame_frameSize=(-0.05,
                                                                                                    0.66,
                                                                                                    -0.4,
                                                                                                    0.07),
                                                  itemFrame_frameColor=(0.85, 0.95, 1, 1),
                                                  itemFrame_borderWidth=(0.01, 0.01), numItemsVisible=6,
                                                  items=list(self.shirtList))
        self.shirtScrollList.incButton.reparentTo(hidden)
        self.shirtScrollList.decButton.reparentTo(hidden)
        self.shirtslider = DirectSlider(parent=self, range=(len(self.shirtIDs), 0),
                                   scale=(0.7, 0.7, 0.225), pos=(-0.1, 0, 0.245),
                                   pageSize=1, orientation=DGG.VERTICAL, command=self.scrollListTo, extraArgs=[self.shirtScrollList, 'shirt'],
                                   thumb_geom=(coolbutton.find('**/QuitBtn_UP'),
                                               coolbutton.find('**/QuitBtn_DN'),
                                               coolbutton.find('**/QuitBtn_RLVR_default'),
                                               coolbutton.find('**/QuitBtn_UP')),
                                   thumb_relief=None, thumb_geom_hpr=(0, 0, -90), thumb_geom_scale=(0.35, 1, 0.5))
        self.sleeveScrollList = DirectScrolledList(parent=self, relief=None, forceHeight=0.07, pos=(0.35, 0, 0),
                                                  itemFrame_pos=(-0.237, 0, 0.41), itemFrame_scale=1.0,
                                                  itemFrame_relief=DGG.SUNKEN, itemFrame_frameSize=(-0.05,
                                                                                                    0.66,
                                                                                                    -0.4,
                                                                                                    0.07),
                                                  itemFrame_frameColor=(0.85, 0.95, 1, 1),
                                                  itemFrame_borderWidth=(0.01, 0.01), numItemsVisible=6,
                                                  items=list(self.sleeveList))
        self.sleeveScrollList.incButton.reparentTo(hidden)
        self.sleeveScrollList.decButton.reparentTo(hidden)
        self.sleeveslider = DirectSlider(parent=self, range=(len(self.sleeveIDs), 0),
                                        scale=(0.7, 0.7, 0.225), pos=(0.75, 0, 0.245),
                                        pageSize=1, orientation=DGG.VERTICAL, command=self.scrollListTo,  extraArgs=[self.sleeveScrollList, 'sleeve'],
                                        thumb_geom=(coolbutton.find('**/QuitBtn_UP'),
                                                    coolbutton.find('**/QuitBtn_DN'),
                                                    coolbutton.find('**/QuitBtn_RLVR_default'),
                                                    coolbutton.find('**/QuitBtn_UP')),
                                        thumb_relief=None, thumb_geom_hpr=(0, 0, -90), thumb_geom_scale=(0.35, 1, 0.5))
        self.pantScrollList1 = DirectScrolledList(parent=self, relief=None, forceHeight=0.07, pos=(-0.5, 0, 0),
                                                 itemFrame_pos=(-0.237, 0, -0.08), itemFrame_scale=1.0,
                                                 itemFrame_relief=DGG.SUNKEN, itemFrame_frameSize=(-0.05,
                                                                                                   0.66,
                                                                                                   -0.4,
                                                                                                   0.07),
                                                 itemFrame_frameColor=(0.85, 0.95, 1, 1),
                                                 itemFrame_borderWidth=(0.01, 0.01), numItemsVisible=6,
                                                 items=list(self.boyPantList))
        self.pantScrollList1.incButton.reparentTo(hidden)
        self.pantScrollList1.decButton.reparentTo(hidden)
        self.pantslider1 = DirectSlider(parent=self, range=(len(self.boyPantIDs), 0),
                                       scale=(0.7, 0.7, 0.225), pos=(-0.1, 0, -0.245),
                                       pageSize=1, orientation=DGG.VERTICAL, command=self.scrollListTo,
                                       extraArgs=[self.pantScrollList1, 'boypants'],
                                       thumb_geom=(coolbutton.find('**/QuitBtn_UP'),
                                                   coolbutton.find('**/QuitBtn_DN'),
                                                   coolbutton.find('**/QuitBtn_RLVR_default'),
                                                   coolbutton.find('**/QuitBtn_UP')),
                                       thumb_relief=None, thumb_geom_hpr=(0, 0, -90), thumb_geom_scale=(0.5, 1, 0.5))
        if self.gender == 1:
            self.pantScrollList1.hide()
            self.pantslider1.hide()
        self.pantScrollList2 = DirectScrolledList(parent=self, relief=None, forceHeight=0.07, pos=(-0.5, 0, 0),
                                                  itemFrame_pos=(-0.237, 0, -0.08), itemFrame_scale=1.0,
                                                  itemFrame_relief=DGG.SUNKEN, itemFrame_frameSize=(-0.05,
                                                                                                    0.66,
                                                                                                    -0.4,
                                                                                                    0.07),
                                                  itemFrame_frameColor=(0.85, 0.95, 1, 1),
                                                  itemFrame_borderWidth=(0.01, 0.01), numItemsVisible=6,
                                                  items=list(self.girlPantList))
        self.pantScrollList2.incButton.reparentTo(hidden)
        self.pantScrollList2.decButton.reparentTo(hidden)
        self.pantslider2 = DirectSlider(parent=self, range=(len(self.girlPantIDs), 0),
                                        scale=(0.7, 0.7, 0.225), pos=(-0.1, 0, -0.245),
                                        pageSize=1, orientation=DGG.VERTICAL, command=self.scrollListTo,
                                        extraArgs=[self.pantScrollList2, 'girlpants'],
                                        thumb_geom=(coolbutton.find('**/QuitBtn_UP'),
                                                    coolbutton.find('**/QuitBtn_DN'),
                                                    coolbutton.find('**/QuitBtn_RLVR_default'),
                                                    coolbutton.find('**/QuitBtn_UP')),
                                        thumb_relief=None, thumb_geom_hpr=(0, 0, -90), thumb_geom_scale=(0.5, 1, 0.5))
        if self.gender == 0:
            self.pantScrollList2.hide()
            self.pantslider2.hide()
        self.colorScrollList = DirectScrolledList(parent=self, relief=None, forceHeight=0.07, pos=(0.68, 0, 0),
                                                  itemFrame_pos=(-0.237, 0, -0.08), itemFrame_scale=1.0,
                                                  itemFrame_relief=DGG.SUNKEN, itemFrame_frameSize=(-0.05,
                                                                                                    0.33,
                                                                                                    -0.4,
                                                                                                    0.07),
                                                  itemFrame_frameColor=(0.85, 0.95, 1, 1),
                                                  itemFrame_borderWidth=(0.01, 0.01), numItemsVisible=6,
                                                  items=list(self.colorList))
        self.colorScrollList.incButton.reparentTo(hidden)
        self.colorScrollList.decButton.reparentTo(hidden)
        self.colorslider = DirectSlider(parent=self, range=(len(self.colorIDs), 0),
                                        scale=(0.7, 0.7, 0.225), pos=(0.75, 0, -0.245),
                                        pageSize=1, orientation=DGG.VERTICAL, command=self.scrollListTo,
                                        extraArgs=[self.colorScrollList, 'color'],
                                        thumb_geom=(coolbutton.find('**/QuitBtn_UP'),
                                                    coolbutton.find('**/QuitBtn_DN'),
                                                    coolbutton.find('**/QuitBtn_RLVR_default'),
                                                    coolbutton.find('**/QuitBtn_UP')),
                                        thumb_relief=None, thumb_geom_hpr=(0, 0, -90), thumb_geom_scale=(0.75, 1, 0.5))
        gui.removeNode()
        coolbutton.removeNode()


class AccTabPage1(DirectFrame):
    notify = DirectNotifyGlobal.directNotify.newCategory('AccTabPage1')

    # TODO Clean Up if possible

    def __init__(self, parent = aspect2d):
        self.textRolloverColor = Vec4(1, 1, 0, 1)
        self.textDownColor = Vec4(0.5, 0.9, 1, 1)
        self.textDisabledColor = Vec4(0.4, 0.8, 0.4, 1)
        self._parent = parent
        self.currentSizeIndex = None
        DirectFrame.__init__(self, parent=self._parent, relief=None, pos=(0.0, 0.0, 0.0), scale=(1.0, 1.0, 1.0))
        self.load()

    def load(self):
        self.model = None
        self.turnSeq = Sequence()
        self.word1Desc = DirectLabel(parent=hidden, relief=None, text='', text_align=TextNode.ALeft, text_scale=0.06, text_wordwrap=12, pos=(0.058, 0, 0))
        self.hatList = []
        self.hatIDs = []
        self.hatTexList = []
        self.hatTexIDs = []
        self.glassesList = []
        self.glassesIDs = []
        self.glassesTexList = []
        self.glassesTexIDs = []
        self.hat = 0
        self.hatTex = 0
        self.glasses = 0
        self.glassesTex = 0
        av = base.cr.doId2do.get(base.localAvatar.doId)
        self.headType = ToonDNA.toonHeadTypes.index(av.style.head)
        self.headName = ToonDNA.toonHeadTypes[self.headType]
        self.gender = av.style.gender
        self.l = locals()
        self.makeList()
        self.hatWords = list(self.hatList)
        self.hatTexWords = list(self.hatTexList)
        self.glassesWords = list(self.glassesList)
        self.glassesTexWords = list(self.glassesTexList)

        self.makeScrollLists()
        self.createModel()
        self.makeButtons()

    def scrollListTo(self, scrollList, slider):
        messenger.send('wakeup')
        if slider == 'hat':
            slider = self.hatslider
        elif slider == 'hatTex':
            slider = self.hattexslider
        elif slider == 'glasses':
            slider = self.glassesslider
        elif slider == 'glassesTex':
            slider = self.glassestexslider
        scrollList.scrollTo(int(slider['value']))

    def makeSplit(self, string):
        abble = string.split('/', 1)[-1].split('/', 1)[-1].split('_', 1)[-1].split('_', 1)[-1].split('_',1)[-1].split('_', 1)[-1].split('_', 1)[-1].split('_', 1)[-1]
        return abble

    def makeList(self):
        for x in range(len(ToonDNA.HatModels)):
            text = str(x) + " - "
            if ToonDNA.HatModels[x] == None:
                text += "No Hat"
            else:
                text += self.makeSplit(ToonDNA.HatModels[x])

            self.l['self.hats' + str(x)] = DirectButton(parent=self, relief=None, text=text, text_align=TextNode.ALeft, text_scale=0.05, text1_bg=self.textDownColor, text2_bg=self.textRolloverColor, text3_fg=self.textDisabledColor, textMayChange=1, command=self.showWordInfo, extraArgs=[x, self.word1Desc, 'hat'])

            self.l['self.hats' + str(x)]["text"] = text

            self.hatList.append(self.l['self.hats' + str(x)])
            self.hatIDs.append(x)
        for x in range(len(ToonDNA.HatTextures)):
            text = str(x) + " - "
            if ToonDNA.HatTextures[x] == None:
                text += "Normal Texture"
            else:
                text += self.makeSplit(ToonDNA.HatTextures[x].replace(".png", ""))

            self.l['self.hatTexs' + str(x)] = DirectButton(parent=self, relief=None, text=text, text_align=TextNode.ALeft, text_scale=0.05, text1_bg=self.textDownColor, text2_bg=self.textRolloverColor, text3_fg=self.textDisabledColor, textMayChange=1, command=self.showWordInfo, extraArgs=[x, self.word1Desc, 'hatTex'])

            self.l['self.hatTexs' + str(x)]["text"] = text

            self.hatTexList.append(self.l['self.hatTexs' + str(x)])
            self.hatTexIDs.append(x)
        for x in range(len(ToonDNA.GlassesModels)):
            text = str(x) + " - "
            if ToonDNA.GlassesModels[x] == None:
                text += "No Glasses"
            else:
                text += self.makeSplit(ToonDNA.GlassesModels[x])

            self.l['self.glass' + str(x)] = DirectButton(parent=self, relief=None, text=text, text_align=TextNode.ALeft, text_scale=0.05, text1_bg=self.textDownColor, text2_bg=self.textRolloverColor, text3_fg=self.textDisabledColor, textMayChange=1, command=self.showWordInfo, extraArgs=[x, self.word1Desc, 'glasses'])

            self.l['self.glass' + str(x)]["text"] = text

            self.glassesList.append(self.l['self.glass' + str(x)])
            self.glassesIDs.append(x)
        for x in range(len(ToonDNA.GlassesTextures)):
            text = str(x) + " - "
            if ToonDNA.GlassesTextures[x] == None:
                text += "Normal Texture"
            else:
                text += self.makeSplit(ToonDNA.GlassesTextures[x].replace(".png", ""))

            self.l['self.glassTexs' + str(x)] = DirectButton(parent=self, relief=None, text=text, text_align=TextNode.ALeft, text_scale=0.05, text1_bg=self.textDownColor, text2_bg=self.textRolloverColor, text3_fg=self.textDisabledColor, textMayChange=1, command=self.showWordInfo, extraArgs=[x, self.word1Desc, 'glassesTex'])


            self.l['self.glassTexs' + str(x)]["text"] = text

            self.glassesTexList.append(self.l['self.glassTexs' + str(x)])
            self.glassesTexIDs.append(x)

        self.hatLabel = DirectLabel(parent=self, relief=None,
                                     text="Hat ID: (" + str(self.hat) + ', ' + str(self.hatTex) + ", 0)",
                                     text_align=TextNode.ALeft, text_scale=0.06, text_wordwrap=12, pos=(-0.65, 0, 0.5))
        self.glassesLabel = DirectLabel(parent=self, relief=None,
                                     text="Glasses ID: (" + str(self.glasses) + ', ' + str(self.glassesTex) + ", 0)",
                                     text_align=TextNode.ALeft, text_scale=0.06, text_wordwrap=12, pos=(0.15, 0, 0.5))



    def unload(self):
        for x in range(len(ToonDNA.HatModels)):
            del self.l['self.hats' + str(x)]
        for x in range(len(ToonDNA.HatTextures)):
            del self.l['self.hatTexs' + str(x)]
        for x in range(len(ToonDNA.GlassesModels)):
            del self.l['self.glass' + str(x)]
        for x in range(len(ToonDNA.GlassesTextures)):
            del self.l['self.glassTexs' + str(x)]

        self.hatScrollList.destroy()
        self.glassesScrollList.destroy()
        self.hatTexScrollList.destroy()
        self.glassesTexScrollList.destroy()

        del self.hatLabel, self.glassesLabel, self.hatScrollList, self.glassesScrollList, self.hatTexScrollList
        del self.glassesTexScrollList

        self.hatslider.destroy()
        self.glassesslider.destroy()
        self.hattexslider.destroy()
        self.glassestexslider.destroy()
        del self.hatslider, self.glassesslider, self.hattexslider, self.glassestexslider

        self.toggleGender.destroy()
        self.toggleBody.destroy()
        self.setClothes.destroy()
        del self.toggleGender, self.toggleBody, self.setClothes

        if self.turnSeq.isPlaying():
            self.turnSeq.finish()
        del self.turnSeq
        self.model.removeNode()
        del self.model

    def exit(self):
        self.ignore('confirmDone')
        self.hide()

    def enter(self):
        self.ignore('confirmDone')
        self.show()

        if self._parent.book.safeMode:
            self.toggleGender['state'] = DGG.DISABLED
            self.toggleBody['state'] = DGG.DISABLED
            self.setClothes['state'] = DGG.DISABLED
        else:
            self.toggleGender['state'] = DGG.NORMAL
            self.toggleBody['state'] = DGG.NORMAL
            self.setClothes['state'] = DGG.NORMAL

    def createModel(self):
        if self.turnSeq.isPlaying():
            self.turnSeq.finish()
        if self.model:
            self.model.removeNode()
            del self.model

        frameGUI = loader.loadModel('phase_3.5/models/gui/fishingBook')
        toonFrame = DirectFrame(parent=self, relief=None, image=frameGUI.find('**/fram3'), pos=(0.7, 0, -0.45),
                                scale=0.0225)

        toon = Toon.Toon()
        dna = ToonDNA.ToonDNA()
        dna.newToon((self.headName, 'ms', 'm', self.gender))
        toon.setDNA(dna)
        toon.setHat(self.hat, self.hatTex, 0)
        toon.setGlasses(self.glasses, self.glassesTex, 0)
        self.model = NodePath('clothing')
        toon.getPart('head', '1000').reparentTo(self.model)
        toon.getGeomNode().hide()
        self.model.setH(180)
        self.model.reparentTo(self)
        self.model.setScale(0.125)
        self.model.setPos(0.4, 0, -0.525)
        self.model.setBin('unsorted', 0, 1)
        self.model.setDepthTest(True)
        self.model.setDepthWrite(True)
        self.turnSeq = LerpHprInterval(self.model, duration=5, hpr=(540, 0, 0), startHpr=(180, 0, 0))
        self.turnSeq.loop()

    def makeButtons(self):
        if self.gender == 'm':
            a = "Male"
        else:
            a = "Female"
        gui = loader.loadModel('phase_3/models/gui/pick_a_toon_gui')
        self.toggleGender = DirectButton(parent=self, image=(gui.find('**/QuitBtn_UP'), gui.find('**/QuitBtn_DN'),
                                                             gui.find('**/QuitBtn_RLVR_default')), relief=None,
                                         text='Toggle Gender (%s)' % a, text_scale=0.04, text_pos=(0, -0.0125),
                                         scale=0.8, pos=(-0.45, 0, -0.4), command=self.changeBody, extraArgs=['gender'])
        self.toggleBody = DirectButton(parent=self, image=(gui.find('**/QuitBtn_UP'), gui.find('**/QuitBtn_DN'),
                                                           gui.find('**/QuitBtn_RLVR_default')), relief=None,
                                       text='Toggle Head (%s)' % self.headName, text_scale=0.04, text_pos=(0, -0.0125),
                                       scale=0.8, pos=(-0.45, 0, -0.5), command=self.changeBody, extraArgs=['species'])
        self.setClothes = DirectButton(parent=self, image=(gui.find('**/QuitBtn_UP'), gui.find('**/QuitBtn_DN'),
                                                           gui.find('**/QuitBtn_RLVR_default')), relief=None,
                                       text='Set Accessories', text_scale=0.05, text_pos=(0, -0.0125), scale=0.8,
                                       pos=(-0.45, 0, -0.6), command=self.setAsClothing)

    def setAsClothing(self):
        messenger.send('wakeup')
        av = base.cr.doId2do.get(base.localAvatar.doId)
        av.updateHeadAccessories(self.hat, self.hatTex, self.glasses, self.glassesTex)

    def changeBody(self, type):
        if type == 'gender':
            if self.gender == 'm':
                self.gender = 'f'
                self.toggleGender['text'] = 'Toggle Gender (Female)'
            else:
                self.gender = 'm'
                self.toggleGender['text'] = 'Toggle Gender (Male)'
        elif type == 'species':
            self.headType = self.headType + 1
            if self.headType > 33:
                self.headType = 0
            self.headName = ToonDNA.toonHeadTypes[self.headType]
            self.toggleBody['text'] = 'Toggle Head (%s)' % self.headName
        self.createModel()

    def showWordInfo(self, wordNum, desc, clothType):
        listNum = wordNum
        if clothType == 'hat':
            clothList = self.hatList
        elif clothType == 'hatTex':
            clothList = self.hatTexList
        elif clothType == 'glasses':
            clothList = self.glassesList
        elif clothType == 'glassesTex':
            clothList = self.glassesTexList

        for word in clothList:
            if word['state'] != DGG.NORMAL:
                word['state'] = DGG.NORMAL

        wordName = clothList[listNum]
        wordName['state'] = DGG.DISABLED

        if clothType == 'hat':
            self.hat = wordNum
        elif clothType == 'hatTex':
            self.hatTex = wordNum
        elif clothType == 'glasses':
            self.glasses = wordNum
        elif clothType == 'glassesTex':
            self.glassesTex = wordNum

        self.hatLabel['text'] = "Hat ID: (" + str(self.hat) + ', ' + str(self.hatTex) + ", 0)"
        self.glassesLabel['text'] = "Glasses ID: (" + str(self.glasses) + ', ' + str(self.glassesTex) + ", 0)"
        self.createModel()

    def makeScrollLists(self):
        gui = loader.loadModel('phase_3.5/models/gui/friendslist_gui')
        coolbutton = loader.loadModel('phase_3/models/gui/pick_a_toon_gui')
        self.hatScrollList = DirectScrolledList(parent=self, relief=None, forceHeight=0.07, pos=(-0.5, 0, 0),
                                                  itemFrame_pos=(-0.237, 0, 0.41), itemFrame_scale=1.0,
                                                  itemFrame_relief=DGG.SUNKEN, itemFrame_frameSize=(-0.05,
                                                                                                    0.66,
                                                                                                    -0.4,
                                                                                                    0.07),
                                                  itemFrame_frameColor=(0.85, 0.95, 1, 1),
                                                  itemFrame_borderWidth=(0.01, 0.01), numItemsVisible=6,
                                                  items=list(self.hatList))
        self.hatScrollList.incButton.reparentTo(hidden)
        self.hatScrollList.decButton.reparentTo(hidden)
        self.hatslider = DirectSlider(parent=self, range=(len(self.hatIDs), 0),
                                   scale=(0.7, 0.7, 0.225), pos=(-0.1, 0, 0.245),
                                   pageSize=1, orientation=DGG.VERTICAL, command=self.scrollListTo, extraArgs=[self.hatScrollList, 'hat'],
                                   thumb_geom=(coolbutton.find('**/QuitBtn_UP'),
                                               coolbutton.find('**/QuitBtn_DN'),
                                               coolbutton.find('**/QuitBtn_RLVR_default'),
                                               coolbutton.find('**/QuitBtn_UP')),
                                   thumb_relief=None, thumb_geom_hpr=(0, 0, -90), thumb_geom_scale=(-0.5, 1, 0.5))
        self.hatTexScrollList = DirectScrolledList(parent=self, relief=None, forceHeight=0.07, pos=(-0.5, 0, 0),
                                                  itemFrame_pos=(-0.237, 0, -0.08), itemFrame_scale=1.0,
                                                  itemFrame_relief=DGG.SUNKEN, itemFrame_frameSize=(-0.05,
                                                                                                    0.66,
                                                                                                    -0.25,
                                                                                                    0.07),
                                                  itemFrame_frameColor=(0.85, 0.95, 1, 1),
                                                  itemFrame_borderWidth=(0.01, 0.01), numItemsVisible=4,
                                                  items=list(self.hatTexList))
        self.hatTexScrollList.incButton.reparentTo(hidden)
        self.hatTexScrollList.decButton.reparentTo(hidden)
        self.hattexslider = DirectSlider(parent=self, range=(len(self.hatTexIDs), 0),
                                        scale=(0.7, 0.7, 0.15), pos=(-0.1, 0, -0.1685),
                                        pageSize=1, orientation=DGG.VERTICAL, command=self.scrollListTo,  extraArgs=[self.hatTexScrollList, 'hatTex'],
                                        thumb_geom=(coolbutton.find('**/QuitBtn_UP'),
                                                    coolbutton.find('**/QuitBtn_DN'),
                                                    coolbutton.find('**/QuitBtn_RLVR_default'),
                                                    coolbutton.find('**/QuitBtn_UP')),
                                        thumb_relief=None, thumb_geom_hpr=(0, 0, -90), thumb_geom_scale=(0.5, 1, 0.5))
        self.glassesScrollList = DirectScrolledList(parent=self, relief=None, forceHeight=0.07, pos=(0.35, 0, 0),
                                                 itemFrame_pos=(-0.237, 0, 0.41), itemFrame_scale=1.0,
                                                 itemFrame_relief=DGG.SUNKEN, itemFrame_frameSize=(-0.05,
                                                                                                   0.66,
                                                                                                   -0.4,
                                                                                                   0.07),
                                                 itemFrame_frameColor=(0.85, 0.95, 1, 1),
                                                 itemFrame_borderWidth=(0.01, 0.01), numItemsVisible=6,
                                                 items=list(self.glassesList))
        self.glassesScrollList.incButton.reparentTo(hidden)
        self.glassesScrollList.decButton.reparentTo(hidden)
        self.glassesslider = DirectSlider(parent=self, range=(len(self.glassesIDs), 0),
                                       scale=(0.7, 0.7, 0.225), pos=(0.75, 0, 0.245),
                                       pageSize=1, orientation=DGG.VERTICAL, command=self.scrollListTo,
                                       extraArgs=[self.glassesScrollList, 'glasses'],
                                       thumb_geom=(coolbutton.find('**/QuitBtn_UP'),
                                                   coolbutton.find('**/QuitBtn_DN'),
                                                   coolbutton.find('**/QuitBtn_RLVR_default'),
                                                   coolbutton.find('**/QuitBtn_UP')),
                                       thumb_relief=None, thumb_geom_hpr=(0, 0, -90), thumb_geom_scale=(0.5, 1, 0.5))
        self.glassesTexScrollList = DirectScrolledList(parent=self, relief=None, forceHeight=0.07, pos=(0.35, 0, 0),
                                                  itemFrame_pos=(-0.237, 0, -0.08), itemFrame_scale=1.0,
                                                  itemFrame_relief=DGG.SUNKEN, itemFrame_frameSize=(-0.05,
                                                                                                    0.66,
                                                                                                    -0.25,
                                                                                                    0.07),
                                                  itemFrame_frameColor=(0.85, 0.95, 1, 1),
                                                  itemFrame_borderWidth=(0.01, 0.01), numItemsVisible=4,
                                                  items=list(self.glassesTexList))
        self.glassesTexScrollList.incButton.reparentTo(hidden)
        self.glassesTexScrollList.decButton.reparentTo(hidden)
        self.glassestexslider = DirectSlider(parent=self, range=(len(self.glassesTexIDs), 0),
                                        scale=(0.7, 0.7, 0.15), pos=(0.75, 0, -0.1685),
                                        pageSize=1, orientation=DGG.VERTICAL, command=self.scrollListTo,
                                        extraArgs=[self.glassesTexScrollList, 'glassesTex'],
                                        thumb_geom=(coolbutton.find('**/QuitBtn_UP'),
                                                    coolbutton.find('**/QuitBtn_DN'),
                                                    coolbutton.find('**/QuitBtn_RLVR_default'),
                                                    coolbutton.find('**/QuitBtn_UP')),
                                        thumb_relief=None, thumb_geom_hpr=(0, 0, -90), thumb_geom_scale=(0.5, 1, 0.5))
        gui.removeNode()
        coolbutton.removeNode()

class AccTabPage2(DirectFrame):
    notify = DirectNotifyGlobal.directNotify.newCategory('AccTabPage2')

    # TODO Clean Up if possible

    def __init__(self, parent = aspect2d):
        self.textRolloverColor = Vec4(1, 1, 0, 1)
        self.textDownColor = Vec4(0.5, 0.9, 1, 1)
        self.textDisabledColor = Vec4(0.4, 0.8, 0.4, 1)
        self._parent = parent
        self.currentSizeIndex = None
        DirectFrame.__init__(self, parent=self._parent, relief=None, pos=(0.0, 0.0, 0.0), scale=(1.0, 1.0, 1.0))
        self.load()

    def load(self):
        self.model = None
        self.turnSeq = Sequence()
        self.word1Desc = DirectLabel(parent=hidden, relief=None, text='', text_align=TextNode.ALeft, text_scale=0.06, text_wordwrap=12, pos=(0.058, 0, 0))
        self.backpackList = []
        self.backpackIDs = []
        self.backpackTexList = []
        self.backpackTexIDs = []
        self.shoesList = []
        self.shoesIDs = []
        self.shoesTexList = []
        self.shoesTexIDs = []
        self.backpack = 0
        self.backpackTex = 0
        self.shoes = 0
        self.shoesTex = 0
        self.headType = 0
        av = base.cr.doId2do.get(base.localAvatar.doId)
        self.torsoType = av.style.torso[0]
        if av.style.torso[1] == 'd':
            self.gender = 'f'
        else:
            self.gender = 'm'
        self.l = locals()
        self.makeList()
        self.backpackWords = list(self.backpackList)
        self.backpackTexWords = list(self.backpackTexList)
        self.shoesWords = list(self.shoesList)
        self.shoesTexWords = list(self.shoesTexList)

        self.makeScrollLists()
        self.createModel()
        self.makeButtons()

    def scrollListTo(self, scrollList, slider):
        messenger.send('wakeup')
        if slider == 'backpack':
            slider = self.backpackslider
        elif slider == 'backpackTex':
            slider = self.backpacktexslider
        elif slider == 'shoes':
            slider = self.shoesslider
        elif slider == 'shoesTex':
            slider = self.shoestexslider
        scrollList.scrollTo(int(slider['value']))

    def makeSplit(self, string):
        abble = string.split('/', 1)[-1].split('/', 1)[-1].split('_', 1)[-1].split('_', 1)[-1].split('_',1)[-1].split('_', 1)[-1].split('_', 1)[-1].split('_', 1)[-1]
        return abble

    def makeList(self):
        for x in range(len(ToonDNA.BackpackModels)):
            text = str(x) + " - "
            if ToonDNA.BackpackModels[x] == None:
                text += "No Backpack"
            else:
                text += self.makeSplit(ToonDNA.BackpackModels[x])

            self.l['self.backpacks' + str(x)] = DirectButton(parent=self, relief=None, text=text, text_align=TextNode.ALeft, text_scale=0.05, text1_bg=self.textDownColor, text2_bg=self.textRolloverColor, text3_fg=self.textDisabledColor, textMayChange=1, command=self.showWordInfo, extraArgs=[x, self.word1Desc, 'backpack'])

            self.l['self.backpacks' + str(x)]["text"] = text

            self.backpackList.append(self.l['self.backpacks' + str(x)])
            self.backpackIDs.append(x)
        for x in range(len(ToonDNA.BackpackTextures)):
            text = str(x) + " - "
            if ToonDNA.BackpackTextures[x] == None:
                text += "Normal Texture"
            else:
                text += self.makeSplit(ToonDNA.BackpackTextures[x].replace(".png", ""))

            self.l['self.backpackTexs' + str(x)] = DirectButton(parent=self, relief=None, text=text, text_align=TextNode.ALeft, text_scale=0.05, text1_bg=self.textDownColor, text2_bg=self.textRolloverColor, text3_fg=self.textDisabledColor, textMayChange=1, command=self.showWordInfo, extraArgs=[x, self.word1Desc, 'backpackTex'])

            self.l['self.backpackTexs' + str(x)]["text"] = text

            self.backpackTexList.append(self.l['self.backpackTexs' + str(x)])
            self.backpackTexIDs.append(x)
        for x in range(len(ToonDNA.ShoesModels)):
            text = str(x) + " - "
            if ToonDNA.ShoesModels[x] == None:
                text += "ToonA"
            else:
                text += ToonDNA.ShoesModels[x]

            self.l['self.shoe' + str(x)] = DirectButton(parent=self, relief=None, text=text, text_align=TextNode.ALeft, text_scale=0.05, text1_bg=self.textDownColor, text2_bg=self.textRolloverColor, text3_fg=self.textDisabledColor, textMayChange=1, command=self.showWordInfo, extraArgs=[x, self.word1Desc, 'shoes'])

            self.l['self.shoe' + str(x)]["text"] = text

            self.shoesList.append(self.l['self.shoe' + str(x)])
            self.shoesIDs.append(x)
        for x in range(len(ToonDNA.ShoesTextures)):
            text = str(x) + " - "
            if ToonDNA.ShoesTextures[x] == None:
                text += "ToonB"
            else:
                text += self.makeSplit(ToonDNA.ShoesTextures[x].replace(".png", ""))

            self.l['self.shoeTexs' + str(x)] = DirectButton(parent=self, relief=None, text=text, text_align=TextNode.ALeft, text_scale=0.05, text1_bg=self.textDownColor, text2_bg=self.textRolloverColor, text3_fg=self.textDisabledColor, textMayChange=1, command=self.showWordInfo, extraArgs=[x, self.word1Desc, 'shoesTex'])


            self.l['self.shoeTexs' + str(x)]["text"] = text

            self.shoesTexList.append(self.l['self.shoeTexs' + str(x)])
            self.shoesTexIDs.append(x)

        self.backpackLabel = DirectLabel(parent=self, relief=None,
                                     text="Backpack ID: (" + str(self.backpack) + ', ' + str(self.backpackTex) + ", 0)",
                                     text_align=TextNode.ALeft, text_scale=0.06, text_wordwrap=12, pos=(-0.75, 0, 0.5))
        self.shoesLabel = DirectLabel(parent=self, relief=None,
                                     text="Shoes ID: (" + str(self.shoes) + ', ' + str(self.shoesTex) + ", 0)",
                                     text_align=TextNode.ALeft, text_scale=0.06, text_wordwrap=12, pos=(0.15, 0, 0.5))



    def unload(self):
        for x in range(len(ToonDNA.BackpackModels)):
            del self.l['self.backpacks' + str(x)]
        for x in range(len(ToonDNA.BackpackTextures)):
            del self.l['self.backpackTexs' + str(x)]
        for x in range(len(ToonDNA.ShoesModels)):
            del self.l['self.shoe' + str(x)]
        for x in range(len(ToonDNA.ShoesTextures)):
            del self.l['self.shoeTexs' + str(x)]
        del self.backpackLabel
        del self.shoesLabel

        self.backpackScrollList.destroy()
        self.shoesScrollList.destroy()
        self.backpackTexScrollList.destroy()
        self.shoesTexScrollList.destroy()
        del self.backpackScrollList, self.shoesScrollList, self.backpackTexScrollList, self.shoesTexScrollList

        self.backpackslider.destroy()
        self.shoesslider.destroy()
        self.backpacktexslider.destroy()
        self.shoestexslider.destroy()
        del self.backpackslider, self.shoesslider, self.backpacktexslider, self.shoestexslider

        self.toggleGender.destroy()
        self.toggleBody.destroy()
        self.setClothes.destroy()
        del self.toggleGender, self.toggleBody, self.setClothes

        if self.turnSeq.isPlaying():
            self.turnSeq.finish()
        del self.turnSeq
        self.model.removeNode()
        del self.model

    def exit(self):
        self.ignore('confirmDone')
        self.hide()

    def enter(self):
        self.ignore('confirmDone')
        self.show()

        if self._parent.book.safeMode:
            self.toggleGender['state'] = DGG.DISABLED
            self.toggleBody['state'] = DGG.DISABLED
            self.setClothes['state'] = DGG.DISABLED
        else:
            self.toggleGender['state'] = DGG.NORMAL
            self.toggleBody['state'] = DGG.NORMAL
            self.setClothes['state'] = DGG.NORMAL

    def createModel(self):
        if self.turnSeq.isPlaying():
            self.turnSeq.finish()
        if self.model:
            self.model.removeNode()
            del self.model
        toon = Toon.Toon()
        dna = ToonDNA.ToonDNA()
        if self.headType > 33:
            self.headType = 0
        bodyEnd = 's'
        if self.gender == 'f':
            bodyEnd = 'd'
        dna.newToon(('dls', self.torsoType + bodyEnd, self.torsoType, self.gender))
        toon.setDNA(dna)
        toon.setBackpack(self.backpack, self.backpackTex, 0)
        toon.setShoes(self.shoes, self.shoesTex, 0)
        self.model = NodePath('clothing')
        toon.getPart('head', '1000').removeNode()
        toon.find('**/1000/**/neck').removeNode()
        toon.reparentTo(self.model)
        toon.loop('neutral')
        self.model.setH(180)
        self.model.reparentTo(self)
        self.model.setScale(0.1)
        self.model.setPos(0, 0, -0.525)
        self.model.setBin('unsorted', 0, 1)
        self.model.setDepthTest(True)
        self.model.setDepthWrite(True)
        self.turnSeq = LerpHprInterval(self.model, duration=5, hpr=(540, 0, 0), startHpr=(180, 0, 0))
        self.turnSeq.loop()

    def makeButtons(self):
        if self.torsoType == 'l':
            b = "Long"
        elif self.torsoType == 'm':
            b = "Med"
        else:
            b = "Short"
        if self.gender == 'f':
            a = "Skirt"
        else:
            a = "Shorts"
        gui = loader.loadModel('phase_3/models/gui/pick_a_toon_gui')
        self.toggleGender = DirectButton(parent=self,
            image=(gui.find('**/QuitBtn_UP'), gui.find('**/QuitBtn_DN'), gui.find('**/QuitBtn_RLVR_default')), relief=None,
            text='Toggle Clothes (%s)' % a, text_scale=0.04, text_pos=(0, -0.0125), scale=0.8, pos=(-0.4, 0, -0.5), command=self.changeBody, extraArgs=['gender'])
        self.toggleBody = DirectButton(parent=self,
            image=(gui.find('**/QuitBtn_UP'), gui.find('**/QuitBtn_DN'), gui.find('**/QuitBtn_RLVR_default')), relief=None,
            text='Toggle Body (%s)' % b, text_scale=0.04, text_pos=(0, -0.0125), scale=0.8, pos=(0.4, 0, -0.5), command=self.changeBody, extraArgs=['body'])
        self.setClothes = DirectButton(parent=self,
                                      image=(gui.find('**/QuitBtn_UP'), gui.find('**/QuitBtn_DN'),
                                             gui.find('**/QuitBtn_RLVR_default')), relief=None,
                                      text='Set Accessories', text_scale=0.05, text_pos=(0, -0.0125), scale=0.8,
                                      pos=(0, 0, -0.65), command=self.setAsClothing)

    def setAsClothing(self):
        messenger.send('wakeup')
        av = base.cr.doId2do.get(base.localAvatar.doId)
        av.updateBodyAccessories(self.backpack, self.backpackTex, self.shoes, self.shoesTex)

    def changeBody(self, type):
        if type == 'gender':
            if self.gender == 'f':
                self.gender = 'm'
                self.toggleGender['text'] = 'Toggle Clothes (Shorts)'
            else:
                self.gender = 'f'
                self.toggleGender['text'] = 'Toggle Clothes (Skirt)'
        elif type == 'body':
            if self.torsoType == 'm':
                self.torsoType = 'l'
                self.toggleBody['text'] = 'Toggle Body (Long)'
            elif self.torsoType == 'l':
                self.torsoType = 's'
                self.toggleBody['text'] = 'Toggle Body (Short)'
            else:
                self.torsoType = 'm'
                self.toggleBody['text'] = 'Toggle Body (Med)'
        self.createModel()

    def showWordInfo(self, wordNum, desc, clothType):
        if clothType == 'backpack':
            clothList = self.backpackList
        elif clothType == 'backpackTex':
            clothList = self.backpackTexList
        elif clothType == 'shoes':
            clothList = self.shoesList
        elif clothType == 'shoesTex':
            clothList = self.shoesTexList

        for word in clothList:
            if word['state'] != DGG.NORMAL:
                word['state'] = DGG.NORMAL

        wordName = clothList[wordNum]
        wordName['state'] = DGG.DISABLED

        if clothType == 'backpack':
            self.backpack = wordNum
        elif clothType == 'backpackTex':
            self.backpackTex = wordNum
        elif clothType == 'shoes':
            self.shoes = wordNum
        elif clothType == 'shoesTex':
            self.shoesTex = wordNum

        self.backpackLabel['text'] = "Backpack ID: (" + str(self.backpack) + ', ' + str(self.backpackTex) + ", 0)"
        self.shoesLabel['text'] = "shoes ID: (" + str(self.shoes) + ', ' + str(self.shoesTex) + ", 0)"
        self.createModel()

    def makeScrollLists(self):
        gui = loader.loadModel('phase_3.5/models/gui/friendslist_gui')
        coolbutton = loader.loadModel('phase_3/models/gui/pick_a_toon_gui')
        self.backpackScrollList = DirectScrolledList(parent=self, relief=None, forceHeight=0.07, pos=(-0.5, 0, 0),
                                                  itemFrame_pos=(-0.237, 0, 0.41), itemFrame_scale=1.0,
                                                  itemFrame_relief=DGG.SUNKEN, itemFrame_frameSize=(-0.05,
                                                                                                    0.66,
                                                                                                    -0.4,
                                                                                                    0.07),
                                                  itemFrame_frameColor=(0.85, 0.95, 1, 1),
                                                  itemFrame_borderWidth=(0.01, 0.01), numItemsVisible=6,
                                                  items=list(self.backpackList))
        self.backpackScrollList.incButton.reparentTo(hidden)
        self.backpackScrollList.decButton.reparentTo(hidden)
        self.backpackslider = DirectSlider(parent=self, range=(len(self.backpackIDs), 0),
                                   scale=(0.7, 0.7, 0.225), pos=(-0.1, 0, 0.245),
                                   pageSize=1, orientation=DGG.VERTICAL, command=self.scrollListTo, extraArgs=[self.backpackScrollList, 'backpack'],
                                   thumb_geom=(coolbutton.find('**/QuitBtn_UP'),
                                               coolbutton.find('**/QuitBtn_DN'),
                                               coolbutton.find('**/QuitBtn_RLVR_default'),
                                               coolbutton.find('**/QuitBtn_UP')),
                                   thumb_relief=None, thumb_geom_hpr=(0, 0, -90), thumb_geom_scale=(-0.5, 1, 0.5))
        self.backpackTexScrollList = DirectScrolledList(parent=self, relief=None, forceHeight=0.07, pos=(-0.5, 0, 0),
                                                  itemFrame_pos=(-0.237, 0, -0.08), itemFrame_scale=1.0,
                                                  itemFrame_relief=DGG.SUNKEN, itemFrame_frameSize=(-0.05,
                                                                                                    0.66,
                                                                                                    -0.25,
                                                                                                    0.07),
                                                  itemFrame_frameColor=(0.85, 0.95, 1, 1),
                                                  itemFrame_borderWidth=(0.01, 0.01), numItemsVisible=4,
                                                  items=list(self.backpackTexList))
        self.backpackTexScrollList.incButton.reparentTo(hidden)
        self.backpackTexScrollList.decButton.reparentTo(hidden)
        self.backpacktexslider = DirectSlider(parent=self, range=(len(self.backpackTexIDs), 0),
                                        scale=(0.7, 0.7, 0.15), pos=(-0.1, 0, -0.1685),
                                        pageSize=1, orientation=DGG.VERTICAL, command=self.scrollListTo,  extraArgs=[self.backpackTexScrollList, 'backpackTex'],
                                        thumb_geom=(coolbutton.find('**/QuitBtn_UP'),
                                                    coolbutton.find('**/QuitBtn_DN'),
                                                    coolbutton.find('**/QuitBtn_RLVR_default'),
                                                    coolbutton.find('**/QuitBtn_UP')),
                                        thumb_relief=None, thumb_geom_hpr=(0, 0, -90), thumb_geom_scale=(0.5, 1, 0.5))
        self.shoesScrollList = DirectScrolledList(parent=self, relief=None, forceHeight=0.07, pos=(0.35, 0, 0),
                                                 itemFrame_pos=(-0.237, 0, 0.41), itemFrame_scale=1.0,
                                                 itemFrame_relief=DGG.SUNKEN, itemFrame_frameSize=(-0.05,
                                                                                                   0.66,
                                                                                                   -0.4,
                                                                                                   0.07),
                                                 itemFrame_frameColor=(0.85, 0.95, 1, 1),
                                                 itemFrame_borderWidth=(0.01, 0.01), numItemsVisible=6,
                                                 items=list(self.shoesList))
        self.shoesScrollList.incButton.reparentTo(hidden)
        self.shoesScrollList.decButton.reparentTo(hidden)
        self.shoesslider = DirectSlider(parent=self, range=(len(self.shoesIDs), 0),
                                       scale=(0.7, 0.7, 0.225), pos=(0.75, 0, 0.245),
                                       pageSize=1, orientation=DGG.VERTICAL, command=self.scrollListTo,
                                       extraArgs=[self.shoesScrollList, 'shoes'],
                                       thumb_geom=(coolbutton.find('**/QuitBtn_UP'),
                                                   coolbutton.find('**/QuitBtn_DN'),
                                                   coolbutton.find('**/QuitBtn_RLVR_default'),
                                                   coolbutton.find('**/QuitBtn_UP')),
                                       thumb_relief=None, thumb_geom_hpr=(0, 0, -90), thumb_geom_scale=(0.5, 1, 0.5))
        self.shoesTexScrollList = DirectScrolledList(parent=self, relief=None, forceHeight=0.07, pos=(0.35, 0, 0),
                                                  itemFrame_pos=(-0.237, 0, -0.08), itemFrame_scale=1.0,
                                                  itemFrame_relief=DGG.SUNKEN, itemFrame_frameSize=(-0.05,
                                                                                                    0.66,
                                                                                                    -0.25,
                                                                                                    0.07),
                                                  itemFrame_frameColor=(0.85, 0.95, 1, 1),
                                                  itemFrame_borderWidth=(0.01, 0.01), numItemsVisible=4,
                                                  items=list(self.shoesTexList))
        self.shoesTexScrollList.incButton.reparentTo(hidden)
        self.shoesTexScrollList.decButton.reparentTo(hidden)
        self.shoestexslider = DirectSlider(parent=self, range=(len(self.shoesTexIDs), 0),
                                        scale=(0.7, 0.7, 0.15), pos=(0.75, 0, -0.1685),
                                        pageSize=1, orientation=DGG.VERTICAL, command=self.scrollListTo,
                                        extraArgs=[self.shoesTexScrollList, 'shoesTex'],
                                        thumb_geom=(coolbutton.find('**/QuitBtn_UP'),
                                                    coolbutton.find('**/QuitBtn_DN'),
                                                    coolbutton.find('**/QuitBtn_RLVR_default'),
                                                    coolbutton.find('**/QuitBtn_UP')),
                                        thumb_relief=None, thumb_geom_hpr=(0, 0, -90), thumb_geom_scale=(0.5, 1, 0.5))
        gui.removeNode()
        coolbutton.removeNode()
