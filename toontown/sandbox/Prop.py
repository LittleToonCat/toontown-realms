import datetime
from typing import Optional, Dict, Any, Tuple, Union

from direct.directnotify import DirectNotifyGlobal
from direct.gui import DirectGuiGlobals
from direct.gui.DirectButton import DirectButton
from direct.gui.DirectFrame import DirectFrame
from direct.gui.OnscreenText import OnscreenText
from direct.interval.LerpInterval import LerpScaleInterval, LerpColorScaleInterval
from direct.interval.MetaInterval import Parallel
from direct.showbase.DirectObject import DirectObject
from panda3d.core import Vec3, NodePath, LColor, VBase4, Point3, \
    TextNode, Vec3F, TransparencyAttrib, StencilAttrib, RenderModeAttrib, Vec4, CollisionNode, CollisionSphere

from otp.otpbase import OTPGlobals
from otp.otpgui import OTPGUIUtils
from otp.otpgui.OTPGUIUtils import Animations
from toontown.moviemaker.MovieMakerGUI import MovieMakerGUI
from toontown.sandbox import PropGlobals
from toontown.sandbox.DistributedBuildLot import ScrollableDropdown
from toontown.sandbox.PropGlobals import LIST_ATTRIBUTES
from toontown.sandbox.PropUI import NumberEntry, Dropdown, NumberInput, ToggleSwitch
from toontown.toonbase import TTLocalizer, ToontownGlobals, ClientSettings

if game.process == 'client':
    from toontown.toontowngui import AnimatedButton


