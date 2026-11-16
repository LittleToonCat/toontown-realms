from direct.gui.DirectGui import *
from panda3d.core import *
from panda3d.toontown import *
from direct.task.Task import Task
from direct.fsm import StateData
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import TTLocalizer, ClientSettings, HotkeySettings
from toontown.toontowngui import TTDialog
from toontown.toonbase.DisplayOptions import DisplayOptions
from toontown.toontowngui.SettingsGUI import DropdownOption, DisplayModeDropdown


class DisplaySettingsDialog(DirectFrame, StateData.StateData):
    ApplyTimeoutSeconds = 15
    TimeoutCountdownTask = 'DisplaySettingsTimeoutCountdown'
    WindowedMode = 0
    FullscreenMode = 1
    EmbeddedMode = 2
    notify = DirectNotifyGlobal.directNotify.newCategory('DisplaySettingsDialog')
    settingsButtonsModel = loader.loadModel('phase_3/models/gui/ttoff_m_gui_opts_buttons', allowInstance = True)
    settingsDropdownModel = loader.loadModel('phase_3/models/gui/ttoff_m_gui_opts_dropdown', allowInstance = True)
    colorPickerModel = loader.loadModel("phase_3/models/gui/ttoff_m_gui_opts_colorpicker", allowInstance = True)

    def __init__(self, parent = aspect2d):
        DirectFrame.__init__(self, parent = parent, pos = (0, 0, 0), relief = None,
                             image=self.colorPickerModel.find("**/temp_bg"),
                             image_scale = (1.7, 1, 1.3), image_pos = (0, 0, -0.05),
                             text = TTLocalizer.DisplaySettingsTitle,
                             text_scale = 0.12, text_pos = (0, 0.4), borderWidth = (0.01, 0.01))
        StateData.StateData.__init__(self, 'display-settings-done')
        self.setBin('gui-popup', 0)
        self.initialiseoptions(DisplaySettingsDialog)

    def unload(self):
        if self.isLoaded == 0:
            return None
        self.isLoaded = 0
        self.exit()
        DirectFrame.destroy(self)

    def load(self):
        if self.isLoaded == 1:
            return None
        self.isLoaded = 1
        self.anyChanged = 0
        self.apiChanged = 0
        self.displayMode = ClientSettings.DisplayMode.get()
        self.screenSizes = []
        displayInfo = base.pipe.getDisplayInformation()
        for i in range(displayInfo.getTotalDisplayModes()):
            width = displayInfo.getDisplayModeWidth(i)
            height = displayInfo.getDisplayModeHeight(i)
            if (width, height) not in self.screenSizes:
                self.screenSizes.append((width, height))

        if not self.screenSizes:
            self.screenSizes = [(640, 480),
                                (800, 600),
                                (1024, 768),
                                (1280, 1024),
                                (1600, 1200)]

        guiButton = loader.loadModel('phase_3/models/gui/quit_button')
        gui = loader.loadModel('phase_3.5/models/gui/friendslist_gui')
        nameShopGui = loader.loadModel('phase_3/models/gui/nameshop_gui')

        self.introText = DirectLabel(parent = self, relief = None, scale = TTLocalizer.DSDintroText,
                                     text = TTLocalizer.DisplaySettingsIntro,
                                     text_wordwrap = TTLocalizer.DSDintroTextWordwrap, text_align = TextNode.ALeft,
                                     pos = (-0.725, 0, 0.3))
        self.introTextSimple = DirectLabel(parent = self, relief = None, scale = 0.06,
                                           text = TTLocalizer.DisplaySettingsIntroSimple, text_wordwrap = 25,
                                           text_align = TextNode.ALeft, pos = (-0.725, 0, 0.3))
        self.apiLabel = DirectLabel(parent = self, relief = None, scale = 0.06, text = TTLocalizer.DisplaySettingsApi,
                                    text_align = TextNode.ARight, pos = (-0.08, 0, 0))
        self.apiMenu = DirectOptionMenu(parent = self, relief = DGG.RAISED, scale = 0.06, items = ['x'],
                                        pos = (0, 0, 0))
        self.screenSizeLabel = DirectLabel(parent = self, relief = None, scale = 0.06,
                                           text = TTLocalizer.DisplaySettingsResolution, text_align = TextNode.ARight,
                                           pos = (-0.08, 0, 0.0))
        self.screenSizeLeftArrow = DirectButton(parent = self, relief = None,
                                                image = (self.settingsButtonsModel.find('**/arrow_l_normal'),
                                                         self.settingsButtonsModel.find('**/arrow_l_click'),
                                                         self.settingsButtonsModel.find('**/arrow_l_hover'),
                                                         self.settingsButtonsModel.find('**/arrow_l_disabled')),
                                                scale = 0.095, pos = (0.02, 0, 0.015), pressEffect = False,
                                                command = self.__doScreenSizeLeft)
        self.screenSizeRightArrow = DirectButton(parent = self, relief = None,
                                                 image = (self.settingsButtonsModel.find('**/arrow_r_normal'),
                                                          self.settingsButtonsModel.find('**/arrow_r_click'),
                                                          self.settingsButtonsModel.find('**/arrow_r_hover'),
                                                          self.settingsButtonsModel.find('**/arrow_r_disabled')),
                                                 scale = 0.095, pos = (0.56, 0, 0.015), pressEffect = False,
                                                 command = self.__doScreenSizeRight)
        self.screenSizeValueText = DirectLabel(parent = self,
                                               image = self.settingsDropdownModel.find('**/dropdown_middle_normal'),
                                               image_scale = (.4, 1, .11), image_pos = (0, 0, 0.0145),
                                               relief = None, text = 'x', text_align = TextNode.ACenter,
                                               text_scale = 0.06, pos = (0.29, 0, 0))

        self.displayModeLabel = DirectLabel(parent = self, relief = None, scale = 0.06,
                                            text = TTLocalizer.DisplaySettingsMode,
                                            text_align = TextNode.ARight, pos = (-0.08, 0, -0.121))

        self.displayModeDropdown = DisplayModeDropdown(parent = self, updateCommand = self.updateWindowed)
        self.displayModeDropdown.setPos(0.29, 0, -0.115)
        self.apply = DirectButton(parent = self, relief = None,
                                  image = (self.settingsButtonsModel.find('**/button_green_up'),
                                           self.settingsButtonsModel.find('**/button_green_down'),
                                           self.settingsButtonsModel.find('**/button_green_rollover')),
                                  image_scale = (.4, 1, .11), text = TTLocalizer.DisplaySettingsApply,
                                  text_scale = 0.06, pressEffect = False,
                                  text_pos = (0.0, -0.015), pos = (0, 0, -0.59), command = self.__apply)
        self.cancel = DirectButton(parent = self, relief = None,
                                   image = (self.settingsButtonsModel.find('**/close_button_normal'),
                                            self.settingsButtonsModel.find('**/close_button_click'),
                                            self.settingsButtonsModel.find('**/close_button_hover')),
                                   image_scale = .14, pressEffect = False,
                                   pos = (0.7, 0, 0.46), command = self.__cancel)
        guiButton.removeNode()
        gui.removeNode()
        nameShopGui.removeNode()
        self.hide()

    def enter(self, changeDisplaySettings, changeDisplayAPI, inBook = True):
        if self.isEntered == 1:
            return None
        self.isEntered = 1
        if self.isLoaded == 0:
            self.load()
        self.applyDialog = None
        self.timeoutDialog = None
        self.restoreDialog = None
        self.revertDialog = None
        self.inBook = inBook
        base.transitions.fadeScreen(0.5)
        if not self.inBook:
            self.reparentTo(aspect2dp)
        properties = base.win.getProperties()
        self.screenSizeIndex = self.chooseClosestScreenSize(properties.getXSize(), properties.getYSize())
        self.isFullscreen = properties.getFullscreen()
        self.updateApiMenu(changeDisplaySettings, changeDisplayAPI)
        self.updateScreenSize()
        if changeDisplaySettings:
            self.introText.show()
            self.introTextSimple.hide()
            if changeDisplayAPI and len(self.apis) > 1:
                self.apiLabel.show()
                self.apiMenu.show()
            else:
                self.apiLabel.hide()
                self.apiMenu.hide()
        else:
            self.introText.hide()
            self.introTextSimple.show()
            self.apiLabel.hide()
            self.apiMenu.hide()
        self.anyChanged = 0
        self.apiChanged = 0
        self.show()
        self.accept(HotkeySettings.ExitActivity.getPressed(),
                    self.__cancel)

    def exit(self):
        if self.isEntered == 0:
            return None
        self.isEntered = 0
        self.cleanupDialogs()
        if self.inBook:
            base.transitions.noTransitions()
        taskMgr.remove(self.TimeoutCountdownTask)
        self.ignoreAll()
        self.hide()
        messenger.send(self.doneEvent, [self.anyChanged, self.apiChanged])

    def cleanupDialogs(self):
        if self.applyDialog != None:
            self.applyDialog.cleanup()
            self.applyDialog = None
        if self.timeoutDialog != None:
            self.timeoutDialog.cleanup()
            self.timeoutDialog = None
        if self.restoreDialog != None:
            self.restoreDialog.cleanup()
            self.restoreDialog = None
        if self.revertDialog != None:
            self.revertDialog.cleanup()
            self.revertDialog = None

    def updateApiMenu(self, changeDisplaySettings, changeDisplayAPI):
        self.apis = []
        self.apiPipes = []
        if changeDisplayAPI:
            base.makeAllPipes()
        for pipe in base.pipeList:
            if pipe.isValid():
                self.apiPipes.append(pipe)
                self.apis.append(pipe.getInterfaceName())

        self.apiMenu['items'] = self.apis
        self.apiMenu.set(base.pipe.getInterfaceName())

    def updateWindowed(self, mode):
        self.displayMode = mode

    def updateScreenSize(self):
        xSize, ySize = self.screenSizes[self.screenSizeIndex]
        self.screenSizeValueText['text'] = '%s x %s' % (xSize, ySize)
        if self.screenSizeIndex > 0:
            self.screenSizeLeftArrow.show()
        else:
            self.screenSizeLeftArrow.hide()
        if self.screenSizeIndex < len(self.screenSizes) - 1:
            self.screenSizeRightArrow.show()
        else:
            self.screenSizeRightArrow.hide()

    def chooseClosestScreenSize(self, currentXSize, currentYSize):
        for i in range(len(self.screenSizes)):
            xSize, ySize = self.screenSizes[i]
            if currentXSize == xSize and currentYSize == ySize:
                return i

        currentCount = currentXSize * currentYSize
        bestDiff = None
        bestI = None
        for i in range(len(self.screenSizes)):
            xSize, ySize = self.screenSizes[i]
            diff = abs(xSize * ySize - currentCount)
            if bestI == None or diff < bestDiff:
                bestI = i
                bestDiff = diff

        return bestI

    def __doWindowed(self, value):
        self.displayMode = self.WindowedMode
        self.updateWindowed()

    def __doFullscreen(self, value):
        self.displayMode = self.FullscreenMode
        self.updateWindowed()

    def __doEmbedded(self, value):
        self.displayMode = self.EmbeddedMode
        self.updateWindowed()

    def __doScreenSizeLeft(self):
        if self.screenSizeIndex > 0:
            self.screenSizeIndex = self.screenSizeIndex - 1
            self.updateScreenSize()

    def __doScreenSizeRight(self):
        if self.screenSizeIndex < len(self.screenSizes) - 1:
            self.screenSizeIndex = self.screenSizeIndex + 1
            self.updateScreenSize()

    def __apply(self):
        self.cleanupDialogs()
        self.clearBin()
        self.applyDialog = TTDialog.TTDialog(dialogName = 'DisplaySettingsApply', style = TTDialog.TwoChoice,
                                             text = TTLocalizer.DisplaySettingsApplyWarning % self.ApplyTimeoutSeconds,
                                             text_wordwrap = 15, command = self.__applyDone)
        self.applyDialog.setBin('gui-popup', 0)
        if not self.inBook:
            self.reparentTo(aspect2d)
            self.applyDialog.reparentTo(aspect2dp, 100)

    def __applyDone(self, command):
        self.applyDialog.cleanup()
        self.applyDialog = None
        self.setBin('gui-popup', 0)
        if not self.inBook:
            self.reparentTo(aspect2dp)
        base.transitions.fadeScreen(0.5)
        if command != DGG.DIALOG_OK:
            return
        self.origPipe = base.pipe
        self.origProperties = base.win.getProperties()
        pipe = self.apiPipes[self.apiMenu.selectedIndex]
        properties = WindowProperties()
        xSize, ySize = self.screenSizes[self.screenSizeIndex]
        properties.setSize(xSize, ySize)
        properties.setFullscreen(self.displayMode == self.FullscreenMode)
        fullscreen = self.displayMode == self.FullscreenMode
        embedded = self.displayMode == self.EmbeddedMode
        if embedded:
            if DisplayOptions.isEmbeddedPossible():
                pass
            else:
                self.notify.warning('how was the player able to choose embedded')
                embedded = False
        if not self.changeDisplayProperties(pipe, xSize, ySize, self.displayMode, embedded):
            self.__revertBack(1)
            return
        self.clearBin()
        self.timeoutDialog = TTDialog.TTDialog(dialogName = 'DisplaySettingsTimeout', style = TTDialog.TwoChoice,
                                               text = TTLocalizer.DisplaySettingsAccept % self.ApplyTimeoutSeconds,
                                               text_wordwrap = 15, command = self.__timeoutDone)
        self.timeoutDialog.setBin('gui-popup', 0)
        if not self.inBook:
            self.reparentTo(aspect2d)
            self.timeoutDialog.reparentTo(aspect2dp, 100)
        self.timeoutRemaining = self.ApplyTimeoutSeconds
        self.timeoutStart = None
        taskMgr.add(self.__timeoutCountdown, self.TimeoutCountdownTask)

    def changeDisplayProperties(self, pipe, width, height, displayMode = 0, embedded = False):
        result = False
        self.notify.info('changeDisplayProperties')
        fullscreen = displayMode == 1
        borderless = displayMode == 2
        self.current_pipe = base.pipe
        self.current_properties = WindowProperties(base.win.getProperties())
        properties = self.current_properties
        self.notify.debug('DISPLAY PREVIOUS:')
        self.notify.debug('  BORDERLESS: %s' % bool(properties.getUndecorated()))
        self.notify.debug('  FULLSCREEN: %s' % bool(properties.getFullscreen()))
        self.notify.debug('  X SIZE:     %s' % properties.getXSize())
        self.notify.debug('  Y SIZE:     %s' % properties.getYSize())
        self.notify.debug('DISPLAY REQUESTED:')
        self.notify.debug('  BORDERLESS: %s' % bool(borderless))
        self.notify.debug('  FULLSCREEN: %s' % bool(fullscreen))
        self.notify.debug('  X SIZE:     %s' % width)
        self.notify.debug('  Y SIZE:     %s' % height)
        if self.current_pipe == pipe \
                and bool(self.current_properties.getParentWindow()) == bool(embedded) \
                and self.current_properties.getFullscreen() == fullscreen \
                and self.current_properties.getUndecorated() == borderless \
                and self.current_properties.getXSize() == width \
                and self.current_properties.getYSize() == height:
            self.notify.info('DISPLAY NO CHANGE REQUIRED')
        else:
            properties = WindowProperties()
            properties.setSize(width, height)
            properties.setFullscreen(fullscreen)
            properties.setUndecorated(borderless)
            properties.setParentWindow(0)
            original_sort = base.win.getSort()
            if self.resetDisplayProperties(pipe, properties):
                self.notify.debug('DISPLAY CHANGE SET')
                properties = base.win.getProperties()
                self.notify.debug('DISPLAY ACHIEVED:')
                self.notify.debug('  EMBEDDED:   %s' % bool(properties.getParentWindow()))
                self.notify.debug('  FULLSCREEN: %s' % bool(properties.getFullscreen()))
                self.notify.debug('  X SIZE:     %s' % properties.getXSize())
                self.notify.debug('  Y SIZE:     %s' % properties.getYSize())
                if bool(properties.getParentWindow()) == bool(embedded) \
                        and properties.getFullscreen() == fullscreen \
                        and properties.getUndecorated() == borderless \
                        and properties.getXSize() == width \
                        and properties.getYSize() == height:
                    self.notify.info('DISPLAY CHANGE VERIFIED')
                    result = True
                else:
                    self.notify.warning('DISPLAY CHANGE FAILED, RESTORING PREVIOUS DISPLAY')
            else:
                self.notify.warning('DISPLAY CHANGE FAILED')
            base.win.setSort(original_sort)
            base.graphicsEngine.renderFrame()
            base.graphicsEngine.renderFrame()
        return result

    def __timeoutCountdown(self, task):
        if self.timeoutStart == None:
            self.timeoutStart = globalClock.getRealTime()
        elapsed = int(globalClock.getFrameTime() - self.timeoutStart)
        remaining = max(self.ApplyTimeoutSeconds - elapsed, 0)
        if remaining < self.timeoutRemaining:
            self.timeoutRemaining = remaining
            self.timeoutDialog['text'] = (TTLocalizer.DisplaySettingsAccept % remaining,)
        if remaining == 0:
            self.__timeoutDone('cancel')
            return Task.done
        return Task.cont

    def __timeoutDone(self, command):
        taskMgr.remove(self.TimeoutCountdownTask)
        self.timeoutDialog.cleanup()
        self.timeoutDialog = None
        self.setBin('gui-popup', 0)
        if not self.inBook:
            self.reparentTo(aspect2dp)
        base.transitions.fadeScreen(0.5)
        if command == DGG.DIALOG_OK:
            self.anyChanged = 1
            self.exit()
            return
        self.__revertBack(0)

    def __revertBack(self, reason):
        if not self.resetDisplayProperties(self.origPipe, self.origProperties):
            self.notify.warning("Couldn't restore original display settings!")
            base.panda3dRenderError()
        self.clearBin()
        if reason == 0:
            revertText = TTLocalizer.DisplaySettingsRevertUser
        else:
            revertText = TTLocalizer.DisplaySettingsRevertFailed
        self.revertDialog = TTDialog.TTDialog(dialogName = 'DisplaySettingsRevert', style = TTDialog.Acknowledge,
                                              text = revertText, text_wordwrap = 15, command = self.__revertDone)
        self.revertDialog.setBin('gui-popup', 0)
        if not self.inBook:
            self.reparentTo(aspect2d)
            self.revertDialog.reparentTo(aspect2dp, 100)

    def __revertDone(self, command):
        self.revertDialog.cleanup()
        self.revertDialog = None
        self.setBin('gui-popup', 0)
        if not self.inBook:
            self.reparentTo(aspect2dp)
        base.transitions.fadeScreen(0.5)

    def __cancel(self):
        self.exit()

    def resetDisplayProperties(self, pipe, properties):
        if base.win:
            currentProperties = base.win.getProperties()
            gsg = base.win.getGsg()
        else:
            currentProperties = WindowProperties.getDefault()
            gsg = None
        newProperties = WindowProperties(currentProperties)
        newProperties.addProperties(properties)
        if base.pipe != pipe:
            self.apiChanged = 1
            gsg = None
        if gsg == None or currentProperties.getFullscreen() != newProperties.getFullscreen() \
                or currentProperties.getUndecorated() != newProperties.getUndecorated() \
                or currentProperties.getParentWindow() != newProperties.getParentWindow():
            self.notify.debug('window properties: %s' % properties)
            self.notify.debug('gsg: %s' % gsg)
            base.pipe = pipe
            if not base.openMainWindow(props = properties, gsg = gsg, keepCamera = True):
                self.notify.warning('OPEN MAIN WINDOW FAILED')
                return 0
            self.notify.info('OPEN MAIN WINDOW PASSED')
            base.disableShowbaseMouse()
            NametagGlobals.setCamera(base.cam)
            NametagGlobals.setMouseWatcher(base.mouseWatcherNode)
            base.graphicsEngine.renderFrame()
            base.graphicsEngine.renderFrame()
            base.graphicsEngine.openWindows()
            if base.win.isClosed():
                self.notify.info('Window did not open, removing.')
                base.closeWindow(base.win)
                return 0
        else:
            self.notify.debug('Adjusting properties')
            base.win.requestProperties(properties)
            base.graphicsEngine.renderFrame()
        return 1

    def isCurrentlyEmbedded(self):
        result = False
        if base.win.getProperties().getParentWindow():
            result = True
        return result
