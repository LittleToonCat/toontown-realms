import re
import traceback

from direct.gui import DirectGuiGlobals
from typing import List, Optional, Union, Tuple

from direct.gui.DirectButton import DirectButton
from direct.gui.DirectEntry import DirectEntry
from direct.gui.DirectFrame import DirectFrame
from direct.gui.OnscreenText import OnscreenText
from direct.task import Task
from panda3d.core import TextNode, NodePath, Vec3, VBase4

from direct.interval.MetaInterval import Parallel

from otp.otpbase.PythonUtil import bound
from otp.otpgui import OTPGUIUtils
from toontown.datapack.DataPackManager import DataPackManager
from toontown.moviemaker.MovieMakerGUI import MovieMakerGUI
from toontown.sandbox import PropGlobals
from toontown.toonbase import TTLocalizer, ClientSettings
from toontown.toonbase.ToonBaseGlobal import base
from toontown.toontowngui import TTDialog
from toontown.toontowngui.AnimatedButton import AnimatedButton
from toontown.toontowngui.ToontownScrolledGridFrame import ToontownScrolledGridFrame

cdrGui = base.loader.loadModel('phase_3.5/models/gui/tt_m_gui_sbk_codeRedemptionGui')  # type: NodePath


class NumberEntry(DirectEntry):

    def __init__(self, parent = None, **kwargs):
        self.value = 0.0
        optiondefs = (
            ('relief', None, None),
            ('image_scale', (0.6, 1.0, 0.75), None),
            ('text_scale', 0.06, None),
            ('text_pos', (0.0, -0.005), None),
            ('text_align', TextNode.ACenter, None),
            ('image', cdrGui.find('**/tt_t_gui_sbk_cdrCodeBox'), None),
            ('width', 5, None),
            ('onChange', None, None),
            ('onChangeExtraArgs', None, None),
            ('incrementScale', 1.0, None),
            ('minMax', (-65536, 65536), None),
            ('numberType', float, None),
            ('startValue', 0.0, self.__setStartValue)
        )

        self.defineoptions(kwargs, optiondefs)
        DirectEntry.__init__(self, parent)
        self.initialiseoptions(NumberEntry)

        self.bind(DirectGuiGlobals.TYPE, self.__onType)

        self.lButton = AnimatedButton(
                parent = self,
                relief = None,
                pos = (-.3, 0, 0),
                scale = 0.08,
                image = (
                    PropGlobals.PropUi.find('**/arrow_l_normal'),
                    PropGlobals.PropUi.find('**/arrow_l_click'),
                    PropGlobals.PropUi.find('**/arrow_l_hover'),
                    PropGlobals.PropUi.find('**/arrow_l_disabled')
                )
        )
        self.rButton = AnimatedButton(
                parent = self,
                relief = None,
                pos = (.3, 0, 0),
                scale = 0.08,
                image = (
                    PropGlobals.PropUi.find('**/arrow_r_normal'),
                    PropGlobals.PropUi.find('**/arrow_r_click'),
                    PropGlobals.PropUi.find('**/arrow_r_hover'),
                    PropGlobals.PropUi.find('**/arrow_r_disabled')
                )
        )

        self.lButton.bind(DirectGuiGlobals.B1PRESS, self.__lButtonPress)
        self.lButton.bind(DirectGuiGlobals.B1RELEASE, self.__lButtonRelease)

        self.rButton.bind(DirectGuiGlobals.B1PRESS, self.__rButtonPress)
        self.rButton.bind(DirectGuiGlobals.B1RELEASE, self.__rButtonRelease)

    def __lButtonPress(self, e = None):
        messenger.send('wakeup')
        self.__setValue(self.value-self['incrementScale'])
        task = self.addTask(self.__runCounter, 'counterTask')
        task.delayTime = 0.4
        task.prevTime = 0.0
        task.delta = -self['incrementScale']

    def __lButtonRelease(self, e = None):
        messenger.send('wakeup')
        self.removeTask('counterTask')

    def __rButtonPress(self, e = None):
        messenger.send('wakeup')
        self.__setValue(self.value+self['incrementScale'])
        task = self.addTask(self.__runCounter, 'counterTask')
        task.delayTime = 0.4
        task.prevTime = 0.0
        task.delta = self['incrementScale']

    def __rButtonRelease(self, e = None):
        messenger.send('wakeup')
        self.removeTask('counterTask')

    def __runCounter(self, task):
        # type: (Task) -> int
        """
        Performs the task of the arrow buttons
        The longer its held down, the faster it moves
        """
        if task.time - task.prevTime < task.delayTime:
            return Task.cont
        else:
            task.delayTime = max(0.02, task.delayTime * 0.75)
            task.prevTime = task.time
            self.__setValue(self.value + task.delta)
            return Task.cont

    def __setStartValue(self):
        self.__setValue(self['startValue'])

    def __setValue(self, value):
        # type: (float) -> None
        self.value = bound(self['numberType'](value), *self['minMax'])
        self.__valueChanged()
        self.set(str(self.value))

    def __valueChanged(self):
        if self['onChange']:
            if self['onChangeExtraArgs']:
                self['onChange'](self.value, *self['onChangeExtraArgs'])
            else:
                self['onChange'](self.value)

    def __onType(self, e = None):
        """
        Runs a simple regex filter to make sure we are only writing floats
        """
        try:
            if not self.get() in ('.', '-'):
                reg = re.findall(r'[-+]?\d*\.\d+|[-+]?\d+\.?', self.get())
                if len(reg) == 0:
                    self.set('')  # Just clear the field if theres nothing valid in it
                    return
                validatedValue = reg[0]
                input = bound(self['numberType'](validatedValue), *self['minMax'])
                self.set(str(input))
            else:
                input = bound(self['numberType'](self.get()), *self['minMax'])
            self.value = input
            self.__valueChanged()
        except:
            if __debug__:
                traceback.print_exc()
            return

    def destroy(self):
        self.removeAllTasks()
        DirectEntry.destroy(self)


