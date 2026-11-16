""" Settings Screen GUI Elements - drewcification 010321 """
from typing import Type, Union

from direct.gui.DirectGui import *
from direct.interval.IntervalGlobal import *

from panda3d.core import *

from toontown.datapack.DataPackManager import DataPackManager
from toontown.hood.EstateHood import EstateHood
from toontown.toonbase import TTLocalizer, ToontownGlobals, ClientSettings
from toontown.toonbase.ClientSettings import ShtickerBookBackground
from toontown.toonbase.SettingsBase import SettingBase, EnumSetting, BoolSetting, FloatSetting, SettingsWarning, ListSetting, IntegerSetting
from toontown.toontowngui import TTDialog
from toontown.toontowngui.ColorPickerGUI import ColorPickerGUI
from toontown.toontowngui.HelpButton import HelpButton
from toontown.toontowngui.ToontownGUIUtils import Animations
from toontown.toontowngui.ColorUtils import *


class SettingsButton(DirectButton):
    """
    Generic Settings button with a label
    """

    def __init__(self, settingsScreen, settingString, parent = hidden, **kwargs):
        """
        :param settingsScreen: The parent Settings Screen
        :param settingString: The setting key as seen in settings.json
        :param parent: Parent Frame
        :param row: The row in which the option is placed
        :param kwargs: extra key word args if needed
        """
        gui = loader.loadModel('phase_3/models/gui/ttoff_m_gui_opts_buttons', allowInstance = True)
        textures = (gui.find('**/button_green_up'), gui.find('**/button_green_down'),
                    gui.find('**/button_green_rollover'), gui.find('**/button_inactive'))
        self.settingsScreen = settingsScreen
        optiondefs = (
            ('relief', None, None),
            ('text', '', None),
            ('text_pos', (0.0, -0.012), None),
            ('text_fg', (0.0, 0.0, 0.0, 1.0), None),
            ('text_scale', 0.04, None),
            ('text_align', TextNode.ACenter, None),
            ('image', textures, None),
            ('image_scale', (.4, 1, .11), None),
            ('pressEffect', False, None)
        )

        self.defineoptions(kwargs, optiondefs)
        DirectButton.__init__(self, parent)
        self.initialiseoptions(SettingsButton)

        self.label = OnscreenText(parent = self, align = TextNode.ALeft,
                                  text = TTLocalizer.SettingTitles.get(settingString, settingString),
                                  pos = (-1.1, -0.02), scale = 0.06, wordwrap = 20, mayChange = False)

        #if self.setting.getSettingDescription():
        #    self.helpButton = HelpButton(parent = self, contents = self.setting.getSettingDescription(), pos = (-1.15, 0, 0), inScroll = True)

    def nothing(self):
        pass


