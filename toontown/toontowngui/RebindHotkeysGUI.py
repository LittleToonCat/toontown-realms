# RebindHotkeysGUI - Replacement for the old ControlSettingsDIaloog
# Created by drewc May 24, 2024
from direct.directnotify import DirectNotifyGlobal
from panda3d.core import NodePath, TextNode
from typing import Type, Tuple

from direct.fsm.FSM import FSM
from direct.fsm.StateData import StateData
from direct.gui.DirectButton import DirectButton
from direct.gui.DirectFrame import DirectFrame
from direct.showbase import ShowBaseGlobal

from direct.gui.OnscreenText import OnscreenText

from toontown.toonbase import TTLocalizer
from toontown.toonbase.HotkeySettings import HotkeySetting
from toontown.toontowngui.HelpButton import HelpButton


class RebindKeyButton(DirectButton, FSM):

    def __init__(self, key: Type[HotkeySetting], **kwargs):
        FSM.__init__(f'rebind{key}')
        gui = base.loader.loadModel('phase_3/models/gui/ttoff_m_gui_opts_buttons', allowInstance = True)
        textures: Tuple[NodePath, ...] = (gui.find('**/button_green_up'), gui.find('**/button_green_down'),
                                          gui.find('**/button_green_rollover'), gui.find('**/button_inactive'))

        opts = (
            ('relief', None, None),
            ('text', key.get(), None),
            ('text_pos', (0.0, -0.012), None),
            ('text_fg', (0.0, 0.0, 0.0, 1.0), None),
            ('text_scale', 0.04, None),
            ('text_align', TextNode.ACenter, None),
            ('image', textures, None),
            ('image_scale', (.4, 1, .11), None),
            ('pressEffect', False, None),
            ('command', self.waitForKey)
        )

        self.defineoptions(kwargs, opts)
        DirectButton.__init__(self, base.hidden)
        self.initialiseoptions(RebindKeyButton)

        self.label = OnscreenText(
            parent = self, align = TextNode.ALeft,
            text = key.getSettingDisplayName(),
            pos = (-1.1, -0.02),
            scale = 0.06,
            wordwrap = 20,
            mayChange = False)

        self.key: Type[HotkeySetting] = key

        if key.getSettingDescription():
            self.helpButton = HelpButton(parent = self, contents = key.getSettingDescription(), pos = (-1.15, 0, 0), inScroll = True)

    def waitForKey(self):
        self['text'] = '...'

class RebindHotkeysGUI(DirectFrame, StateData):
    notify = DirectNotifyGlobal.directNotify.newCategory('RebindHotkeysUI')

    def __init__(self, parent: NodePath = base.aspect2dp):
        DirectFrame.__init__(
            self,
            parent = parent,
            text = TTLocalizer.ControlSettingsTitle,
            text_scale = 0.12,
            text_pos = (0, 0.65)
        )
        StateData.__init__('hotkey-settings-done')
        self.setBin('gui-popup', 0)
