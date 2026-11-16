"""
PropSpecial Texture Plane class - A flat plane that you can apply any in-game texture to
"""
from direct.gui.DirectGui import DGG
from direct.gui.DirectEntry import DirectEntry
from direct.gui.DirectFrame import DirectFrame
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import Vec3, NodePath, TextNode, Texture, TextureStage

from otp.otpbase.PythonUtil import bound
from toontown.datapack.DataPackManager import DataPackManager
from toontown.sandbox import PropGlobals
from toontown.sandbox.PropGlobals import PropPool
from toontown.sandbox.PropSpecial import PropSpecial
from toontown.sandbox.PropUI import Dropdown, NumberEntry, TexturePicker
from toontown.toonbase import TTLocalizer
from toontown.toontowngui.AnimatedButton import AnimatedButton
from typing import Optional, Dict


class PropSpecialTexturePlane(PropSpecial):

    def __init__(self, generator, name, uuid, pos = Vec3(0, 0, 0), hpr = Vec3(0, 0, 0), scale = Vec3(1.0, 1.0, 1.0),
                 data: Optional[Dict] = None):
        if data is None:
            data = {}
        PropSpecial.__init__(self, generator, name, uuid, pos, hpr, scale, data)
        self.model = PropPool.getProp(name)
        self.model.reparentTo(self)

        collisions = self.findAllMatches('**/+CollisionNode')
        if collisions:
            for coll in collisions:
                coll.stash()

        self.updateData()

    def deselect(self):
        PropSpecial.deselect(self)
        self.__toggleEditFocus(False)

    def createGui(self):
        PropSpecial.createGui(self)
        # add an edit tab
        ''' Edit Page '''
        editPage = DirectFrame(parent = self.uiFrame, relief = None)
        editTitle = self.makeTitle(parent = editPage, text = TTLocalizer.PropEditorEditTitle)

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
        if base.cr.experimentalFeatures:
            self.pageButtons.append(AnimatedButton(
                    parent = self.uiFrame,
                    image = PropGlobals.PropUi.find(f'**/page_edit'),
                    image_scale = 0.05,
                    text = ('', TTLocalizer.PropEditorAdvancedEditTitle, TTLocalizer.PropEditorAdvancedEditTitle, ''),
                    text_scale = 0.04,
                    text_pos = (0, -0.06),
                    image3_color = (0.8, 0.8, 0.8, 0.5),
                    pos = (PropGlobals.UITabButtonStart + (i+1) / 20, 0, -0.46),
                    command = self.selectPage,
                    extraArgs = [i+1]
            ))

        self.texturePicker = TexturePicker(
            parent = editPage,
            textures = ['phase_14.5/maps/ttoff_t_propgen_texPlane_defaultTex.png'],
            selectedTexture = self.data.get('texture_path', None),
            pos = (0.0, 0.0, 0.2),
            onChange = self.__setTexturePath,
            pickerOffset = Vec3(-.55, 0, -.05),
            pickerParent = editPage,
            scale = 0.7
        )

        self.uiPages.append(editPage)
        editPage.hide()

        ''' Adv Edit Page '''
        if base.cr.experimentalFeatures:
            advEditPage = DirectFrame(parent = self.uiFrame, relief = None,
                                      image = PropGlobals.PropUi.find('**/propui_bg'),
                                      image_scale = (1.308, 1, 1),
                                      scale = 0.9
                                      )
            advEditTitle = self.makeTitle(parent = advEditPage, text = TTLocalizer.PropEditorAdvancedEditTitle)
            btnTextures = (PropGlobals.PropUi.find('**/button_normal'),
                           PropGlobals.PropUi.find('**/button_click'),
                           PropGlobals.PropUi.find('**/button_hover'),
                           PropGlobals.PropUi.find('**/button_normal'))

            self.texOffsetUEntry = NumberEntry(
                parent = advEditPage,
                pos = PropGlobals.UIPosUOffsetPos,
                scale = 0.8,
                incrementScale = 0.01,  # todo: ability to change this in game (perhaps right clicking?)
                minMax = (-100, 100),
                startValue = round(self.data.get('u_offset', 0.0), 5),
                onChange = self.__setTextureCoord,
                onChangeExtraArgs = ['u_offset']
            )
            self.texOffsetVEntry = NumberEntry(
                parent = advEditPage,
                pos = PropGlobals.UIPosVOffsetPos,
                scale = 0.8,
                incrementScale = 0.01,
                minMax = (-100, 1100),
                startValue = round(self.data.get('v_offset', 0.0), 5),
                onChange = self.__setTextureCoord,
                onChangeExtraArgs = ['v_offset']
            )

            self.texScaleUEntry = NumberEntry(
                parent = advEditPage,
                pos = PropGlobals.UIPosUScalePos,
                scale = 0.8,
                incrementScale = 0.01,  # todo: ability to change this in game (perhaps right clicking?)
                minMax = (PropGlobals.PropMinUVScale, PropGlobals.PropMaxUVScale),
                startValue = round(self.data.get('u_scale', 1.0), 5),
                onChange = self.__setTextureCoord,
                onChangeExtraArgs = ['u_scale']
            )
            self.texScaleVEntry = NumberEntry(
                parent = advEditPage,
                pos = PropGlobals.UIPosVScalePos,
                scale = 0.8,
                incrementScale = 0.01,
                minMax = (PropGlobals.PropMinUVScale, PropGlobals.PropMaxUVScale),
                startValue = round(self.data.get('v_scale', 1.0), 5),
                onChange = self.__setTextureCoord,
                onChangeExtraArgs = ['v_scale']
            )

            self.uiPages.append(advEditPage)
            advEditPage.hide()


    def __setTextureCoord(self, val: float, part: str):
        self.data[part] = val
        self.generator.requestUpdateProp(self.uuid)

    def __setTexturePath(self, texture: str):
        """
        Select which texture to apply
        """

        self.data['texture_path'] = texture
        self.generator.requestUpdateProp(self.uuid)

    def updateData(self):
        PropSpecial.updateData(self)

        texture: Texture = DataPackManager.getTexture(self.data.get('texture_path', 'phase_14.5/maps/ttoff_t_propgen_texPlane_defaultTex.png'))

        plane: NodePath = self.model.find('**/Plane')
        self.model.find('**/Plane').setTexture(texture, 1)

        # == Tex Scale ==
        plane.setTexScale(TextureStage.getDefault(), self.data.get('u_scale', 1.0),  self.data.get('v_scale', 1.0))
        plane.setTexOffset(TextureStage.getDefault(), self.data.get('u_offset', 0.0), self.data.get('v_offset', 0.0))

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
        return 20

    @property
    def defaultTextImgScaleX(self):
        return 1.75