class ColorPickerOption(DirectButton):
    """
    Generic Settings button with a label
    """
    buttonShader = Shader.load(Shader.SLGLSL, vertex = 'phase_3/shaders/ttoff_sha_ui_generic.vert',
                               fragment = 'phase_3/shaders/ttoff_sha_ui_settings_color_pick_button.frag')

    def __init__(self, settingsScreen, setting: ListSetting, parent = hidden, includedSwatches = [],
                 **kwargs):
        """
        :param settingsScreen: The parent Settings Screen
        :param settingString: The setting key as seen in settings.json
        :param parent: Parent Frame
        :param row: The row in which the option is placed
        :param includedSwatches: List of rgb(a) values to always be included in the swatch list
        :param kwargs: extra key word args if needed
        """
        gui = loader.loadModel('phase_3/models/gui/ttoff_m_gui_opts_colorpicker', allowInstance = True)
        self.settingsScreen = settingsScreen
        self.setting = setting
        self.includedSwatches = includedSwatches
        optiondefs = (
            ('relief', None, None),
            ('image', gui.find('**/preset_splatter_circle'), None),
            ('image_scale', (.15, .15, .15), None),
            ('command', self.openPicker, None),
            # TODO: Separate this entire class into a non-settings compatible version. this is kinda hacky but it works
            ('isForSettings', True, None),
            ('hideAlpha', False, None),
            ('onCloseRGBA', None, None),
            ('startRGBA', None, None),
            ('pickerParent', base.aspect2dp, None),
            ('pickerOffset', Vec3(0, 0, 0), None),
            ('fadeScreen', True, None)
        )

        self.defineoptions(kwargs, optiondefs)
        DirectButton.__init__(self, parent)
        self.initialiseoptions(ColorPickerOption)
        self.setShader(self.buttonShader)

        if self['startRGBA']:
            self['image_color'] = self['startRGBA']
        else:
            self['image_color'] = hsvToRgb(*hsvIntToFloat(*self.setting.get()))

        self.label = OnscreenText(parent = self, align = TextNode.ALeft,
                                  text = self.setting.getSettingDisplayName() if isinstance(self.setting, SettingBase) else '',
                                  pos = (-1.1, -0.02), scale = 0.06, wordwrap = 20, mayChange = False)
        self.label.setShaderOff()
        if not isinstance(self.setting, SettingBase):
            return
        if self.setting.getSettingDescription():
            self.helpButton = HelpButton(parent = self, contents = self.setting.getSettingDescription(), pos = (-1.15, 0, 0), inScroll = True)

    def openPicker(self):
        messenger.send('wakeup')
        if self['fadeScreen']:
            base.transitions.fadeScreen(0.5)

        # Move the settings screen and close button behind the fade screen to prevent interaction
        if self.settingsScreen:
            if not self.settingsScreen.inBook:
                self.settingsScreen.reparentTo(aspect2d)
                # a2d is behind the fadeScreen
                self.settingsScreen.bookCloseButton.reparentTo(base.a2dBottomRight)
        if self['isForSettings']:
            self.picker = ColorPickerGUI(self.setting, includedSwatches = self.includedSwatches,
                                         startHsva = (self.setting.get()),
                                         parent = aspect2dp, scale = 0.2)
        else:
            self.picker = ColorPickerGUI('', parent = self['pickerParent'], pos = self['pickerOffset'], scale = 0.1)
            self.picker.setFromRgbaFloat(*self['startRGBA'])
            if self['hideAlpha']:
                self.picker.alphaBar.hide()

        if ClientSettings.GUIAnimations.get():
            startPos = self.getPos(aspect2d)

            Parallel(
                self.picker.posInterval(0.2, Point3(0), startPos, blendType = 'easeOut'),
                self.picker.scaleInterval(0.2, Point3(0.2 if self['isForSettings'] else 0.1), Point3(0.01), blendType = 'easeOut'),
                self.picker.colorScaleInterval(0.2, VBase4(1.0), VBase4(1.0, 1.0, 1.0, 0.0))
            ).start()

        self.accept(f'color-picked-{self.setting}', self.updateColor)
        self.accept(self.picker.doneEvent, self.closePicker)

    def closePicker(self):
        messenger.send('wakeup')
        if self['fadeScreen']:
            base.transitions.noFade()

        if self['isForSettings']:
            if not self.settingsScreen.inBook:
                self.settingsScreen.reparentTo(aspect2d, 8000)
                # a2dp is in front of the fadeScreen
                self.settingsScreen.bookCloseButton.reparentTo(base.a2dpBottomRight)
                base.transitions.fadeScreen(0.5)
            self.setting.set(hsvFloatToInt(*self.picker.hsva))
            self['image_color'] = hsvToRgb(*hsvIntToFloat(*self.setting.get()))
            return
        if self['onCloseRGBA']:
            col = hsvToRgb(*self.picker.hsva)
            if self['startRGBA']:
                self['startRGBA'] = col
            self['onCloseRGBA'](col)
            self['image_color'] = col

    def updateColor(self):
        messenger.send('wakeup')
        # We still have this here because we want to preview the color while in the picker
        if self.setting == ShtickerBookBackground:
            base.cr.makeACogEgg = self.picker.rgba == (0, 0, 0, 0)
            if hasattr(base, 'localAvatar'):
                color = self.picker.hsva
                if color[3] == 1:
                    base.render.hide()
                else:
                    base.render.show()
                base.localAvatar.book.background.setColor(Vec4(*hsvToRgb(*color)))


