from panda3d.core import TextNode, TransparencyAttrib
from direct.showbase import DirectObject
from direct.gui.DirectGui import *

from otp.otpgui import OTPGUIUtils
from toontown.toonbase.ToonBaseGlobal import base
from toontown.toonbase import ToontownGlobals, TTLocalizer

from direct.discord_rpc.util.utils import is_windows

from toontown.toontowngui.ToontownScrolledFrame import ToontownScrolledFrame

if is_windows():
    import re
import os
import string


class FileBrowser(DirectObject.DirectObject):

    def __init__(self, wantTransitions = True):
        self.dot = os.getcwd()

        self.prevdir = os.getcwd()

        self.selectedFile = ' '

        self.browserCreated = False
        self.browser = None
        self.fileList = None
        self.fileNameEntry = None

        self.wantTransitions = wantTransitions

    def cleanup(self):
        self.dot = None
        self.prevdir = None
        self.selectedFile = None
        self.browserCreated = None
        self.fileList = None
        self.fileNameEntry = None

        if self.browser:
            self.browser.destroy()
        del self.browser

        self.ignoreAll()
        return

    def selectDirectory(self, name, dirpath):
        self.selectedFile = ' '
        self.fileNameEntry.enterText('')
        self.cleanCanvas()
        self.dot = os.path.join(dirpath, name)
        self.createFileList(self.dot)

    def selectFile(self, name, dirpath):
        self.selectedFile = os.path.join(dirpath, name)
        self.dot = dirpath
        self.fileNameEntry.enterText(name)

    def upSelected(self):
        self.selectedFile = ' '
        self.fileNameEntry.enterText('')
        self.cleanCanvas()
        last_dir = self.dot
        self.dot = os.path.dirname(self.dot)
        if is_windows():
            # only do this for Windows, and *before* creating the file fileList
            # *nix systems should keep the '/'
            if len(last_dir) <= 3:
                self.dot = ''
        self.createFileList(self.dot)
        # might still need this?
        if len(self.dot) <= 3:
            self.dot = ''

    def enterPath(self, textentered):
        if os.path.isabs(textentered):
            words = os.path.split(textentered)
        else:
            words = (self.dot, textentered)

        if os.path.isdir(os.path.join(words[0], words[1])):
            self.selectDirectory(words[1], words[0])
        else:
            self.selectFile(words[1], words[0])
            self.openSelected()

    def openSelected(self):
        temp = self.fileNameEntry.get()
        if not temp:
            messenger.send('selectionMade', [self.dot])
            self.closeFileBrowser()
            return

        if os.path.isabs(temp):
            words = os.path.split(temp)
        else:
            words = (self.dot, temp)

        if os.path.isdir(os.path.join(words[0], words[1])):
            self.selectDirectory(words[1], words[0])
        else:
            self.selectedFile = os.path.join(words[0], words[1])
            messenger.send('selectionMade', [self.selectedFile])
            self.closeFileBrowser()

    def cancelSelected(self):
        self.selectedFile = ' '
        self.dot = self.prevdir
        self.fileNameEntry.enterText('')
        messenger.send('selectionMade', [self.selectedFile])
        self.closeFileBrowser()

    def showFileBrowser(self):
        self.browser.show()

    def closeFileBrowser(self):
        self.browser.hide()
        if self.wantTransitions:
            base.transitions.noTransitions()
        self.selectedFile = ' '
        self.fileNameEntry.enterText('')
        if hasattr(base, 'localAvatar'):
            base.localAvatar.chatMgr.setBackgroundFocus(base.controlManager.getChatDisabled(), True)
            base.controlManager.disableAlphaNumericHotkeys = False
        self.ignoreAll()

    def openFileBrowser(self):
        if hasattr(base, 'localAvatar'):
            base.localAvatar.chatMgr.setBackgroundFocus(False, True)
            base.controlManager.disableAlphaNumericHotkeys = True
        self.prevdir = self.dot
        if self.wantTransitions:
            base.transitions.fadeScreen(0.5)
        if self.browserCreated:
            self.showFileBrowser()
        else:
            self.createFileBrowser()

    def cleanCanvas(self):
        canvas = self.fileList.getCanvas()
        kids = canvas.getChildren()
        for I in range(kids.getNumPaths()):
            temp = kids.getPath(I)
            if temp.getTag('mytype') == 'button':
                temp.removeNode()

    def createFileList(self, mydir):
        self.fileList.clearItems()
        ellipse = '...'
        btns = []
        if not mydir:
            # only do drive things on Windows
            if is_windows():
                drives = re.findall(r"[A-Z]+:.*$", os.popen("mountvol /").read(), re.MULTILINE)
                drives.sort()
                for name in drives:
                    name = name.replace(':\\', '')
                    cutoffName = name[0:21]
                    if len(cutoffName) < len(name):
                        cutoffName += ellipse
                    dirbutton = DirectButton(text = cutoffName, text_scale = (0.05, 0.05), text_align = TextNode.ALeft,
                                             text_font = ToontownGlobals.getToonFont(), frameSize = (-.5, .6, -.01, .037),
                                             text_pos = (-.45, 0),
                                             frameColor = (0.9414, 1.0, 0.9414, 1.0), relief = DGG.SUNKEN,
                                             borderWidth = (0.003, 0.003), command = self.selectDirectory,
                                             extraArgs = [name + ":\\", mydir])
                    dirbutton.setTag('mytype', 'button')
                    btns.append(dirbutton)
                self.fileList.addItems(*btns)
                return
            else:
                # otherwise, assume root directory
                mydir = os.path.sep

        directoryInfo = os.walk(mydir)  # we only need this here anyways
        for dirpath, dirnames, filenames in directoryInfo:
            dirnames.sort()
            for name in dirnames:
                cutoffName = name[0:21]
                if len(cutoffName) < len(name):
                    cutoffName += ellipse
                dirbutton = DirectButton(text = cutoffName, text_scale = (0.05, 0.05), text_align = TextNode.ALeft,
                                         text_font = ToontownGlobals.getToonFont(), frameSize = (-.5, .6, -.01, .037),
                                         text_pos = (-.45, 0),
                                         frameColor = (0.9414, 1.0, 0.9414, 1.0), relief = DGG.SUNKEN,
                                         borderWidth = (0.003, 0.003), command = self.selectDirectory,
                                         extraArgs = [name, dirpath])
                dirbutton.setTag('mytype', 'button')
                btns.append(dirbutton)

            filenames.sort()
            for name in filenames:
                cutoffName = name[0:21]
                if len(cutoffName) < len(name):
                    cutoffName += ellipse
                filebutton = DirectButton(text = cutoffName, text_scale = (0.05, 0.05), text_align = TextNode.ALeft,
                                          text_font = ToontownGlobals.getToonFont(), frameSize = (-.5, .6, -.01, .037),
                                          text_pos = (-.45, 0),
                                          frameColor = (1.0, 0.9414, 0.96, 1.0), relief = DGG.SUNKEN,
                                          borderWidth = (0.003, 0.003), command = self.selectFile,
                                          extraArgs = [name, dirpath])
                filebutton.setTag('mytype', 'button')
                btns.append(filebutton)

            self.fileList.addItems(*btns)
            break

    def createFileBrowser(self):
        self.browserCreated = True

        cdrGui = loader.loadModel('phase_3.5/models/gui/tt_m_gui_sbk_codeRedemptionGui')
        guiButton = loader.loadModel('phase_3/models/gui/quit_button')
        circleModel = loader.loadModel('phase_3/models/gui/tt_m_gui_mat_nameShop')

        settingsScrollbarModel = loader.loadModel('phase_3.5/models/gui/ttoff_m_gui_sbk_generic')

        self.browser = DirectFrame(frameSize = (-0.6, 0.6, -0.8, 0.95), frameColor = (1.0, 0.98, 0.80, 1.0),
                                   relief = None, borderWidth = (0.01, 0.01), geom = DGG.getDefaultDialogGeom(),
                                   geom_scale = (1.3, 1, 1.8), geom_pos = (0, 0, 0.05),
                                   geom_color = ToontownGlobals.GlobalDialogColor, scale = 0.85)
        self.browser.setBin('gui-popup', 0)

        self.fileList = ToontownScrolledFrame(parent = self.browser, relief = DGG.SUNKEN,
                                              itemMargin = (0.0, -.06),
                                              itemPadding = 0.05,
                                              pos = (0, 0, 0.1),
                                              useItemBoundsForPadding = False,
                                              width = 0.65,
                                              height = 0.55,
                                              manageScrollBars = False,
                                              verticalScroll_frameColor = (0, 0, 0, 0),
                                              verticalScroll_manageButtons = False,
                                              verticalScroll_thumb_geom = (
                                                  settingsScrollbarModel.find('**/scrollbar_normal'),
                                                  settingsScrollbarModel.find('**/scrollbar_press'),
                                                  settingsScrollbarModel.find('**/scrollbar_hover')),
                                              verticalScroll_thumb_geom_scale = OTPGUIUtils.getImageScale(151, 399, 0.125),
                                              verticalScroll_thumb_relief = None,
                                              verticalScroll_resizeThumb = False,
                                              verticalScroll_decButton_relief = None,
                                              verticalScroll_incButton_relief = None)

        self.fileNameBox = DirectFrame(parent = self.browser, relief = None,
                                       image = cdrGui.find('**/tt_t_gui_sbk_cdrCodeBox2'), pos = (0.1, 0, -0.525),
                                       scale = (1.0, 0.6, 0.6))

        self.fileNameEntry = DirectEntry(parent = self.browser, relief = None, borderWidth = (0.01, 0.01), text = "",
                                         text_font = ToontownGlobals.getToonFont(), pos = (-0.23, 0, -0.53), scale = 0.05,
                                         width = 13, command = self.enterPath, numLines = 1, focus = 1, overflow = 1)
        self.fileNameLabel = DirectLabel(parent = self.browser, text = TTLocalizer.FileBrowserFileName,
                                         text_scale = (0.05, 0.05), text_font = ToontownGlobals.getToonFont(),
                                         frameColor = (1.0, 0.98, 0.80, 1.0), pos = (-0.425, 0, -0.525))

        cancelButton = DirectButton(parent = self.browser, frameSize = (-0.11, 0.11, -0.05, 0.05), relief = None,
                                    image = (guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'),
                                             guiButton.find('**/QuitBtn_RLVR')),
                                    borderWidth = (0.01, 0.01), pos = (-0.25, 0, -0.7),
                                    text = TTLocalizer.lCancel, text_pos = (0, -0.02), text_scale = (0.07, 0.07),
                                    text_font = ToontownGlobals.getToonFont(), command = self.cancelSelected)

        openButton = DirectButton(parent = self.browser, frameSize = (-0.11, 0.11, -0.05, 0.05), relief = None,
                                  image = (guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'),
                                           guiButton.find('**/QuitBtn_RLVR')),
                                  borderWidth = (0.01, 0.01), pos = (0.25, 0, -0.7),
                                  text = TTLocalizer.FileBrowserOpen, text_pos = (-0.01, -0.02), text_scale = (0.07, 0.07),
                                  text_font = ToontownGlobals.getToonFont(), command = self.openSelected)

        higherButton = DirectButton(parent = self.browser, frameSize = (-0.3, 0.3, -0.04, 0.04), relief = None,
                                    image = (guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'),
                                             guiButton.find('**/QuitBtn_RLVR')),
                                    borderWidth = (0.01, 0.01), pos = (0, 0, 0.85),
                                    text = TTLocalizer.FileBrowserUp, text_pos = (-0.01, -0.015), text_scale = (0.05, 0.05),
                                    text_font = ToontownGlobals.getToonFont(), command = self.upSelected)

        self.createFileList(self.dot)

        cdrGui.removeNode()
        guiButton.removeNode()
        circleModel.removeNode()

        settingsScrollbarModel.removeNode()