class Prop(NodePath, DirectObject):
    selectedProp = None
    # widgetObj = loader.loadModel('phase_14.5/models/misc/propgen_widgets')  # type: NodePath
    notify = DirectNotifyGlobal.directNotify.newCategory('Prop')

    def __init__(self,
                 generator,
                 name: str,
                 uuid: str,
                 pos: Vec3F = Vec3(0, 0, 0),
                 hpr: Vec3F = Vec3(0, 0, 0),
                 scale: Vec3F = Vec3(1.0, 1.0, 1.0),
                 data: Optional[Dict[str, Any]] = None):
        """
        :param name: Name
        :param pos: Position
        :param hpr: Rotation
        :param scale: Scale
        :param data: Dict of additional data (e.g. for noteblock: data = {'pitch': 3})
        """
        NodePath.__init__(self, name)
        DirectObject.__init__(self)
        if data is None:
            data = {}
        self.uuid = uuid
        if name not in PropGlobals.PropList:
            self.notify.error(f"Prop {name} does not exist in PropList")
            return
        self._name = name
        # These are non-editable attributes of a prop
        self.attributes = PropGlobals.PropList[self.name][LIST_ATTRIBUTES]

        # These are editable attributes of a prop
        self.data = data

        self.model = None
        self.uiFrame = None
        self.widget = None
        self.previewProp: Optional[NodePath] = None
        self.outlinedModel: Optional[NodePath] = None
        self.newPropPos = None
        self.newPropHpr = None
        self.newPropScale = None
        self.newPropColor = None
        self.generator = generator
        self.setTag('spawnPropTag', str(hash(self)))
        self.accept('selectedProp', self.propSelected)
        self.accept('deleteProp', self.propAttemptDelete)
        self.setPosHprScale(pos, hpr, scale)
        if self.data.get('color_scale', None):
            self.setColorScale(*self.data['color_scale'])
            if self.attributes.get('supports_transparency', False):
                self.setTransparency(TransparencyAttrib.MDual)
        self.updateEffect()

        self.snapPoints: Dict[str, Tuple[CollisionSphere, CollisionNode, NodePath]] = {}

    def getPropName(self) -> str:
        return self._name

    def addSnapPoints(self):
        if 'snap_points' in self.attributes:
            for name, point in self.attributes.get('snap_points').items():

                if len(point) == 5:
                    node, xoff, yoff, zoff, radius = point
                    node = self.find(node)
                    if node.isEmpty():
                        node = self
                else:
                    xoff, yoff, zoff, radius = point
                    node = self
                collSphere = CollisionSphere(0, 0, 0, radius)
                collSphere.setTangible(0)
                collNode = CollisionNode(f'snap_{name}@{self.uuid}')
                collNode.setCollideMask(ToontownGlobals.PropGenSnapPointBitMask)
                collNode.addSolid(collSphere)

                collNodePath: NodePath = node.attachNewNode(collNode)
                collNodePath.setPos(xoff, yoff, zoff)
                self.snapPoints[name] = (collSphere, collNode, collNodePath)

    def propSelected(self, prop: NodePath):
        if not base.cr.playGame.getPlace().fsm.getCurrentState().getName() == 'walk':
            return
        if prop == self:
            if Prop.selectedProp is not None and Prop.selectedProp != self:
                Prop.selectedProp.deselect()
            # self.generator.closeNewPropWindow()
            DirectGuiGlobals.defaultClickSound.play()
            Prop.selectedProp = self
            self.notify.debug(f'Selected {self._name} ({self.uuid})')
            self.outlinedModel:NodePath = self.instanceTo(base.outlineNode)
            if not self.previewProp and self.model:
                self.previewProp: NodePath = render.attachNewNode('preview')
                self.previewProp.setPosHprScale(self, Vec3(0), Vec3(0), Vec3(1))
                self.model.copyTo(self.previewProp)
                self.previewProp.setAttrib(
                    RenderModeAttrib.make(RenderModeAttrib.MFilledWireframe, 1, True, LColor(0.5)), 1)
                self.previewProp.setAttrib(
                    StencilAttrib.make(
                        1, StencilAttrib.SCFGreaterThan, StencilAttrib.SOKeep, StencilAttrib.SOKeep,
                        StencilAttrib.SOKeep, 8, 255, 255), 1)
                self.previewProp.setTransparency(TransparencyAttrib.MDual)
                self.previewProp.setAlphaScale(0.4)
            if not self.uiFrame:
                self.createGui()

    def propAttemptDelete(self, prop: NodePath):
        if prop == self:
            self.generator.requestDeleteProp(self.uuid)

    def deselect(self):
        self.notify.debug(f'Deselected {self._name} ({self.uuid})')
        if not self.model.isEmpty():
            self.model.show()
        self.removeAllTasks()
        if self.previewProp:
            self.previewProp.removeNode()
            self.previewProp = None
        if self.outlinedModel:
            self.outlinedModel.removeNode()
            self.outlinedModel = None
        if self.uiFrame:
            self.uiFrame.destroy()
            self.uiFrame = None
            self.uiPages = []
            for cell in base.rightCells:
                base.setCellsAvailable([cell], 1)
        Prop.selectedProp = None

    def createGui(self):
        for cell in base.rightCells:
            base.setCellsAvailable([cell], 0)

        self.newPropPos = self.getPos()
        self.newPropHpr = self.getHpr()
        self.newPropScale = self.getScale()
        self.newPropColor = [self.getColorScale()[0], self.getColorScale()[1],
                             self.getColorScale()[2], self.getColorScale()[3]]
        btnTextures = (PropGlobals.PropUi.find('**/button_normal'),
                       PropGlobals.PropUi.find('**/button_click'),
                       PropGlobals.PropUi.find('**/button_hover'),
                       PropGlobals.PropUi.find('**/button_normal'))
        self.uiFrame = DirectButton(
            parent = base.a2dTopRight,
            pressEffect = 0,
            clickSound = None,
            rolloverSound = None,
            text = self.name,
            text_fg = VBase4(1.0, 1.0, 1.0, 1.0),
            text_shadow = VBase4(0.0, 0.0, 0.0, 0.7),
            text_scale = 0.045,
            text_pos = (0.0, 0.42),
            text_mayChange = 0,
            relief = None,
            pos = (-0.355, 0, -.54),
            image = MovieMakerGUI.gui.find('**/actor_editor_bg'),
            image_scale = OTPGUIUtils.getImageScale(702, 1027, 1.08)
        )

        self.uiFrame.bind(DirectGuiGlobals.B1PRESS, self.dragStart)
        self.uiFrame.bind(DirectGuiGlobals.B1RELEASE, self.dragStop)

        self.cancel = AnimatedButton.AnimatedButton(
            parent = self.uiFrame,
            relief = None,
            image = (MovieMakerGUI.gui.find('**/tab_close'),
                     MovieMakerGUI.gui.find('**/tab_close_p'),
                     MovieMakerGUI.gui.find('**/tab_close_h'),
                     MovieMakerGUI.gui.find('**/tab_close')
                     ),
            pos = PropGlobals.UICloseButton,
            image_scale = 0.078,
            text = ('', TTLocalizer.lClose, TTLocalizer.lClose, ''),
            text_scale = 0.04,
            text_pos = (0, 0.06),
            command = self.deselect
        )

        self.duplicate = AnimatedButton.AnimatedButton(
            parent = self.uiFrame,
            relief = None,
            image = PropGlobals.PropUi.find('**/duplicate'),
            pos = PropGlobals.UIDuplicateButton,
            image_scale = 0.05,
            text = ('', TTLocalizer.PropGeneratorDuplicate, TTLocalizer.PropGeneratorDuplicate, ''),
            text_scale = 0.04,
            text_pos = (0, -0.06),
            command = self.__duplicate
        )

        self.grab = AnimatedButton.AnimatedButton(
            parent = self.uiFrame,
            relief = None,
            image = MovieMakerGUI.gui.find('**/actor_move'),
            pos = PropGlobals.UIGrabButton,
            image_scale = 0.05,
            text = ('', TTLocalizer.PropGeneratorGrab, TTLocalizer.PropGeneratorGrab, ''),
            text_scale = 0.04,
            text_pos = (0, -0.06),
            command = self.__grab
        )

        # TODO: Replace with a delete icon
        self.deleteButton = AnimatedButton.AnimatedButton(
            relief = None,
            parent = self.uiFrame,
            pos = PropGlobals.UIDeleteButton,
            image = MovieMakerGUI.gui.find('**/actor_delete'),
            image_scale = 0.05,
            text = ('', TTLocalizer.PhotoPageDelete, TTLocalizer.PhotoPageDelete, ''),
            text_scale = 0.04,
            text_pos = (0, -0.06),
            command = self.generator.requestDeleteProp, extraArgs = [self.uuid]
        )

        ''' Info Page '''
        infoPage = DirectFrame(parent = self.uiFrame, relief = None)
        infoTitle = self.makeTitle(parent = infoPage, text = TTLocalizer.PropEditorInfoTitle)
        infoLabelUUID = OnscreenText(parent = infoPage,
                                     text = TTLocalizer.PropEditorInfoUUID,
                                     scale = PropGlobals.UIInfoScale,
                                     pos = PropGlobals.UIInfoUUIDLabelPos,
                                     align = TextNode.ALeft,
                                     fg = VBase4(1.0, 1.0, 1.0, 1.0)
                                     )
        infoUUID = OnscreenText(parent = infoPage,
                                text = self.uuid,
                                scale = PropGlobals.UIInfoScale,
                                pos = PropGlobals.UIInfoUUIDInfoPos,
                                align = TextNode.ARight,
                                fg = VBase4(1.0, 1.0, 1.0, 1.0)
                                )
        infoLabelCreator = OnscreenText(parent = infoPage,
                                        text = TTLocalizer.PropEditorInfoCreator,
                                        scale = PropGlobals.UIInfoScale,
                                        pos = PropGlobals.UIInfoCreatorLabelPos,
                                        align = TextNode.ALeft,
                                        fg = VBase4(1.0, 1.0, 1.0, 1.0)
                                        )
        infoCreator = OnscreenText(parent = infoPage,
                                   text = '$UNKNOWN',
                                   scale = PropGlobals.UIInfoScale,
                                   pos = PropGlobals.UIInfoCreatorInfoPos,
                                   align = TextNode.ARight,
                                   fg = VBase4(1.0, 1.0, 1.0, 1.0)
                                   )
        infoLabelSpawnTime = OnscreenText(parent = infoPage,
                                          text = TTLocalizer.PropEditorInfoSpawnTime,
                                          scale = PropGlobals.UIInfoScale,
                                          pos = PropGlobals.UIInfoSpawnTimeLabelPos,
                                          align = TextNode.ALeft,
                                          fg = VBase4(1.0, 1.0, 1.0, 1.0)
                                          )
        infoSpawnTime = OnscreenText(parent = infoPage,
                                     text = '$UNKNOWN',
                                     scale = PropGlobals.UIInfoScale,
                                     pos = PropGlobals.UIInfoSpawnTimeInfoPos,
                                     align = TextNode.ARight,
                                     fg = VBase4(1.0, 1.0, 1.0, 1.0)
                                     )
        infoLabelEditTime = OnscreenText(parent = infoPage,
                                         text = TTLocalizer.PropEditorInfoLastEdit,
                                         scale = PropGlobals.UIInfoScale,
                                         pos = PropGlobals.UIInfoLastEditLabelPos,
                                         align = TextNode.ALeft,
                                         fg = VBase4(1.0, 1.0, 1.0, 1.0)
                                         )
        infoEditTime = OnscreenText(parent = infoPage,
                                    text = '$UNKNOWN',
                                    scale = PropGlobals.UIInfoScale,
                                    pos = PropGlobals.UIInfoLastEditInfoPos,
                                    align = TextNode.ARight,
                                    fg = VBase4(1.0, 1.0, 1.0, 1.0)
                                    )
        infoLastEditor = OnscreenText(parent = infoPage,
                                      text = '$UNKNOWN',
                                      scale = PropGlobals.UIInfoScale,
                                      pos = PropGlobals.UIInfoLastEditorInfoPos,
                                      align = TextNode.ARight,
                                      fg = VBase4(1.0, 1.0, 1.0, 1.0)
                                      )

        spawnerName = self.data.get('spawned_by_name', '$UNKNOWN')
        for emoji in base.emojis:
            spawnerName = spawnerName.replace(f':{emoji}:', f'\x01white\x01\5{emoji}\5\x02')
        if base.cr.getChatFilterMode() >= OTPGlobals.CHAT_FILTER_CENSOR:
            # todo: make this follow whitelist if its set to whitelist
            spawnerName = base.profanityFilter.censor(spawnerName)
        # Populate the data
        infoCreator['text'] = f"{spawnerName} " \
                              f"({self.data.get('spawned_by_avid', '$UNKNOWN')})"

        if 'spawned_on' in self.data:
            infoSpawnTime['text'] = datetime.datetime.fromtimestamp(self.data['spawned_on']).ctime()

        if 'edited_on' in self.data:
            infoEditTime['text'] = datetime.datetime.fromtimestamp(self.data['edited_on']).ctime()
            if 'edited_by_avid' or 'edited_by_name' in self.data:
                name = self.data.get('edited_by_name', '$UNKNOWN')
                for emoji in base.emojis:
                    name = name.replace(f':{emoji}:', f'\x01white\x01\5{emoji}\5\x02')
                if base.cr.getChatFilterMode() >= OTPGlobals.CHAT_FILTER_CENSOR:
                    # todo: make this follow whitelist if its set to whitelist
                    name = base.profanityFilter.censor(name)
                infoLastEditor['text'] = f"by {name} " \
                                         f"({self.data.get('edited_by_avid', '$UNKNOWN')})"
            else:
                infoLastEditor.hide()
        else:
            infoLabelEditTime.hide()
            infoEditTime.hide()
            infoLastEditor.hide()

        ''' Settings Page '''
        settingsPage = DirectFrame(parent = self.uiFrame, relief = None)
        settingsTitle = self.makeTitle(parent = settingsPage, text = TTLocalizer.PropEditorSettingsTitle)
        selectedEffect = 0
        if 'effect' in self.data:
            if self.data['effect'] in list(PropGlobals.Effects.keys()):
                selectedEffect = list(PropGlobals.Effects).index(self.data['effect']) + 1
        effectDropdown = ScrollableDropdown(
            parent = settingsPage,
            items = ['None', *list(PropGlobals.Effects.keys())],
            label = TTLocalizer.PropEditorSettingsEffect,
            pos = PropGlobals.UIPosYPos,
            scale = 0.08,
            selectedItem = selectedEffect,
            onChange = self.__selectEffect
        )

        self.toggleLock = ToggleSwitch(
            parent = settingsPage,
            text = TTLocalizer.PropGeneratorLockProps,
            text_pos = (-5.2, -0.17),
            text_align = TextNode.ALeft,
            text_scale = 0.7,
            scale = 0.06,
            pos = (0, 0, 0),
            toggled = False,
            onChange = self.__toggleLock
        )
        ''' Position Page '''
        positionPage = DirectFrame(parent = self.uiFrame, relief = None)
        positionTitle = self.makeTitle(parent = positionPage, text = TTLocalizer.PropEditorPositionTitle)

        self.posXEntry = NumberInput(
            parent = positionPage,
            pos = PropGlobals.UIPosXPos,
            scale = 0.8,
            text_scale = 0.04,
            incrementScale = 0.5,  # todo: ability to change this in game (perhaps right clicking?)
            startValue = round(self.getX(), 2),
            onChange = self.__setPreviewPos,
            onChangeExtraArgs = [0]
        )
        self.posYEntry = NumberInput(
            parent = positionPage,
            pos = PropGlobals.UIPosYPos,
            scale = 0.8,
            text_scale = 0.04,
            incrementScale = 0.5,
            startValue = round(self.getY(), 2),
            onChange = self.__setPreviewPos,
            onChangeExtraArgs = [1]
        )
        self.posZEntry = NumberInput(
            parent = positionPage,
            pos = PropGlobals.UIPosZPos,
            scale = 0.8,
            text_scale = 0.04,
            incrementScale = 0.5,
            startValue = round(self.getZ(), 2),
            onChange = self.__setPreviewPos,
            onChangeExtraArgs = [2]
        )

        self.rotXEntry = NumberInput(
            parent = positionPage,
            pos = PropGlobals.UIRotXPos,
            scale = 0.8,
            text_scale = 0.04,
            incrementScale = 1,  # todo: ability to change this in game (perhaps right clicking?)
            startValue = round(self.getH(), 1),
            onChange = self.__setPreviewHpr,
            onChangeExtraArgs = [0]
        )
        self.rotYEntry = NumberInput(
            parent = positionPage,
            pos = PropGlobals.UIRotYPos,
            scale = 0.8,
            text_scale = 0.04,
            incrementScale = 1,
            startValue = round(self.getP(), 1),
            onChange = self.__setPreviewHpr,
            onChangeExtraArgs = [1]
        )
        self.rotZEntry = NumberInput(
            parent = positionPage,
            pos = PropGlobals.UIRotZPos,
            scale = 0.8,
            text_scale = 0.04,
            incrementScale = 1,
            startValue = round(self.getR(), 1),
            onChange = self.__setPreviewHpr,
            onChangeExtraArgs = [2]
        )

        self.scaleXEntry = NumberInput(
            parent = positionPage,
            pos = PropGlobals.UIScaleXPos,
            scale = 0.8,
            text_scale = 0.04,
            incrementScale = 0.1,  # todo: ability to change this in game (perhaps right clicking?)
            minMax = (PropGlobals.PropMinScale, PropGlobals.PropMaxScale),
            startValue = round(self.getSx(), 2),
            onChange = self.__setPreviewScale,
            onChangeExtraArgs = [0]
        )
        self.scaleYEntry = NumberInput(
            parent = positionPage,
            pos = PropGlobals.UIScaleYPos,
            scale = 0.8,
            text_scale = 0.04,
            incrementScale = 0.1,
            minMax = (PropGlobals.PropMinScale, PropGlobals.PropMaxScale),
            startValue = round(self.getSy(), 2),
            onChange = self.__setPreviewScale,
            onChangeExtraArgs = [1]
        )
        self.scaleZEntry = NumberInput(
            parent = positionPage,
            pos = PropGlobals.UIScaleZPos,
            scale = 0.8,
            text_scale = 0.04,
            incrementScale = 0.1,
            minMax = (PropGlobals.PropMinScale, PropGlobals.PropMaxScale),
            startValue = round(self.getSz(), 2),
            onChange = self.__setPreviewScale,
            onChangeExtraArgs = [2]
        )

        posSetButton = AnimatedButton.AnimatedButton(
            parent = positionPage,
            text = TTLocalizer.PropEditorSet,
            text_pos = (0, -0.025),
            text_scale = 0.08,
            image_scale = (.42, 1, .11),
            image = btnTextures,
            pos = (0, 0, -0.33),
            scale = .8,
            command = lambda: self.generator.requestUpdateProp(self.uuid)
        )


        ''' Color Page '''
        colorPage = DirectFrame(parent = self.uiFrame, relief = None)
        colorTitle = self.makeTitle(parent = colorPage, text = TTLocalizer.PropEditorColorTitle)

        wantAlpha = self.attributes.get('supports_transparency', False)
        self.colorREntry = NumberEntry(
            parent = colorPage,
            pos = PropGlobals.UIColorRPos if wantAlpha else PropGlobals.UIPosXPos,
            scale = 0.65 if wantAlpha else 0.8,
            incrementScale = 1,
            numberType = int,
            minMax = (0, 255),
            startValue = self.data['color_scale'][0] * 255 if 'color_scale' in self.data else 255,
            onChange = self.__setPreviewColor,
            onChangeExtraArgs = [0]
        )
        self.colorGEntry = NumberEntry(
            parent = colorPage,
            pos = PropGlobals.UIColorGPos if wantAlpha else PropGlobals.UIPosYPos,
            scale = 0.65 if wantAlpha else 0.8,
            incrementScale = 1,
            numberType = int,
            minMax = (0, 255),
            startValue = self.data['color_scale'][1] * 255 if 'color_scale' in self.data else 255,
            onChange = self.__setPreviewColor,
            onChangeExtraArgs = [1]
        )
        self.colorBEntry = NumberEntry(
            parent = colorPage,
            pos = PropGlobals.UIColorBPos if wantAlpha else PropGlobals.UIPosZPos,
            scale = 0.65 if wantAlpha else 0.8,
            incrementScale = 1,
            numberType = int,
            minMax = (0, 255),
            startValue = self.data['color_scale'][2] * 255 if 'color_scale' in self.data else 255,
            onChange = self.__setPreviewColor,
            onChangeExtraArgs = [2]
        )

        if wantAlpha:
            self.colorAEntry = NumberEntry(
                parent = colorPage,
                pos = PropGlobals.UIColorAPos,
                scale = 0.65,
                incrementScale = 1,
                numberType = int,
                minMax = (10, 100),
                startValue = self.data['color_scale'][3] * 100 if 'color_scale' in self.data else 100,
                onChange = self.__setPreviewColor,
                onChangeExtraArgs = [3]
            )

        colorSetButton = AnimatedButton.AnimatedButton(
            parent = colorPage,
            text = TTLocalizer.PropEditorSet,
            text_pos = (0, -0.025),
            text_scale = 0.08,
            image_scale = (.42, 1, .11),
            image = btnTextures,
            pos = (0, 0, -0.23),
            scale = .8,
            command = lambda: self.generator.requestUpdateProp(self.uuid)
        )

        self.uiPages = [infoPage, settingsPage, positionPage, colorPage]
        self.pageButtons = []
        for i, page in enumerate(('info', 'settings', 'position', 'color')):
            title = TTLocalizer.PropEditorPageIdToTitle.get(page, f'${page}')
            btn = AnimatedButton.AnimatedButton(
                parent = self.uiFrame,
                image = PropGlobals.PropUi.find(f'**/page_{page}'),
                image_scale = 0.05,
                text = ('', title, title, ''),
                text_scale = 0.04,
                text_pos = (0, -0.06),
                image3_color = (0.8, 0.8, 0.8, 0.5),
                pos = (PropGlobals.UITabButtonStart + i / 20, 0, -0.46),
                command = self.selectPage,
                extraArgs = [i]
            )
            self.pageButtons.append(btn)

        self.selectPage(0)
        if ClientSettings.GUIAnimations.get():
            Animations.slideDown(self.uiFrame, -.54, intensity = 0.2).start()

    def selectPage(self, index):
        for i, page in enumerate(self.uiPages):
            if i == index:
                page.show()
            else:
                page.hide()

        if 1 < index < 6:
            self.previewProp.show()
        else:
            self.previewProp.hide()

        if index == 5:
            self.model.hide()
            self.previewProp.setAlphaScale(self.getColorScale()[3])
        else:
            self.model.show()
            self.previewProp.setAlphaScale(0.4)

        for i, page in enumerate(self.pageButtons):
            if i == index:
                self.pageButtons[i]['state'] = DirectGuiGlobals.DISABLED
            else:
                self.pageButtons[i]['state'] = DirectGuiGlobals.NORMAL
        # base.localAvatar.enableAvatarControls()

    def dragStart(self, event):
        self.removeTask('dragTask')
        vWidget2render2d = self.uiFrame.getPos(render2d)
        vMouse2render2d = Point3(event.getMouse()[0], 0, event.getMouse()[1])
        editVec = Vec3(vWidget2render2d - vMouse2render2d)
        task = self.addTask(self.dragTask, 'dragTask', appendTask = True)
        task.editVec = editVec

    def dragTask(self, task):
        mwn = base.mouseWatcherNode  # type: MouseWatcher
        if mwn.hasMouse():
            vMouse2render2d = Point3(mwn.getMouseX(), 0, mwn.getMouseY())
            newPos = vMouse2render2d + task.editVec
            self.uiFrame.setPos(render2d, newPos)
        return task.cont

    def dragStop(self, event):
        self.removeTask('dragTask')

    def removeNode(self):
        if Prop.selectedProp == self:
            self.deselect()
        NodePath.removeNode(self)

    def update(self, pos: Vec3F, hpr: Vec3F, scale: Vec3F, data: Dict[str, Any]):
        """
        Update the data of the prop
        """
        self.setPosHprScale(pos, hpr, scale)
        self.data = data
        self.updateData()

    def updateData(self):
        self.notify.debug(f'Updating data for {self.uuid}:\n      ->{self.data}')
        if self.data.get('color_scale', None):
            self.setColorScale(*self.data['color_scale'])
            if self.attributes.get('supports_transparency', False):
                self.setTransparency(TransparencyAttrib.MDual)
        self.updateEffect()

    def updateEffect(self):
        if 'effect' in self.data:
            if self.data['effect'] in PropGlobals.Effects:
                self.setShader(PropGlobals.Effects[self.data['effect']])
        else:
            self.setShader(PropGlobals.BasePropShader)

    def __setPreviewPos(self, value: float, component: int):
        """
        :param value: The position value of the specified component
        :param component: Whether we are using X (0), Y (1), or Z (2)
        """
        # self.notify.debug(f'preview POS[{component}] -> {value}')
        componentToFunc = (
            self.previewProp.setX, self.previewProp.setY, self.previewProp.setZ
        )
        self.newPropPos[component] = value
        if self.previewProp:
            componentToFunc[component](render, value)

    def __setPreviewHpr(self, value: float, component: int):
        """
        :param value: The rotation value of the specified component
        :param component: Whether we are using H (0), P (1), or R (2)
        """
        # self.notify.debug(f'preview HPR[{component}] -> {value}')
        componentToFunc = (
            self.previewProp.setH, self.previewProp.setP, self.previewProp.setR
        )
        self.newPropHpr[component] = value
        if self.previewProp:
            componentToFunc[component](render, value)

    def __setPreviewScale(self, value: float, component: int):
        """
        :param value: The scale value of the specified component
        :param component: Whether we are using X (0), Y (1), or Z (2)
        """
        # self.notify.debug(f'preview SCALE[{component}] -> {value}')
        componentToFunc = (
            self.previewProp.setSx, self.previewProp.setSy, self.previewProp.setSz
        )
        self.newPropScale[component] = value
        if self.previewProp:
            componentToFunc[component](render, value)

    def __setPreviewColor(self, value: float, component: int):
        """
        :param value: The scale value of the specified component
        :param component: Whether we are using X (0), Y (1), or Z (2)
        """
        # self.notify.debug(f'preview COLOR[{component}] -> {value}')
        if component == 3:
            self.newPropColor[component] = value / 100.
        else:
            self.newPropColor[component] = value / 255.
        self.previewProp.setColorScale(*self.newPropColor)

    def __selectEffect(self, effect: int):
        """
        Select which effect to apply
        :param effect: Animation name
        """
        effect = ['None', *list(PropGlobals.Effects.keys())][effect]
        if effect in PropGlobals.Effects:
            self.data['effect'] = effect
            self.generator.requestUpdateProp(self.uuid)
        if effect == 'None' and 'effect' in self.data:
            del self.data['effect']
            self.generator.requestUpdateProp(self.uuid)

    def __toggleLock(self):
        self.data['locked'] = self.toggleLock['toggled']
        self.generator.requestUpdateProp(self.uuid)

    def __grab(self):
        self.generator.openNewPropWindow()

        self.deselect()

        self.generator.propListGui.select(self._name)
        self.generator.propListGui.selectedPropText['text'] = TTLocalizer.PropGeneratorCurrentlyMoving

        self.generator.movingPropUUID = self.uuid

        self.generator.sampleProp.setScale(self.getScale())
        if 'color_scale' in self.data:
            self.generator.sampleProp.setColorScale(*self.data['color_scale'][:3], 0.6)

    def __duplicate(self):
        """
        Duplicates our currently selected prop, but with whatever our preview position is
        """
        self.generator.openNewPropWindow()

        self.deselect()

        self.generator.propListGui.select(self._name)

        self.generator.propListGui.selectedPropText['text'] = TTLocalizer.PropGeneratorCurrentlyDuplicating

        self.generator.duplicatingPropData = self.data

        self.generator.sampleProp.setScale(self.getScale())
        if 'color_scale' in self.data:
            self.generator.sampleProp.setColorScale(*self.data['color_scale'][:3], 0.6)

    @staticmethod
    def makeTitle(parent: NodePath, text: str) -> OnscreenText:
        """
        Simple unified method to create the title for all pages
        """
        return OnscreenText(parent = parent, pos = PropGlobals.UITitlePos, mayChange = 0,
                            font = loader.loadFont(TTLocalizer.NametagFonts[0]),
                            scale = PropGlobals.UITitleScale, text = text)

    @property
    def propName(self):
        return self._name