class DropdownOption(DirectButton):
    """
    Dropdown Button w/ menu
    Panda's DirectOptionMenu is garbage. so let's just do this
    """
    gui = loader.loadModel('phase_3/models/gui/ttoff_m_gui_opts_dropdown', allowInstance = True)

    textures = (
        # main
        (gui.find('**/dropdown_button_normal'), gui.find('**/dropdown_button_click'),
         gui.find('**/dropdown_button_hover')),
        # top
        (gui.find('**/dropdown_top_normal'), gui.find('**/dropdown_top_click'), gui.find('**/dropdown_top_hover')),
        # middle
        (gui.find('**/dropdown_middle_normal'), gui.find('**/dropdown_middle_click'),
         gui.find('**/dropdown_middle_hover')),
        # bottom
        (gui.find('**/dropdown_bottom_normal'), gui.find('**/dropdown_bottom_click'),
         gui.find('**/dropdown_bottom_hover'))
    )

    def __init__(self, settingsScreen, setting: EnumSetting, parent = hidden, isGameSetting = True, **kwargs):
        """
        :param settingsScreen: The parent Settings Screen
        :param settingString: The setting key as seen in settings.json
        :param parent: Parent Frame
        :param row: The row in which the option is placed
        :param kwargs: extra key word args if needed
        """
        self.settingsScreen = settingsScreen
        self.setting: EnumSetting = setting

        if isGameSetting:
            text = DataPackManager.getLocalizedText(f'#SettingEnum_{self.setting.enum.__name__}__{self.setting.get().name}')
            self.selectedMode = self.setting.get()
        else:
            text = ''
            self.selectedMode = 0

        optiondefs = (
            ('relief', None, None),
            ('text', text, None),
            ('text_pos', (0.0, -0.012), None),
            ('text_fg', (0.0, 0.0, 0.0, 1.0), None),
            ('text_scale', 0.04, None),
            ('text_align', TextNode.ACenter, None),
            ('image', self.textures[0], None),
            ('image_scale', (.4, 1, .11), None),

            ('pressEffect', False, None),
            ('command', self.openDropdown, None)
        )

        self.defineoptions(kwargs, optiondefs)
        DirectButton.__init__(self, parent)
        self.initialiseoptions(DropdownOption)
        self.dropdownButtons = []

        self.label = OnscreenText(parent = self, align = TextNode.ALeft,
                                  text = self.setting.getSettingDisplayName(),
                                  pos = (-1.1, -0.02), scale = 0.06, wordwrap = 20, mayChange = False)

        if self.setting.getSettingDescription():
            self.helpButton = HelpButton(parent = self, contents = self.setting.getSettingDescription(),
                                         pos = (-1.15, 0, 0), inScroll = True)

    def openDropdown(self):
        """
        Expand the dropdown menu and display all options
        """
        messenger.send('wakeup')
        base.transitions.fadeScreen(0.5)
        self.dropdownFrame = DirectFrame()
        self.dropdownFrame.reparentTo(aspect2dp)
        self.dropdownFrame.setPos(self, 0, 0, 0)
        # this makes sure the dropdown is properly scaled with different shtickerbook scales
        self.dropdownFrame.setScale(self, 1.0)
        self.dropdownFrame.setBin('gui-popup', 100)

        if self.settingsScreen:
            # Move the settings screen and close button behind the fade screen to prevent interaction
            if not self.settingsScreen.inBook:
                self.settingsScreen.reparentTo(aspect2d)
                # a2d is behind the fadeScreen
                self.settingsScreen.bookCloseButton.reparentTo(base.a2dBottomRight)

        # The first button will always be the close button
        backButton = DirectButton(parent = self.dropdownFrame, pos = (0, 0, 0), relief = None, text = 'Close',
                                  text_pos = (0, -0.01), text_scale = 0.04, image_scale = (.4, 1, .11),
                                  image = self.textures[1], command = self.closeDropdown, pressEffect = False)

        # Add the options
        for index, option in enumerate(self.setting.enum):
            # The bottom option will have it's own texture
            if index == len(self.setting.enum) - 1:
                image = self.textures[3]
            else:
                image = self.textures[2]
            optionName = f'#SettingEnum_{self.setting.enum.__name__}__{option.name}'
            btn = DirectButton(parent = self.dropdownFrame, pos = (0, 0, -0.1 - (.1 * index)), relief = None,
                               text = DataPackManager.getLocalizedText(optionName), text_pos = (0, -0.01), text_scale = 0.05, image_scale = (.4, 1, .11),
                               image = image, command = self.chooseOption, extraArgs = [option], pressEffect = False)
            # The currently selected option will have green text
            # although i think just a diff button background could work aswell
            if index == self.setting.get():
                btn['text_fg'] = (0, 1, .6, 1)
                btn['text_shadow'] = (0, 0, 0, 0.75)
            self.dropdownButtons.append(btn)

        # If the bottom button is off the screen, move it up until its not
        if self.dropdownButtons[-1].getZ(render2d) < -0.95:
            self.dropdownFrame.setPos(self.dropdownFrame, 0, 0, -0.95 - self.dropdownButtons[-1].getZ(render2d))

        clipperTop = PlaneNode('clipper')
        clipperTop.setPlane(Plane(Vec3(0, 0, -1), Point3(0, 0, self.dropdownFrame.getZ() + (0.055 * self.dropdownFrame.getScale()[0]))))
        self.dropdownFrame.setClipPlane(base.aspect2dp.attachNewNode(clipperTop))

        Animations.slideDown(self.dropdownFrame, self.dropdownFrame.getZ(), startZ = self.dropdownFrame.getZ() + .2, intensity = 0).start()

    def closeDropdown(self):
        self.dropdownFrame.destroy()
        del self.dropdownFrame

        self.dropdownButtons = []
        if self.settingsScreen:
            base.transitions.noFade()
            if not self.settingsScreen.inBook:
                self.settingsScreen.reparentTo(aspect2d, 8000)
                # a2dp is in front of the fadeScreen
                self.settingsScreen.bookCloseButton.reparentTo(base.a2dpBottomRight)
                base.transitions.fadeScreen(0.5)

    def chooseOption(self, optionIndex):
        messenger.send('wakeup')
        self.setting.set(optionIndex)
        self.closeDropdown()

        self['text'] = DataPackManager.getLocalizedText(f'#SettingEnum_{self.setting.enum.__name__}__{self.setting.get().name}')
        if self.setting in ToontownGlobals.SettingsWarnings:
            warn = ToontownGlobals.SettingsWarnings[self.setting]
            if warn == SettingsWarning.SWRestart:
                notice = TTLocalizer.OptionsPageRestartNotice

            elif warn == SettingsWarning.SWReload:
                notice = TTLocalizer.OptionsPageReloadNotice

            elif warn == SettingsWarning.SWStreet:
                notice = TTLocalizer.OptionsPageReloadNotice

            elif warn == SettingsWarning.SWEstate:
                if not base.cr.playGame.hood or not isinstance(base.cr.playGame.hood, EstateHood):
                    return
                notice = TTLocalizer.OptionsPageReloadNotice

            elif warn == SettingsWarning.SWStreet:
                notice = TTLocalizer.OptionsPageReloadNotice

            else:
                notice = '???'

            self._dialog = TTDialog.TTDialog(style = TTDialog.Acknowledge, text = notice,
                                             command = self.__confirmNotice)
            self._dialog.show()
            if not self.settingsScreen.inBook:
                self.settingsScreen.reparentTo(aspect2d)
                # a2d is behind the fadeScreen
                self.settingsScreen.bookCloseButton.reparentTo(base.a2dBottomRight)

    def __confirmNotice(self, state):
        messenger.send('wakeup')
        if hasattr(self, '_dialog') and self._dialog:
            self._dialog.destroy()
            self._dialog = None
            if not self.settingsScreen.inBook:
                self.settingsScreen.reparentTo(aspect2d, 8000)
                # a2dp is in front of the fadeScreen
                self.settingsScreen.bookCloseButton.reparentTo(base.a2dpBottomRight)
                base.transitions.fadeScreen(0.5)


