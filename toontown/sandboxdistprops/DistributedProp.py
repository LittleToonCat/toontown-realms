# Distributed Prop == Client Side
# Created by drewc Oct 14 2023
from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedNode import DistributedNode
from typing import Optional, List

from panda3d.core import NodePath, RenderModeAttrib, StencilAttrib, TransparencyAttrib, LColor, Vec3, VBase4

from direct.gui.DirectFrame import DirectFrame
from direct.gui.OnscreenText import OnscreenText

from otp.otpgui import OTPGUIUtils
from toontown.moviemaker.MovieMakerGUI import MovieMakerGUI
from toontown.sandbox import PropGlobals
from toontown.sandbox.Prop import Prop
from toontown.sandbox.PropDistributed import PropDistributed
from toontown.toonbase import TTLocalizer
from toontown.toonbase.ToonBaseGlobal import base
from toontown.toontowngui.AnimatedButton import AnimatedButton
from toontown.sandbox.DistributedPropGenerator import DistributedPropGenerator


class DistributedProp(DistributedNode):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistProp')
    notify.setDebug(True)

    def __init__(self, cr):
        DistributedNode.__init__(self, cr)

        self.uuid: Optional[str] = None
        self.generatorDoId: int = 0
        self.generator: Optional[DistributedPropGenerator] = None

        self.model: Optional[NodePath] = None
        self.previewProp: Optional[NodePath] = None

        self.uiFrame: Optional[DirectFrame] = None
        self.closeButton: Optional[AnimatedButton] = None
        self.grab: Optional[AnimatedButton] = None
        self.deleteButton: Optional[AnimatedButton] = None

        self.uiPages: List[DirectFrame] = []
        self.pageButtons: List[AnimatedButton] = []

        self.infoPage: Optional[DirectFrame] = None
        self.infoTitle: Optional[OnscreenText] = None

        self._name: Optional[str] = None

    def announceGenerate(self):
        self.setTag('spawnPropTag', str(hash(self)))
        self.accept('selectedProp', self.propSelected)
        # self.accept('deleteProp', self.propAttemptDelete)

    def delete(self):
        self.ignoreAll()
        self.deselect()
        DistributedNode.delete(self)

    def setUUID(self, uuid: str):
        self.uuid = uuid

    def setGeneratorDoId(self, doId: int):
        self.generatorDoId = doId
        gen = self.cr.doId2do.get(self.generatorDoId, None)
        if gen is None:
            self.notify.warning(f'DistributedPropGenerator {doId} not found. Many functions unavailable.')
        if isinstance(gen, DistributedPropGenerator):
            self.generator = gen
        else:
            self.notify.warning(f'{doId} is not of type DistributedPropGenerator. Many functions unavailable.')

    def setPropName(self, name: str):
        self._name = name

    def getPropName(self) -> str:
        return self._name

    def propSelected(self, prop: NodePath):
        if not base.cr.playGame.getPlace().fsm.getCurrentState().getName() == 'walk':
            return
        if prop == self:
            if Prop.selectedProp is not None and Prop.selectedProp != self:
                Prop.selectedProp.deselect()
            #self.generator.closeNewPropWindow()
            Prop.selectedProp = self
            self.notify.debug(f'Selected ({self.uuid})')
            self.showTightBounds()
            if not self.previewProp and self.model:
                self.previewProp: NodePath = base.render.attachNewNode('preview')
                self.previewProp.setPosHprScale(self, Vec3(0), Vec3(0), Vec3(1))
                self.model.copyTo(self.previewProp)
                self.previewProp.setAttrib(
                        RenderModeAttrib.make(RenderModeAttrib.MFilledWireframe, 1, True, LColor(0.5)), 1)

                self.previewProp.setTransparency(TransparencyAttrib.MDual)
                self.previewProp.setAlphaScale(0.4)
            if not self.uiFrame:
                self.createGui()

    def createGui(self):
        for cell in base.rightCells:
            base.setCellsAvailable([cell], 0)

        self.uiFrame = DirectFrame(
                parent = base.a2dTopRight,
                text = self.getPropName(),
                text_fg = VBase4(0.584, 0.41, 0.21, 1.0),
                text_shadow = VBase4(0.0, 0.0, 0.0, 0.7),
                text_scale = 0.045,
                text_pos = (0.0, 0.42),
                text_mayChange = 0,
                relief = None,
                pos = (-0.355, 0, -.51),
                image = MovieMakerGUI.gui.find('**/actor_editor_bg'),
                image_scale = OTPGUIUtils.getImageScale(646, 932)
        )

        self.closeButton = AnimatedButton(
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

        self.grab = AnimatedButton(
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

        self.deleteButton = AnimatedButton(
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

        self.infoPage = DirectFrame(parent = self.uiFrame, relief = None)
        self.infoTitle = self.makeTitle(parent = self.infoPage, text = TTLocalizer.PropEditorInfoTitle)

    def __grab(self):
        self.generator.openNewPropWindow()

        self.deselect()

        dummyProp: PropDistributed = self.generator.propListNew[self.uuid]

        self.generator.propListGui.select(dummyProp.getPropName())
        self.generator.propListGui.selectedPropText['text'] = TTLocalizer.PropGeneratorCurrentlyMoving

        self.generator.movingPropUUID = self.uuid

        self.generator.sampleProp.setScale(self.getScale())
        if dummyProp.data.get('color_scale', None):
            self.generator.sampleProp.setColorScale(*dummyProp.data['color_scale'][:3], 0.6)

    def deselect(self):
        self.notify.debug(f'Deselected {self.uuid}')

        self.hideBounds()
        if self.previewProp:
            self.previewProp.removeNode()
            self.previewProp = None

        if self.uiFrame:
            self.uiFrame.destroy()
            self.uiFrame = None
            for cell in base.rightCells:
                base.setCellsAvailable([cell], 1)
            self.closeButton = None

        Prop.selectedProp = None

    def makePage(self, name: str, icon: NodePath) -> DirectFrame:
        page = DirectFrame(parent = self.uiFrame, relief = None)

    @staticmethod
    def makeTitle(parent: NodePath, text: str) -> OnscreenText:
        """
        Simple unified method to create the title for all pages
        """
        return OnscreenText(parent = parent, pos = PropGlobals.UITitlePos, mayChange = False,
                            font = base.loader.loadFont(TTLocalizer.NametagFonts[0]),
                            scale = PropGlobals.UITitleScale, text = text)