class Dropdown(DirectButton):
    """
    Dropdown Button w/ menu
    Panda's DirectOptionMenu is garbage. so let's just do this
    """
    textures = (
        # main
        (PropGlobals.PropUi.find('**/dropdown_button_normal'),
         PropGlobals.PropUi.find('**/dropdown_button_click'),
         PropGlobals.PropUi.find('**/dropdown_button_hover')),
        # top
        (PropGlobals.PropUi.find('**/dropdown_top_normal'),
         PropGlobals.PropUi.find('**/dropdown_top_click'),
         PropGlobals.PropUi.find('**/dropdown_top_hover')),
        # middle
        (PropGlobals.PropUi.find('**/dropdown_middle_normal'),
         PropGlobals.PropUi.find('**/dropdown_middle_click'),
         PropGlobals.PropUi.find('**/dropdown_middle_hover')),
        # bottom
        (PropGlobals.PropUi.find('**/dropdown_bottom_normal'),
         PropGlobals.PropUi.find('**/dropdown_bottom_click'),
         PropGlobals.PropUi.find('**/dropdown_bottom_hover'))
        )

    def __init__(self, parent = None, **kwargs):
        """
        """
        optiondefs = (
            ('relief', None, None),
            ('items', [], None),
            ('text', ' ', None),
            ('text_pos', (0.0, -0.0095), None),
            ('text_fg', (0.0, 0.0, 0.0, 1.0), None),
            ('text_scale', 0.035, None),
            ('text_align', TextNode.ACenter, None),
            ('image', self.textures[0], None),
            ('image_scale', (.4, 1, .11), None),
            ('pressEffect', False, None),
            ('command', self.openDropdown, None),
            ('labelText', '', None),
            ('onOpen', None, None),
            ('onClose', None, None),
            ('onChange', None, None),
            ('onChangePassIndex', False, None),
            ('selected', 0, None)
            )

        self.defineoptions(kwargs, optiondefs)
        DirectButton.__init__(self, parent)
        self.initialiseoptions(Dropdown)

        self.dropdownButtons = []

        self.label = OnscreenText(parent = self, align = TextNode.ACenter,
                                  text = self['labelText'],
                                  pos = (0, 0.074), scale = 0.05, wordwrap = 20, mayChange = False)
        self['text'] = self['items'][self['selected']]

    def openDropdown(self):
        """
        Expand the dropdown menu and display all options
        """
        messenger.send('wakeup')
        base.transitions.fadeScreen(0.5)
        if self['onOpen']:
            self['onOpen']()
        self.dropdownFrame = DirectFrame()
        self.dropdownFrame.reparentTo(aspect2dp)
        self.dropdownFrame.setPos(self, 0, 0, 0)
        # this makes sure the dropdown is properly scaled with different shtickerbook scales
        self.dropdownFrame.setScale(self, 1.0)
        self.dropdownFrame.setBin('gui-popup', 100)

        # The first button will always be the close button
        backButton = DirectButton(parent = self.dropdownFrame, pos = (0, 0, 0), relief = None, text = 'Close',
                                  text_pos = (0, -0.01), text_scale = 0.04, image_scale = (.4, 1, .11),
                                  image = self.textures[1], command = self.closeDropdown, pressEffect = False)

        # Add the options
        for index, option in enumerate(self['items']):
            # The bottom option will have it's own texture
            if index == len(self['items']) - 1:
                image = self.textures[3]
            else:
                image = self.textures[2]

            btn = DirectButton(parent = self.dropdownFrame, pos = (0, 0, -0.1 - (.1 * index)), relief = None,
                               text = option, text_pos = (0, -0.0095), text_scale = 0.035, image_scale = (.4, 1, .11),
                               image = image, command = self.chooseOption, extraArgs = [option, index],
                               pressEffect = False)

    def closeDropdown(self):
        self.dropdownFrame.destroy()
        del self.dropdownFrame
        base.transitions.noFade()
        self.dropdownButtons = []
        if self['onClose']:
            self['onClose']()

    def chooseOption(self, option, index):
        messenger.send('wakeup')
        if self['onChange']:
            if self['onChangePassIndex']:
                self['onChange'](index)
            else:
                self['onChange'](option)
        self['text'] = option
        self['selected'] = index
        self.closeDropdown()