class DisplayModeDropdown(DropdownOption):
    def __init__(self, updateCommand, parent = hidden):
        DropdownOption.__init__(self, None, ClientSettings.DisplayMode, parent)
        self.updateCommand = updateCommand
        self.selectedMode = ClientSettings.DisplayMode.get()
        self.initialiseoptions(DisplayModeDropdown)
        self.label.removeNode()
        del self.label

    def openDropdown(self):
        DropdownOption.openDropdown(self)
        self.dropdownFrame.wrtReparentTo(self)

    def chooseOption(self, optionIndex: int):
        messenger.send('wakeup')
        self['text'] = TTLocalizer.SettingsOptions[self.setting][optionIndex]
        self.selectedMode = optionIndex
        self.closeDropdown()
        self.updateCommand(optionIndex)


class TeleportGreetingDropdown(DropdownOption):
    def __init__(self, settingScreen, updateCommand, parent = hidden):
        DropdownOption.__init__(self, settingScreen, ClientSettings.TeleportGreeting, parent, isGameSetting = False)
        self.updateCommand = updateCommand
        self.selectedMode = base.localAvatar.getTeleportGreeting()
        self['text'] = DataPackManager.getLocalizedText(f'#SettingEnum_{self.setting.enum.__name__}__{self.setting.get().name}')
        self.initialiseoptions(TeleportGreetingDropdown)

    def chooseOption(self, optionIndex: int):
        messenger.send('wakeup')
        self['text'] = DataPackManager.getLocalizedText(f'#SettingEnum_{self.setting.enum.__name__}__{self.setting.get().name}')
        self.selectedMode = optionIndex
        self.closeDropdown()
        self.updateCommand(optionIndex)


