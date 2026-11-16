# Reflection
# More modern reimplementation / port of the reflection system found in potco
# definitely could probably be optimized more
# Created by drewc Feb 25 2024
from typing import Optional

from direct.showbase.DirectObject import DirectObject
from direct.task.Task import Task
from panda3d.core import NodePath, Plane, Vec3, VBase4, Texture, PNMImage, PlaneNode, Camera, RenderState, \
    CullFaceAttrib, ClipPlaneAttrib, GraphicsOutput, DisplayRegion, \
    GeomVertexFormat, Lens, Mat4

from otp.otpbase import OTPRender

BLACK_CLEAR_COLOR = VBase4(0.0)


class Reflection(DirectObject):
    global_reflection = None

    @classmethod
    def getGlobalReflection(cls):
        return Reflection.global_reflection

    @classmethod
    def initialize(cls, parent: NodePath, resX: int = 512, resY: int = 512):
        if not Reflection.global_reflection:
            Reflection.global_reflection = Reflection('reflection', resX, resY, parent, Plane(Vec3(0, 0, 1), Vec3(0, 0, 0)))
            Reflection.global_reflection.lock = True

    @classmethod
    def uninitialize(cls):
        reflection = Reflection.global_reflection
        if reflection:
            reflection.lock = False
            reflection.delete()

        Reflection.global_reflection = None

    def __init__(self, name: str, width: float, height: float, parent: NodePath, plane: Plane = Plane(Vec3(0, 0, 1), Vec3(0, 0, 0))):
        DirectObject.__init__(self)
        self.lock: bool = False
        self.parent: NodePath = parent
        self.plane: Plane = plane
        self._name: str = name
        self.width: float = width
        self.height: float = height

        self.reflectionState: bool = True
        self.cardCreated: bool = False

        self.reflectionCardNP: Optional[NodePath] = None

        self.reflectionBuffer: Optional[GraphicsOutput] = None
        self.displayRegion: Optional[DisplayRegion] = None
        self.format: Optional[GeomVertexFormat] = None
        self._reflectShowThroughOnly: bool = False

        self.lens: Optional[Lens] = None

        self.clearColor: VBase4 = BLACK_CLEAR_COLOR

        self.reflectionTexture: Texture = Texture('reflection_buffer')
        self.reflectionTexture.setWrapU(Texture.WMClamp)
        self.reflectionTexture.setWrapV(Texture.WMClamp)
        self.reflectionTexture.setMagfilter(Texture.FTLinearMipmapLinear)

        black: PNMImage = PNMImage(1, 1, 4)
        self.blackReflectionTexture: Texture = Texture('black')
        self.blackReflectionTexture.load(black)
        self.blackReflectionTexture.setKeepRamImage(True)
        self.blackReflectionTexture.setCompression(Texture.CMOff)

        self.planeNode: PlaneNode = PlaneNode(f'reflection_plane_{self._name}')
        self.planeNode.setPlane(self.plane)

        self.clipPlane: Plane = plane
        self.clipPlaneNode: PlaneNode = PlaneNode(f'clip_plane_{self._name}')
        self.clipPlaneNode.setPlane(self.clipPlane)

        self.reflectionRoot: NodePath = parent.attachNewNode(f'refection_root_{self._name}')
        self.reflectionPlaneNP: NodePath = self.reflectionRoot.attachNewNode(self.planeNode)
        self.clipPlaneNP: NodePath = self.reflectionRoot.attachNewNode(self.clipPlaneNode)

        self.reflectionCamera: Camera = Camera(f'reflection_camera_{self._name}')
        self.reflectionCamera.setInitialState(RenderState.make(CullFaceAttrib.makeReverse(), ClipPlaneAttrib.make().addOnPlane(self.clipPlaneNP)))
        self.reflectionCameraNP: NodePath = self.reflectionPlaneNP.attachNewNode(self.reflectionCamera)
        self.__createBuffer()
        self.reflectShowThroughOnly(False)

        self.accept('close_main_window', self.__destroyBuffer)
        self.accept('open_main_window', self.__createBuffer)
        self.accept('texture_state_changed', self.__createBuffer)

    def __createBuffer(self):
        self.__destroyBuffer()
        self.reflectionBuffer: GraphicsOutput = base.win.makeTextureBuffer(f'reflection_buffer{self._name}', self.width, self.height, tex = self.reflectionTexture)
        # set this sort very early, the buffer needs to render before the main frame does
        self.reflectionBuffer.setSort(-200)
        self.reflectionBuffer.setClearColor(BLACK_CLEAR_COLOR)
        self.displayRegion: DisplayRegion = self.reflectionBuffer.makeDisplayRegion()
        self.displayRegion.setCamera(self.reflectionCameraNP)
        base.graphicsEngine.openWindows()
        self.reflectionBuffer.setInverted(False)

    def __destroyBuffer(self):
        if self.reflectionBuffer:
            base.graphicsEngine.removeWindow(self.reflectionBuffer)
            self.reflectionBuffer = None

    def enable(self, flag: bool):
        if flag:
            self.reflectionCameraNP.node().setLens(base.camLens)
            self.addTask(self.__reflectionTask, 'reflTask', sort = 49)
            if self.reflectionBuffer is not None:
                self.reflectionBuffer.setActive(True)
            if self.reflectionCardNP:
                self.reflectionCardNP.unstash()

            self.reflectionState = True
        else:
            self.removeTask('reflTask')
            if self.reflectionBuffer is not None:
                self.reflectionBuffer.setActive(False)

            if self.reflectionCardNP:
                self.reflectionCardNP.stash()
            self.reflectionState = False

    def updateReflection(self):
        if self.reflectionBuffer:
            if self.reflectionState:
                self.reflectionBuffer.setClearColor(self.clearColor)
            else:
                self.reflectionBuffer.setClearColor(BLACK_CLEAR_COLOR)

        refMat: Mat4 = base.cam.getMat(self.reflectionPlaneNP)
        reflMat: Mat4 = self.plane.getReflectionMat()
        mat: Mat4 = refMat * reflMat
        self.reflectionCameraNP.setMat(mat)

    def delete(self):
        if not self.lock:
            if self.reflectionCardNP:
                self.reflectionCardNP.removeNode()
            self.reflectionCameraNP.removeNode()
            self.clipPlaneNP.removeNode()
            self.reflectionPlaneNP.removeNode()
            self.reflectionRoot.removeNode()
            self.reflectionBuffer.clearRenderTextures()
            self.reflectionBuffer.removeAllDisplayRegions()
            self.displayRegion = None
            self.__destroyBuffer()
            self.ignore('close_main_window')
            self.ignore('open_main_window')
            self.ignore('texture_state_changed')

    def reflectShowThroughOnly(self, flag: bool):
        if flag:
            self.reflectionCamera.setCameraMask(OTPRender.SkyReflectionCameraBitmask)
            base.render.hide(OTPRender.ReflectionCameraBitmask | OTPRender.SkyReflectionCameraBitmask)
        else:
            self.reflectionCamera.setCameraMask(OTPRender.ReflectionCameraBitmask)
            base.render.show(OTPRender.ReflectionCameraBitmask | OTPRender.SkyReflectionCameraBitmask)
        self._reflectShowThroughOnly = flag

    def __reflectionTask(self, task: Task) -> int:
        self.updateReflection()
        return task.cont