GRID_INCLUDED = 0
GRID_CUSTOM = 1


class TexturePicker(DirectButton):
    def __init__(self, parent: NodePath, textures: Union[List[str], Tuple[str, ...]], selectedTexture: Optional[str] = None, **kwargs):

        optiondefs = (
            ('relief', DirectGuiGlobals.FLAT, None),
            ('text', ' ', None),
            ('text_pos', (0.0, -0.0095), None),
            ('text_fg', (0.0, 0.0, 0.0, 1.0), None),
            ('text_scale', 0.035, None),
            ('text_align', TextNode.ACenter, None),
            ('frameSize', (-0.11, 0.11, -0.11, 0.11), None),
            ('frameColor', (0.0, 0.0, 0.0, 1.0), None),
            ('pressEffect', False, None),
            ('command', self.openPicker, None),
            ('labelText', '', None),
            ('onOpen', None, None),
            ('onClose', None, None),
            ('onChange', None, None),
            ('selected', selectedTexture if selectedTexture else textures[0], None),
            ('pickerOffset', Vec3(0, 0, 0), None),
            ('pickerParent', self, None),
            ('closeOnPick', True, None)
            )

        self.defineoptions(kwargs, optiondefs)
        DirectButton.__init__(self, parent)
        self.initialiseoptions(TexturePicker)

        self['image'] = DataPackManager.getTexture(self['selected'])
        self['image_scale'] = 0.1

        self.textures = textures
        self.gridButtons: List[AnimatedButton] = []

        self.pickerGrid: Optional[ToontownScrolledGridFrame] = None
        self.presetButton: Optional[AnimatedButton] = None
        self.customButton: Optional[AnimatedButton] = None
        self.closeButton: Optional[AnimatedButton] = None

        self.addTextureDialog: Optional[TTDialog.TTGlobalDialog] = None

        self.addTextureDialogInput: Optional[DirectEntry] = None

    def destroy(self):
        if self.addTextureDialog:
            self.closeAddTexture()
        self.closePicker()

    def openPicker(self):
        base.messenger.send('wakeup')
        scrollbar = base.loader.loadModel('phase_3.5/models/gui/ttoff_m_gui_sbk_generic', allowInstance = True)
        self.pickerGrid = ToontownScrolledGridFrame(
            parent = self['pickerParent'],
            pos = self['pickerOffset'],
            relief = None,
            image = MovieMakerGUI.gui.find('**/browser'),
            image_scale = OTPGUIUtils.getImageScale(1516, 593, 0.7),
            image_color = VBase4(1.0, 1.0, 1.0, 1.0),
            height = .34,
            width = .88,
            itemPadding = .16,
            itemMargin = (-.585, -.17),
            itemsPerRow = 10,
            manageScrollBars = False,
            verticalScroll_thumb_geom = (
                scrollbar.find('**/scrollbar_normal'),
                scrollbar.find('**/scrollbar_press'),
                scrollbar.find('**/scrollbar_hover')),
            verticalScroll_thumb_geom_scale = OTPGUIUtils.getImageScale(151, 399, 0.15),
            verticalScroll_thumb_relief = None,
            verticalScroll_resizeThumb = False,
            verticalScroll_manageButtons = False,
        )

        self.pickerGrid.setBin('gui-popup', -200)

        self.presetButton = AnimatedButton(
            parent = self.pickerGrid,
            pos = (-0.838, 0, .28),
            scale = 0.07,
            image = PropGlobals.PropUi.find('**/page_color'),
            image3_color = (0.8, 0.8, 0.8, 0.5),
            text = ("", TTLocalizer.TexturePickerTabDefault, TTLocalizer.TexturePickerTabDefault, ""),
            text_pos = (-2, 0.1),
            text_scale = 0.6,
            text_style = 3,
            text_fg = (1.0, 1.0, 1.0, 1.0),
            command = self.setGrid,
            extraArgs = [0]
        )
        self.customButton = AnimatedButton(
            parent = self.pickerGrid,
            pos = (-0.838, 0, .2),
            scale = 0.07,
            image = PropGlobals.PropUi.find('**/page_edit'),
            image3_color = (0.8, 0.8, 0.8, 0.5),
            text = ("", TTLocalizer.TexturePickerTabCustom, TTLocalizer.TexturePickerTabCustom, ""),
            text_pos = (-2, 0.1),
            text_scale = 0.6,
            text_style = 3,
            text_fg = (1.0, 1.0, 1.0, 1.0),
            command = self.setGrid,
            extraArgs = [1]
        )

        self.closeButton = AnimatedButton(
            parent = self.pickerGrid,
            pos = (-0.838, 0, -.28),
            scale = 0.07,
            image = PropGlobals.PropUi.find('**/close_button_normal'),
            image3_color = (0.8, 0.8, 0.8, 0.5),
            text = ("", TTLocalizer.lClose, TTLocalizer.lClose, ""),
            text_pos = (-2, -0.1),
            text_scale = 0.6,
            text_style = 3,
            text_fg = (1.0, 1.0, 1.0, 1.0),
            command = self.closePicker
        )

        self.setGrid(GRID_INCLUDED)

    def setGrid(self, gridIndex: int):
        self.pickerGrid.clearItems()
        self.gridButtons: List[AnimatedButton] = []
        if gridIndex == GRID_INCLUDED:
            self.presetButton['state'] = DirectGuiGlobals.DISABLED
            self.customButton['state'] = DirectGuiGlobals.NORMAL
            self.populateGrid(self.textures)
        elif gridIndex == GRID_CUSTOM:
            self.presetButton['state'] = DirectGuiGlobals.NORMAL
            self.customButton['state'] = DirectGuiGlobals.DISABLED
            self.populateGrid(ClientSettings.SavedPropTextures.get())
            addButton = AnimatedButton(
                parent = base.hidden,
                image = 'phase_3/maps/ttrm_t_gui_gen_customContentIcon.png',
                scale = 0.07,
                relief = None,
                text = ("", TTLocalizer.TexturePickerAddCustom),
                text_scale = .6,
                text_style = 3,
                text_pos = (0, 0.175),
                command = self.showAddTextureDialog
            )
            self.gridButtons.append(addButton)
            self.pickerGrid.addItems(addButton)

    def populateGrid(self, textures: List[str]):
        for texture in textures:
            _btn = AnimatedButton(
                parent = base.hidden,
                image = DataPackManager.getTexture(texture),
                scale = 0.07,
                relief = DirectGuiGlobals.FLAT,
                frameSize = (-1.04, 1.04, -1.04, 1.04),
                frameColor = (0.0, 0.0, 0.0, 1.0),
                command = self.__pick,
                extraArgs = [texture]
            )
            self.gridButtons.append(_btn)
        self.pickerGrid.addItems(*self.gridButtons)

    def closePicker(self):
        if self.pickerGrid:
            self.pickerGrid.clearItems()
            self.pickerGrid.destroy()
            self.pickerGrid = None

    def __pick(self, texture: str):
        base.messenger.send('wakeup')
        if self['onChange']:
            self['onChange'](texture)
            self['selected'] = texture
            self['image'] = DataPackManager.getTexture(self['selected'])
            self['image_scale'] = 0.1
        else:
            raise Exception("On Change was not specified")
        if self['closeOnPick']:
            self.closePicker()

    def showAddTextureDialog(self):
        self.pickerGrid.clearBin()
        self.addTextureDialog = TTDialog.TTGlobalDialog(TTLocalizer.TexturePickerAddInstructions,
                                                        "newTextureDial",
                                                        TTDialog.TwoChoice,
                                                        text_wordwrap = 30)
        self.addTextureDialog.reparentTo(base.aspect2dp)
        self.addTextureDialogInput = DirectEntry(parent = self.addTextureDialog, width = 40, scale = 0.04, pos = (-.8, 0, -0.22))

        base.transitions.fadeScreen(0.8)
        base.localAvatar.chatMgr.setBackgroundFocus(False, True)
        base.controlManager.disableAlphaNumericHotkeys = True
        self.acceptOnce('newTextureDial', self.__finishAddTexture)

    def __finishAddTexture(self):
        status: str = self.addTextureDialog.doneStatus

        if status == 'ok':
            texList: List[str] = ClientSettings.SavedPropTextures.get()
            if self.addTextureDialogInput.get(True) not in texList:
                texList.append(self.addTextureDialogInput.get(True))
                ClientSettings.SavedPropTextures.set(texList)
                self.setGrid(GRID_CUSTOM)
            else:
                base.localAvatar.setSystemMessage(0, TTLocalizer.TexturePickerErrorAlreadyExists)
        self.closeAddTexture()
        self.pickerGrid.setBin('gui-popup', -200)

    def closeAddTexture(self):
        self.addTextureDialog.cleanup()
        del self.addTextureDialog
        self.addTextureDialog = None
        self.addTextureDialogInput.destroy()
        del self.addTextureDialogInput
        self.addTextureDialogInput = None
        base.localAvatar.chatMgr.setBackgroundFocus(base.controlManager.getChatDisabled(), True)
        base.controlManager.disableAlphaNumericHotkeys = False