class ToggleOption(DirectButton):
    """
    Toggle Check Mark Settings Button with a label
    """
    gui = loader.loadModel('phase_3/models/gui/ttoff_m_gui_opts_buttons', allowInstance = True)
    onTextures = (gui.find('**/on_up'), gui.find('**/on_down'),
                  gui.find('**/on_rollover'), gui.find('**/on_inactive'))
    offTextures = (gui.find('**/off_up'), gui.find('**/off_down'),
                   gui.find('**/off_rollover'), gui.find('**/off_inactive'))

    def __init__(self, settingsScreen, setting: BoolSetting, parent = hidden, category = 'game', **kwargs):
        """
        :param settingsScreen: The parent Settings Screen
        :param settingString: The setting key as seen in settings.json
        :param parent: Parent Frame
        :param row: The row in which the option is placed
        :param category: The settings category (game or retro)
        :param kwargs: extra key word args if needed
        """
        self.settingsScreen = settingsScreen
        optiondefs = (
            ('relief', None, None),
            ('image_scale', 0.1, None),
            ('image', self.onTextures, None),
            ('pressEffect', False, None),
            ('command', self.toggle, None)
        )

        self.defineoptions(kwargs, optiondefs)
        DirectButton.__init__(self, parent = parent)
        self.initialiseoptions(ToggleOption)
        self.setting = setting
        self.category = category

        self.toggled = setting.get()

        self.label = OnscreenText(parent = self, align = TextNode.ALeft,
                                  text = self.setting.getSettingDisplayName(),
                                  pos = (-1.1, -0.02), scale = 0.06, wordwrap = 20, mayChange = False)

        if self.setting.getSettingDescription():
            self.helpButton = HelpButton(parent = self, contents = self.setting.getSettingDescription(),
                                         pos = (-1.15, 0, 0), inScroll = True)
        self.updateButton()

    def toggle(self):
        messenger.send('wakeup')
        self.toggled = not self.toggled
        self.setting.set(self.toggled)
        self.updateButton()
        if self.setting.changeWarning:
            warn = self.setting.changeWarning
            if warn == SettingsWarning.SWRestart:
                notice = TTLocalizer.OptionsPageRestartNotice

            elif warn == SettingsWarning.SWReload:
                notice = TTLocalizer.OptionsPageReloadNotice

            elif warn == SettingsWarning.SWStreet:
                notice = TTLocalizer.OptionsPageReloadNotice

            elif warn == SettingsWarning.SWEstate:
                if not base.cr.playGame.hood or isinstance(base.cr.playGame.hood, EstateHood):
                    return
                notice = TTLocalizer.OptionsPageReloadNotice

            elif warn == SettingsWarning.SWStreet:
                notice = TTLocalizer.OptionsPageReloadNotice

            else:
                notice = '???'

            self._dialog = TTDialog.TTDialog(style = TTDialog.Acknowledge, text = notice,
                                             command = self.__confirmNotice)
            self._dialog.show()
            if not self.settingsScreen.inBook:
                self.settingsScreen.reparentTo(aspect2d)
                # a2d is behind the fadeScreen
                self.settingsScreen.bookCloseButton.reparentTo(base.a2dBottomRight)

    def __confirmNotice(self, state):
        if hasattr(self, '_dialog') and self._dialog:
            self._dialog.destroy()
            self._dialog = None
            if not self.settingsScreen.inBook:
                self.settingsScreen.reparentTo(aspect2d, 8000)
                # a2dp is in front of the fadeScreen
                self.settingsScreen.bookCloseButton.reparentTo(base.a2dpBottomRight)
                base.transitions.fadeScreen(0.5)

    def updateButton(self):
        """
        Updates the texture of the check box
        """
        self['image'] = self.onTextures if self.toggled else self.offTextures


