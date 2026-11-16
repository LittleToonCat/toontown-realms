"""
PropSpecial Sign class - A prop with editable text
"""
from direct.gui.DirectGui import DGG
from direct.gui.DirectEntry import DirectEntry
from direct.gui.DirectFrame import DirectFrame
from direct.gui.DirectLabel import DirectLabel
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import Vec3, NodePath, TextNode

from otp.otpbase import OTPGlobals
from toontown.sandbox import PropGlobals
from toontown.sandbox.Prop import Prop
from toontown.sandbox.PropGlobals import LIST_MODEL, LIST_ATTRIBUTES, PropPool
from toontown.sandbox.PropSpecial import PropSpecial
from toontown.toonbase import TTLocalizer
from toontown.toontowngui.AnimatedButton import AnimatedButton
from typing import Optional, Dict


class PropSpecialSign(PropSpecial):

    def __init__(self, generator, name, uuid, pos = Vec3(0, 0, 0), hpr = Vec3(0, 0, 0), scale = Vec3(1.0, 1.0, 1.0), data: Optional[Dict] = None):
        PropSpecial.__init__(self, generator, name, uuid, pos, hpr, scale, data)
        self.model = PropPool.getProp(name)
        self.model.reparentTo(self)

        collisions = self.findAllMatches('**/+CollisionNode')
        if collisions:
            for coll in collisions:
                coll.stash()

        self.text = ''

        self.textNode = DirectLabel(
                relief = None,
                parent = self.find('**/prop_text_location*'),
                text_wordwrap = self.attributes['text_wrap'] if 'text_wrap' in self.attributes else None,
                text_align = TextNode.ACenter,
                text = self.text,
                scale = self.attributes['text_scale'] if 'text_scale' in self.attributes else 1)
        self.updateData()

    def createGui(self):
        PropSpecial.createGui(self)
        # add an edit tab
        ''' Sign Page '''
        signPage = DirectFrame(parent = self.uiFrame, relief = None)
        signTitle = self.makeTitle(parent = signPage, text = TTLocalizer.PropEditorEditTitle)

        i = len(self.uiPages)
        self.pageButtons.append(AnimatedButton(
                parent = self.uiFrame,
                image = PropGlobals.PropUi.find(f'**/page_edit'),
                image_scale = 0.05,
                text = ('', TTLocalizer.PropEditorEditTitle, TTLocalizer.PropEditorEditTitle, ''),
                text_scale = 0.04,
                text_pos = (0, -0.06),
                image3_color = (0.8, 0.8, 0.8, 0.5),
                pos = (PropGlobals.UITabButtonStart + i / 20, 0, -0.46),
                command = self.selectPage,
                extraArgs = [i]
        ))
        cdrGui = loader.loadModel('phase_3.5/models/gui/tt_m_gui_sbk_codeRedemptionGui')  # type: NodePath
        dropdwnGui = loader.loadModel('phase_3/models/gui/ttoff_m_gui_opts_dropdown')

        self.textEntry = DirectEntry(
                parent = signPage,
                text_align = TextNode.ACenter,
                relief = None,
                width = self.attributes['text_length'] if 'text_length' in self.attributes else self.defaultTextWidth,
                image = cdrGui.find('**/tt_t_gui_sbk_cdrCodeBox'),
                image_scale = (self.attributes['text_img_scale_x'] if 'text_img_scale_x' in self.attributes else self.defaultTextImgScaleX, 1, 1),
                text_scale = 0.06,
                textMayChange = 1,
                pos = (0, 0, 0),
                scale = 0.7,
                backgroundFocus = 0,
                focus = 0,
                focusInCommand=self.__toggleEditFocus,
                focusInExtraArgs=[True],
                focusOutCommand=self.__toggleEditFocus,
                focusOutExtraArgs=[False],
        )

        submitButton = AnimatedButton(
                image = (dropdwnGui.find('**/dropdown_middle_normal'), 
                         dropdwnGui.find('**/dropdown_middle_click'), 
                         dropdwnGui.find('**/dropdown_middle_hover')),
                image_scale = (4, 1.4, 1.4),
                parent = signPage,
                text = TTLocalizer.PropEditorSet,
                text_scale = 0.7,
                text_pos = (0, -0.2, -0.2),
                pos = (0, 0, -0.2),
                scale = 0.1,
                command = self.setText
        )

        cdrGui.removeNode()

        self.uiPages.append(signPage)
        signPage.hide()

    def deselect(self):
        self.__toggleEditFocus(False)
        PropSpecial.deselect(self)

    def setText(self):
        self.data['text'] = self.textEntry.get()
        self.generator.requestUpdateProp(self.uuid)
        self.__focusOutEditBar()

    def updateData(self):
        PropSpecial.updateData(self)
        if 'text' in self.data:
            self.text = self.data['text']
            for emoji in base.emojis:
                self.text = self.text.replace(f':{emoji}:', f'\x01white\x01\5{emoji}\5\x02')
            if base.cr.getChatFilterMode() >= OTPGlobals.CHAT_FILTER_CENSOR:
                # todo: make this follow whitelist if its set to whitelist
                self.text = base.profanityFilter.censor(self.text)
            self.textNode['text'] = self.text

    def __focusOutEditBar(self):
        self.textEntry['focus'] = 0
        self.textEntry.setFocus()
        self.__toggleEditFocus(False)

    def __toggleEditFocus(self, state):
        messenger.send('wakeup')
        if state:
            localAvatar.chatMgr.disableBackgroundFocus()
            localAvatar.setLocked(True)
            localAvatar.cameraFSM.ignoreHotkeys()
            base.disableToggleHotkeys()
            for btn in self.pageButtons:
                btn['state'] = DGG.DISABLED
        else:
            localAvatar.chatMgr.setBackgroundFocus(base.controlManager.getChatDisabled(), True)
            localAvatar.setLocked(False)
            localAvatar.cameraFSM.initHotkeys()
            base.enableToggleHotkeys()
            for btn in self.pageButtons:
                btn['state'] = DGG.NORMAL

    @property
    def defaultTextWidth(self):
        return 12

    @property
    def defaultTextImgScaleX(self):
        return 1.1