class NumberInput(DirectFrame):
    def __init__(self, parent = None, size: bool = 0, **kwargs):
        self.value = 0.0
        optiondefs = (
            ('relief', None, None),
            ('image_scale', OTPGUIUtils.getImageScale(248, 136, 0.125), None),
            ('text_scale', 0.05, None),
            ('text_pos', (-0.032, -0.015), None),
            ('text_align', TextNode.ACenter, None),
            ('image', MovieMakerGUI.gui.find('**/input_lg') if size
                else MovieMakerGUI.gui.find('**/input_sm'), None),
            ('width', 3, None),
            ('onChange', None, None),
            ('onChangeExtraArgs', None, None),
            ('incrementScale', 1.0, None),
            ('incrementType', 'ADD', None),
            ('minMax', (-65536, 65536), None),
            ('numberType', float, None),
            ('startValue', 0.0, self.__setStartValue)
        )

        self.defineoptions(kwargs, optiondefs)
        DirectFrame.__init__(self, parent)
        self.initialiseoptions(NumberInput)

        # self.bind(DirectGuiGlobals.TYPE, self.__onType)

        self.downButton = AnimatedButton(
            parent = self,
            relief = None,
            pos = (.0825, 0, -0.02),
            hpr = (0, 0, 180),
            scale = 0.03,
            image = (
                MovieMakerGUI.gui.find('**/input_arrow'),
                MovieMakerGUI.gui.find('**/input_arrow_h'),
            )
        )
        self.upButton = AnimatedButton(
            parent = self,
            relief = None,
            pos = (.0825, 0, 0.02),
            scale = 0.03,
            image = (
                MovieMakerGUI.gui.find('**/input_arrow'),
                MovieMakerGUI.gui.find('**/input_arrow_h'),
            )
        )

        self.downButton.bind(DirectGuiGlobals.B1PRESS, self.__lButtonPress)
        self.downButton.bind(DirectGuiGlobals.B1RELEASE, self.__lButtonRelease)

        self.upButton.bind(DirectGuiGlobals.B1PRESS, self.__rButtonPress)
        self.upButton.bind(DirectGuiGlobals.B1RELEASE, self.__rButtonRelease)

    def decrement(self):
        base.messenger.send('wakeup')
        if self['incrementType'] == 'ADD':
            self.__setValue(self.value - self['incrementScale'])
        elif self['incrementType'] == 'MUL':
            self.__setValue(self.value / self['incrementScale'])
        else:
            print(f"Incorrect increment type {self['incrementType']}")

    def increment(self):
        base.messenger.send('wakeup')
        if self['incrementType'] == 'ADD':
            self.__setValue(self.value + self['incrementScale'])
        elif self['incrementType'] == 'MUL':
            self.__setValue(self.value * self['incrementScale'])
        else:
            print(f"Incorrect increment type {self['incrementType']}")

    def __lButtonPress(self, e = None):
        self.decrement()
        task = self.addTask(self.__runCounter, 'counterTask')
        task.delayTime = 0.4
        task.prevTime = 0.0
        task.delta = 0

    def __lButtonRelease(self, e = None):
        base.messenger.send('wakeup')
        self.removeTask('counterTask')

    def __rButtonPress(self, e = None):
        self.increment()
        task = self.addTask(self.__runCounter, 'counterTask')
        task.delayTime = 0.4
        task.prevTime = 0.0
        task.delta = 1

    def __rButtonRelease(self, e = None):
        base.messenger.send('wakeup')
        self.removeTask('counterTask')

    def __runCounter(self, task: Task) -> int:
        """
        Performs the task of the arrow buttons
        The longer its held down, the faster it moves
        """
        if task.time - task.prevTime < task.delayTime:
            return Task.cont
        else:
            task.delayTime = max(0.02, task.delayTime * 0.75)
            task.prevTime = task.time
            if task.delta:
                self.increment()
            else:
                self.decrement()
            return Task.cont

    def __setStartValue(self):
        self.__setValue(self['startValue'])

    def __setValue(self, value: float):
        self.value = bound(self['numberType'](value), *self['minMax'])
        self.__valueChanged()
        self['text'] = str(self.value)

    def __valueChanged(self):
        if self['onChange']:
            if self['onChangeExtraArgs']:
                self['onChange'](self.value, *self['onChangeExtraArgs'])
            else:
                self['onChange'](self.value)

    def destroy(self):
        self.removeAllTasks()
        DirectFrame.destroy(self)