class ToggleSlider(ToggleOption):
    """ """
    gui = loader.loadModel('phase_3/models/gui/ttoff_m_gui_opts_slider', allowInstance = True)
    thumbTextures = (
        gui.find('**/slider_thumb_up'),
        gui.find('**/slider_thumb_press'),
        gui.find('**/slider_thumb_hover'),
        gui.find('**/slider_thumb_press'))
    barTexture = gui.find('**/slider_bg')

    def __init__(self, settingsScreen, boolSetting: Type[BoolSetting], sliderSetting: Type[FloatSetting], parent = hidden,
                 minimum = 0, maximum = 100, multiplier = 1, unit = "", **kwargs):
        """
        :param settingsScreen: The parent Settings Screen
        :param settingString: The setting key used by the toggle button as seen in settings.json
        :param sliderString: The setting key used by the slider as seen in settings.json
        :param parent: Parent Frame
        :param row: The row in which the option is placed
        :param minimum: Minimum value for the slider
        :param maximum: Maximum value for the slider
        :param multiplier: The multiplier for the visual label : e.g. - the volume should be displayed as 0-100,
              but the option is stored as 0.0-1.0, so we would set this option to 100 to show it as 0-100
        :param unit: Unit to show after the value in the label (e.g. %)
        :param kwargs: extra key word args if needed
        """
        self.multiplier = multiplier
        self.boolSetting = boolSetting
        self.sliderSetting = sliderSetting
        self.settingsScreen = settingsScreen
        self.unit = unit

        optiondefs = (
            ('relief', None, None),
            ('image_scale', 0.1, None),
            ('image', self.onTextures, None),
            ('image_pos', (-0.3, 0, 0), None),
            ('pressEffect', False, None),
            ('command', self.toggle, None)
        )

        self.defineoptions(kwargs, optiondefs)
        ToggleOption.__init__(self, settingsScreen, boolSetting, parent = parent, **kwargs)
        self.initialiseoptions(ToggleSlider)

        self.slider = DirectSlider(
            parent = self,
            value = sliderSetting.get(),
            range = (minimum, maximum),
            pageSize = .1,
            pos = (0.05, 0, 0),
            scale = (.3, 1, .3),
            thumb_relief = None,
            thumb_geom = self.thumbTextures,
            thumb_geom_scale = (0.385, 1, 0.22),
            thumb_frameSize = (-.2, .2, -.15, .15),
            thumb_text = '',
            thumb_text_pos = (0.0, -0.02),
            thumb_text_scale = 0.1, thumb_text_style = 3,
            frameColor = (0, 0, 0, 0),
            image_scale = (2.032, 1, 0.254),
            image = self.barTexture,
            command = self.onChange
        )
        self.slider.setTransparency(TransparencyAttrib.MAlpha)

        self.slider['thumb_text'] = ('', f"{(self.slider['value'] * self.multiplier):.0f}{self.unit}",
                                     f"{(self.slider['value'] * self.multiplier):.0f}{self.unit}", '')
        if self.toggled:
            self.slider['state'] = DGG.NORMAL
            self.slider.setAlphaScale(1.0)
        else:
            self.slider['state'] = DGG.DISABLED
            self.slider.setAlphaScale(0.4)

    def toggle(self):
        messenger.send('wakeup')
        ToggleOption.toggle(self)
        if self.toggled:
            self.slider['state'] = DGG.NORMAL
            self.slider.setAlphaScale(1.0)
        else:
            self.slider['state'] = DGG.DISABLED
            self.slider.setAlphaScale(0.4)

    def onChange(self):
        messenger.send('wakeup')
        val = round(self.slider['value'], 4)
        self.sliderSetting.set(val)
        self.slider['thumb_text'] = ('', f"{(val * self.multiplier):.0f}{self.unit}",
                                     f"{(val * self.multiplier):.0f}{self.unit}", '')


