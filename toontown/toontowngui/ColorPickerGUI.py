""" Color Picker GUI - drewcification 2020 (ported to offline 040721) """

import math

from direct.fsm import StateData
from typing import Type

from direct.gui.DirectGui import *
from direct.gui import DirectGuiGlobals
from panda3d.core import *

from toontown.toonbase import HotkeySettings
from toontown.toonbase.SettingsBase import ListSetting
from toontown.toonbase.ToonBaseGlobal import base
from toontown.toontowngui.ToontownGUIUtils import *
from toontown.toontowngui.ColorUtils import *


class ColorPickerGUI(DirectFrame, StateData.StateData):
    # These shaders probably shouldn't be editable by players. maybe ill move them to a py file later
    hueShader = Shader.load(Shader.SLGLSL,
                            vertex = 'phase_3/shaders/ttoff_sha_ui_generic.vert',
                            fragment = 'phase_3/shaders/ttoff_sha_ui_color_hue_wheel.frag')
    saturationShader = Shader.load(Shader.SLGLSL,
                                   vertex = 'phase_3/shaders/ttoff_sha_ui_generic.vert',
                                   fragment = 'phase_3/shaders/ttoff_sha_ui_color_saturation_slider.frag')
    swatchShader = Shader.load(Shader.SLGLSL,
                               vertex = 'phase_3/shaders/ttoff_sha_ui_generic.vert',
                               fragment = 'phase_3/shaders/ttoff_sha_ui_settings_color_pick_button.frag')

    def __init__(self, setting: Type[ListSetting], startHsva = Vec4(0.0, 0.0, 0.0, 100), includedSwatches = [], parent = aspect2d,
                 **kwargs):
        StateData.StateData.__init__(self, 'color-picker-done')
        gui = base.loader.loadModel("phase_3/models/gui/ttoff_m_gui_opts_colorpicker", allowInstance = True)
        self.defineoptions(kwargs, (
            ('image', gui.find('**/temp_bg'), None),
            ('image_scale', (6, 1, 6), None),
            ('relief', None, None),
            ('state', DirectGuiGlobals.NORMAL, None)
        ))
        DirectFrame.__init__(self, parent)

        self.initialiseoptions(ColorPickerGUI)

        self.setAntialias(AntialiasAttrib.MMultisample)

        self.hsva = startHsva
        self.rgba = (1.0, 1.0, 1.0, 1.0)

        self.lastRot = 0

        self.setting = setting
        self.includedSwatches = includedSwatches
        self.savedSwatches = ClientSettings.SavedSwatches.get()

        buttonModel = base.loader.loadModel('phase_3/models/gui/ttoff_m_gui_opts_buttons')

        closeTextures = (buttonModel.find('**/close_button_normal'), buttonModel.find('**/close_button_click'),
                         buttonModel.find('**/close_button_hover'), buttonModel.find('**/close_button_click'))

        self.closeButton = DirectButton(parent = self, relief = None, pos = (2.5, 0, 2.5), pressEffect = False,
                                        scale = .6, image = closeTextures, command = self.close)

        self.colorWheelFrame = DirectFrame(parent = self, relief = None, scale = 1.7, pos = (1.5, 0, 0.8),
                                           hpr = (0, 0, -90))

        # Hue Wheel
        self.colorWheel = DirectFrame(parent = self.colorWheelFrame,
                                      relief = None,
                                      image = gui.find("**/ttoff_t_gui_opts_colorpicker_hue"),
                                      state = DGG.NORMAL)
        # mouse click events
        self.colorWheel.bind(DGG.B1PRESS, self.beginSelecting)
        self.colorWheel.bind(DGG.B1RELEASE, self.stopSelecting)

        # We can't adjust the saturation from here, so let's do it with a shader
        self.colorWheel.setShader(self.hueShader)

        # The overlay which has a pointer to show where the hue is selected
        # So we can either rotate the wheel, or rotate the pointer, i like the wheel, but we can make a decision
        self.colorWheelOverlay = DirectFrame(parent = self.colorWheelFrame, relief = None,
                                             image = gui.find("**/temp_overlay"),
                                             hpr = (0, 0, 90))

        # Value Slider
        self.valueBarBg = DirectFrame(parent = self, relief = None, image = gui.find("**/cs_slider_bg"),
                                      image_scale = (2, 1, 1), pos = (1.5, 0, -0.4), scale = (1.043, 1, 0.295))
        self.valueBar = DirectSlider(parent = self, relief = None, image = gui.find("**/cs_slider_grad"),
                                     thumb_image = gui.find("**/cs_bar_pointer"), thumb_relief = None,
                                     thumb_frameSize = (-.1, .1, -.9, .5),
                                     thumb_image_scale = (.2, 1, 1.6), image_scale = (2, 1, 1),
                                     pos = (1.5, 0, -0.4), scale = (1, 1, 0.25), scrollSize = .00001,
                                     command = self.setBrightness, value = 100.0, range = (.00, 100.0))

        # the thumb shouldn't accept color scale
        self.valueBar.thumb.setColorScaleOff()

        # Saturation Slider
        self.saturationBarBg = DirectFrame(parent = self, relief = None, image = gui.find("**/cs_slider_bg"),
                                           image_scale = (2, 1, 1), pos = (1.5, 0, -1.0), scale = (1.043, 1, 0.295))
        self.saturationBar = DirectSlider(parent = self, relief = None, image = gui.find("**/cs_slider_grad"),
                                          thumb_image = gui.find("**/cs_bar_pointer"), thumb_relief = None,
                                          thumb_frameSize = (-.1, .1, -.9, .5),
                                          thumb_image_scale = (.2, 1, 1.6), image_scale = (2, 1, 1),
                                          pos = (1.5, 0, -1.0), scale = (1, 1, 0.25), scrollSize = .00001,
                                          command = self.setSaturation, value = 100.0, range = (0.0, 100.0))
        # We can't adjust the saturation from here, so let's do it with a shader
        self.saturationBar.setShader(self.saturationShader)
        # The thumb shouldn't show it tho
        self.saturationBar.thumb.setShaderOff()

        # Alpha Slider
        self.alphaBarBg = DirectFrame(parent = self, relief = None, image = gui.find("**/cs_slider_bg"),
                                      image_scale = (2, 1, 1), pos = (1.5, 0, -1.6), scale = (1.043, 1, 0.295))
        self.alphaBar = DirectSlider(parent = self, relief = None, image = gui.find("**/cs_slider_grad"),
                                     thumb_image = gui.find("**/cs_bar_pointer"), thumb_relief = None,
                                     thumb_frameSize = (-.1, .1, -.9, .5),
                                     thumb_image_scale = (.2, 1, 1.6), image_scale = (2, 1, 1),
                                     pos = (1.5, 0, -1.6), scale = (1, 1, 0.25), scrollSize = .00001,
                                     command = self.setAlpha, value = 100.0, range = (0.0, 100.0))

        # We can't adjust the alpha dynamically from here, so let's do it with a shader
        # self.alphaBar.setShader(self.saturationShader)
        # The thumb shouldn't show it tho
        self.alphaBar.thumb.setShaderOff()

        # Hex Entry
        # self.hexEntry = DirectEntry(
        #         parent = self,
        #         relief = None,
        #         image = gui.find("**/cs_hexinput"),
        #         width = 7,
        #         command = self.setFromHex,
        #         pos = (1, 0, 2.0),
        #         scale = 0.2,
        #         state = DirectGuiGlobals.NORMAL,
        #         image_scale = (8, 1, 1.5),
        #         image_pos = (2.3, 1, .2)
        # )

        self.addPresetButton = DirectButton(parent = self, relief = None, pos = (-1.8, 0, -2.4),
                                            image = (gui.find('**/preset_add'),
                                                     gui.find('**/preset_add_press'),
                                                     gui.find('**/preset_add_hover'),
                                                     gui.find('**/preset_add_disabled')
                                                     ),
                                            state = DirectGuiGlobals.DISABLED,
                                            scale = (0.5, 1, 0.5),
                                            command = self.saveSwatch)
        self.delPresetButton = DirectButton(parent = self, relief = None, pos = (-2.4, 0, -2.4),
                                            image = (gui.find('**/preset_remove'),
                                                     gui.find('**/preset_remove_press'),
                                                     gui.find('**/preset_remove_hover'),
                                                     gui.find('**/preset_remove_disabled')
                                                     ),
                                            state = DirectGuiGlobals.DISABLED,
                                            scale = (0.5, 1, 0.5),
                                            command = self.removeSwatch)
        gui.removeNode()

        self.presetButtons = []
        self.setHsv(*startHsva, True)
        self.createSwatches()
        self.accept(HotkeySettings.ExitActivity.getPressed(), self.close)

    def createSwatches(self):
        for swatch in self.presetButtons:
            swatch.removeNode()
            del swatch
        self.presetButtons = []
        gui = base.loader.loadModel("phase_3/models/gui/ttoff_m_gui_opts_colorpicker")
        paintSplatters = [gui.find("**/preset_splatter_a"), gui.find("**/preset_splatter_b"),
                          gui.find("**/preset_splatter_c"), gui.find("**/preset_splatter_d"),
                          gui.find("**/preset_splatter_e")]
        pos = Vec3(-2.4, 0, 2)

        self.savedSwatches = ClientSettings.SavedSwatches.get()

        savedSwatches = []
        for colorArray in self.savedSwatches:
            savedSwatches.append(Vec4(*colorArray))
        allColors = self.includedSwatches + savedSwatches
        for preset in allColors:
            splatter = gui.find('**/preset_splatter_circle')  # random.choice(paintSplatters)
            b = DirectButton(parent = self, relief = None,
                             pos = pos,
                             image_scale = 0.8,
                             image_color = hsvToRgb(preset[0] / 360.,
                                                    preset[1] / 100.,
                                                    preset[2] / 100.,
                                                    preset[3] / 100.),
                             image = (splatter, splatter, splatter),
                             command = self.setHsv, extraArgs = [*preset, True]
                             )
            b.setShader(self.swatchShader)
            self.presetButtons.append(b)
            pos.addX(0.8)
            if not (allColors.index(preset) + 1) % 4:
                pos.setX(-2.4)
                pos.addZ(-0.8)
            if allColors.index(preset) >= 19:  # todo: scroll bar
                break
        gui.removeNode()

        self.checkForSwatches()

    def destroy(self):
        self.stopSelecting(0)
        if self.colorWheelFrame:
            self.colorWheelFrame.destroy()

        if self.colorWheel:
            self.colorWheel.destroy()

        if self.colorWheelOverlay:
            self.colorWheelOverlay.destroy()

        if self.valueBar:
            self.valueBar.destroy()

        if self.saturationBar:
            self.saturationBar.destroy()

        DirectFrame.destroy(self)

    def close(self):
        messenger.send(self.doneEvent)
        self.destroy()

    def beginSelecting(self, event):
        if not base.mouseWatcherNode.hasMouse():
            return
        mx = base.mouseWatcherNode.getMouseX()
        my = base.mouseWatcherNode.getMouseY()

        self.startRot = math.degrees(math.atan2(self.colorWheel.getX(base.render2d) - mx,
                                                self.colorWheel.getZ(base.render2d) - my))

        self.addTask(self.selectTask, 'color-wheel-selection')

    def stopSelecting(self, event):
        self.removeTask('color-wheel-selection')
        self.lastRot = self.colorWheel.getR()

    def selectTask(self, task):
        """ Calculate and rotate the hue wheel """
        if not base.mouseWatcherNode.hasMouse():
            return task.done
        mx = base.mouseWatcherNode.getMouseX()
        my = base.mouseWatcherNode.getMouseY()

        hue = math.degrees(math.atan2(self.colorWheel.getX(render2d) - mx,
                                      self.colorWheel.getZ(render2d) - my))

        # We don't want hue to be below 0, needs to be 0-360 scale
        hue = self.lastRot + (hue - self.startRot)
        if hue < 0:
            hue += 360
        if hue > 360:
            hue -= 360
        self.colorWheel.setR(hue)

        # update the toon color
        self.setHsv(hue, self.saturationBar['value'], self.valueBar['value'], self.alphaBar['value'])
        return task.cont

    def setHsv(self, hue, saturation, value, alpha, fromSwatch = False):
        # if this is called from a swatch, hex input, or randomize, update the sliders
        if self.valueBar['value'] != value: self.valueBar['value'] = value
        if self.saturationBar['value'] != saturation: self.saturationBar['value'] = saturation
        if self.alphaBar['value'] != alpha: self.alphaBar['value'] = alpha

        self.updateColor(int(hue), int(saturation), int(value), int(alpha), fromSwatch)

    def setBrightness(self):
        self.setHsv(self.hsva[0] * 360., self.hsva[1] * 100., self.valueBar['value'], self.hsva[3] * 100)

    def setSaturation(self):
        self.setHsv(self.hsva[0] * 360., self.saturationBar['value'], self.hsva[2] * 100., self.hsva[3] * 100)

    def setAlpha(self):
        self.setHsv(self.hsva[0] * 360., self.hsva[1] * 100., self.hsva[2] * 100., self.alphaBar['value'])

    def setFromRgbaFloat(self, r, g, b, a = 1.0):
        hsv = rgbToHsv(r, g, b)
        self.updateColor(hsv[0] * 360., hsv[1] * 100., hsv[2] * 100., a * 100, True)

    def setFromRgbaInt(self, r, g, b, a = 255):
        r = min(r, 255) / 255.
        g = min(g, 255) / 255.
        b = min(b, 255) / 255.
        a = min(a, 255) / 255.
        self.setFromRgbaFloat(r, g, b, a)

    def updateColor(self, hue, saturation, value, alpha, fromSwatch = False):
        self.hsva = hsvIntToFloat(hue, saturation, value, alpha)

        self.rgba = hsvToRgb(*self.hsva)

        # Adjust the brightness and saturation of the color wheel to accurately(-ish) reflect the values
        self.colorWheel.setShaderInput('matColor', Vec2(saturation / 100., value / 100.))

        # Adjust the value bar to accurately reflect the hue and saturation values
        # The value bar has a static hue and brightness, so we can do the saturation scale
        # directly from here instead of a shader
        self.valueBar.setColorScale(Vec4(hsvToRgb(hue / 360., saturation / 100., 1)))

        # Adjust the saturation bar to accurately reflect the hue and brightness values
        self.saturationBar.setShaderInput('matColor', Vec2(hue / 360., value / 100.))

        # Update the hex box
        # self.hexEntry.set('#%02x%02x%02x%02x' % (
        #    int(self.rgba[0] * 255), int(self.rgba[1] * 255), int(self.rgba[2] * 255), int(self.rgba[3] * 255)))

        # We only wanna manually set the hue if we selected from swatch or random
        if fromSwatch:
            self.colorWheel.setR(hue)
            self.lastRot = hue

        # if this is called from a swatch, hex input, or randomize, update the sliders
        if self.valueBar['value'] != value:
            self.valueBar['value'] = value
        if self.saturationBar['value'] != saturation:
            self.saturationBar['value'] = saturation
        if self.alphaBar['value'] != alpha:
            self.alphaBar['value'] = alpha
        self.checkForSwatches()

        base.messenger.send(f"color-picked-{self.setting}")

    def setFromHex(self, text = None):
        """
        Set the color using a hex value specified
        in the input box
        """
        # todo: fix this? it seems to do some wacky rounding
        if not text:
            text = self.hexEntry.get()
        # the input should look like #RRGGBB - 7 characters
        # todo: handle if they dont put an #, that logically should still work
        if len(text) != 9 or text[0] != '#':
            return
        try:
            # convert them from base 16 to 0-255
            self.setFromRgbaInt(
                    int("0x" + text[1:3], 16),
                    int("0x" + text[3:5], 16),
                    int("0x" + text[5:7], 16),
                    int("0x" + text[7:9], 16)
            )
        except:
            # The user probably just inputed something incorretly
            # Just do nothing, maybe we can put a notice later
            pass

    def showTooltip(self, text, event):
        """ Creates a tooltip which shows `text` on hover """
        self.currentTooltip = ToolTip(text)

    def removeTooltip(self, event):
        """ Removes a tooltip when unhovering """
        if hasattr(self, 'currentTooltip'):
            self.currentTooltip.destroy()
            del self.currentTooltip

    def saveSwatch(self):
        """
        Saves a swatch for future reuse
        :param color:
        :param name:
        :return:
        """
        savedList = ClientSettings.SavedSwatches.get()
        hsva = hsvFloatToInt(*self.hsva)
        if hsva not in savedList:
            savedList.append(hsva)
        ClientSettings.SavedSwatches.set(savedList)
        self.createSwatches()
        return

    def removeSwatch(self):
        """
        Removes previously saved swatch
        :param todo:
        :return:
        """
        savedList = ClientSettings.SavedSwatches.get()
        hsva = hsvFloatToInt(*self.hsva)
        if hsva in savedList:
            savedList.remove(hsva)
        ClientSettings.SavedSwatches.set(savedList)
        self.createSwatches()
        return

    def checkForSwatches(self):
        """
        checks if the current color is a saved swatch, if so, enable the remove button and disable the add
        :return:
        """

        if hsvFloatToInt(*self.hsva) in self.includedSwatches + self.savedSwatches:
            self.delPresetButton['state'] = DirectGuiGlobals.NORMAL
            self.addPresetButton['state'] = DirectGuiGlobals.DISABLED
        elif hsvFloatToInt(*self.hsva) in self.includedSwatches and \
                hsvFloatToInt(*self.hsva) not in self.savedSwatches:
            self.delPresetButton['state'] = DirectGuiGlobals.DISABLED
            self.addPresetButton['state'] = DirectGuiGlobals.DISABLED
        else:
            self.delPresetButton['state'] = DirectGuiGlobals.DISABLED
            self.addPresetButton['state'] = DirectGuiGlobals.NORMAL
        if len(self.savedSwatches) > 15:
            self.addPresetButton['state'] = DirectGuiGlobals.DISABLED