class ToggleSwitch(DirectButton):

    def __init__(self, parent: NodePath,  **kwargs):

        optiondefs = (
            ('relief', None, None),
            ('pressEffect', False, None),
            ('image', (MovieMakerGUI.gui.find('**/toggle_bg'), MovieMakerGUI.gui.find('**/toggle_bg_h')), None),
            ('image_scale', OTPGUIUtils.getImageScale(178, 87), None),
            ('command', self.__toggle, None),
            ('onChange', None, None),
            ('onChangeExtraArgs', [], None),
            ('toggled', False, None),
            )

        self.defineoptions(kwargs, optiondefs)
        DirectButton.__init__(self, parent)
        self.initialiseoptions(ToggleSwitch)

        self.__circleOverlay = self.attachNewNode('_circleOverlay')
        self.__circleOverlay.setScale(0.65)
        MovieMakerGUI.gui.find('**/toggle_cir').copyTo(self.__circleOverlay)
        self.__transition(self['toggled'])

    def __toggle(self):
        self['toggled'] = not self['toggled']
        if self['onChange']:
            self['onChange'](*self['onChangeExtraArgs'])

        self.__transition(self['toggled'])

    def __transition(self, state: bool):
        col: VBase4
        x: float
        if state:
            col = VBase4(0.303, 1.0, 0.303, 1.0)
            x = 0.55
        else:
            col = VBase4(1.0, 0.35, 0.35, 1.0)
            x = -0.55

        Parallel(
            self.__circleOverlay.posInterval(0.1, Vec3(x, 0, 0), blendType='easeOut'),
            self.__circleOverlay.colorScaleInterval(0.1, col, blendType='easeOut'),
            name = f"switch{self.guiId}"
        ).start()