class SliderOption(DirectFrame):
    """ """
    gui = loader.loadModel('phase_3/models/gui/ttoff_m_gui_opts_slider', allowInstance = True)
    thumbTextures = (
        gui.find('**/slider_thumb_up'),
        gui.find('**/slider_thumb_press'),
        gui.find('**/slider_thumb_hover'),
        gui.find('**/slider_thumb_press'))
    barTexture = gui.find('**/slider_bg')
    buttonModel = loader.loadModel('phase_3/models/gui/ttoff_m_gui_opts_buttons', allowInstance = True)

    btnTextures = (buttonModel.find('**/button_green_up'), buttonModel.find('**/button_green_down'),
                   buttonModel.find('**/button_green_rollover'), buttonModel.find('**/button_inactive'))
    moreTextures = (buttonModel.find('**/more_button_normal'), buttonModel.find('**/more_button_click'),
                    buttonModel.find('**/more_button_hover'), buttonModel.find('**/more_button_click'))

    closeTextures = (buttonModel.find('**/close_button_normal'), buttonModel.find('**/close_button_click'),
                     buttonModel.find('**/close_button_hover'), buttonModel.find('**/close_button_click'))

    def __init__(self, settingsScreen, setting: Union[FloatSetting, IntegerSetting], parent = hidden,
                 minimum = None , maximum = None, multiplier = 1, unit = "", **kwargs):
        """
        :param settingsScreen: The parent Settings Screen
        :param sliderString: The setting key used by the slider as seen in settings.json
        :param parent: Parent Frame
        :param row: The row in which the option is placed
        :param minimum: Minimum value for the slider
        :param maximum: Maximum value for the slider
        :param multiplier: The multiplier for the visual label : e.g. - the volume should be displayed as 0-100,
              but the option is stored as 0.0-1.0, so we would set this option to 100 to show it as 0-100
        :param unit: Unit to show after the value in the label (e.g. %)
        :param kwargs: extra key word args if needed
        """
        self.multiplier = multiplier
        self.setting = setting
        self.settingsScreen = settingsScreen
        self.unit = unit

        optiondefs = (
            ('relief', None, None),
        )

        if minimum is None:
            minimum = self.setting.minVal

        if maximum is None:
            maximum = self.setting.maxVal

        self.defineoptions(kwargs, optiondefs)
        DirectFrame.__init__(self, parent, **kwargs)
        self.initialiseoptions(SliderOption)
        self.slider = DirectSlider(
            parent = self,
            value = self.setting.get(),
            range = (minimum, maximum),
            pageSize = .1,
            pos = (0.05, 0, 0),
            scale = (.3, 1, .3),
            thumb_relief = None, thumb_geom = self.thumbTextures,
            thumb_geom_scale = (0.385, 1, 0.22),
            thumb_frameSize = (-.2, .2, -.15, .15),
            thumb_text = '',
            thumb_text_pos = (0.0, -0.02),
            thumb_text_scale = 0.1, thumb_text_style = 3,
            frameColor = (0, 0, 0, 0),
            image_scale = (2.032, 1, 0.254),
            image = self.barTexture,
            command = self.onChange
        )
        self.slider['thumb_text'] = ('', f"{(self.slider['value'] * self.multiplier):.0f}{self.unit}",
                                     f"{(self.slider['value'] * self.multiplier):.0f}{self.unit}", '')
        self.label = OnscreenText(parent = self, align = TextNode.ALeft,
                                  text = self.setting.getSettingDisplayName(),
                                  pos = (-1.1, -0.02), scale = 0.06, wordwrap = 20, mayChange = False)

        self.presetsButton = DirectButton(parent = self, relief = None, image = self.moreTextures, pressEffect = False,
                                          pos = (-.3, 0, 0), scale = 0.08, command = self.showPresets)

        if self.setting.getSettingDescription():
            self.helpButton = HelpButton(parent = self, contents = self.setting.getSettingDescription(),
                                         pos = (-1.15, 0, 0), inScroll = True)

    def onChange(self):
        messenger.send('wakeup')
        val = round(self.slider['value'], 4) if isinstance(self.setting, FloatSetting) else int(self.slider['value'])
        self.setting.set(val)
        self.slider['thumb_text'] = ('', f"{(val * self.multiplier):.0f}{self.unit}",
                                     f"{(val * self.multiplier):.0f}{self.unit}", '')

    def showPresets(self):
        messenger.send('wakeup')
        base.transitions.fadeScreen(0.5)
        self.presetFrame = DirectFrame()
        self.presetFrame.reparentTo(aspect2dp)
        self.presetFrame.setPos(self.presetsButton, 0, 0, 0)
        # this makes sure the dropdown is properly scaled with different shtickerbook scales
        self.presetFrame.setScale(self, 1.0)
        self.presetFrame.setBin('gui-popup', 100)

        if self.settingsScreen:
            # Move the settings screen and close button behind the fade screen to prevent interaction
            if not self.settingsScreen.inBook:
                self.settingsScreen.reparentTo(aspect2d)
                # a2d is behind the fadeScreen
                self.settingsScreen.bookCloseButton.reparentTo(base.a2dBottomRight)

        backButton = DirectButton(parent = self.presetFrame, pos = (0, 0, 0), relief = None,
                                  image_scale = (.08, 1, .08), image = self.closeTextures,
                                  command = self.closePresets, pressEffect = False)
        resetButton = DirectButton(parent = self.presetFrame, pos = (0, 0, 0.1), relief = None,
                                   text = 'Reset to Default', text_pos = (0, -0.01), text_scale = 0.04,
                                   image_scale = (.4, 1, .11), image = self.btnTextures,
                                   command = self.resetDefault, pressEffect = False)
        if ClientSettings.GUIAnimations.get():
            Parallel(
                resetButton.scaleInterval(0.2, Vec3(1), Vec3(0.5), blendType = 'easeOut'),
                resetButton.posInterval(0.2, Vec3(0, 0, 0.1), Vec3(0, 0, 0.05), blendType = 'easeOut'),
                resetButton.colorScaleInterval(0.2, Vec4(1), Vec4(1, 1, 1, 0), blendType = 'easeOut')
            ).start()

    def closePresets(self):
        messenger.send('wakeup')
        self.presetFrame.destroy()
        del self.presetFrame

        if self.settingsScreen:
            base.transitions.noFade()
            if not self.settingsScreen.inBook:
                self.settingsScreen.reparentTo(aspect2d, 8000)
                # a2dp is in front of the fadeScreen
                self.settingsScreen.bookCloseButton.reparentTo(base.a2dpBottomRight)
                base.transitions.fadeScreen(0.5)

    def resetDefault(self):
        messenger.send('wakeup')
        self.slider['value'] = self.setting.default
        self.closePresets()
