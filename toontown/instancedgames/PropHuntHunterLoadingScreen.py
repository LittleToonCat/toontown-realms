from direct.gui.DirectGui import *

from panda3d.core import *

from toontown.toonbase.ToontownTypes import TPosHpr


class PropHuntHunterLoadingScreen:

    def __init__(self, screenshotPosHpr: TPosHpr = (0, 0, 0, 0, 0, 0)):

        # TODO:
        # - Perhaps hide fake props?

        base.transitions.fadeScreen(1.0)

        w, h = base.win.getSize()
        self.mapBuffer = base.win.makeTextureBuffer("map_buffer", w, h)  # type: GraphicsOutput
        self.mapCam = base.makeCamera(self.mapBuffer)
        self.mapCam.reparentTo(render)
        self.mapCam.setPosHpr(*screenshotPosHpr)

        base.graphicsEngine.renderFrame()

        mapTexture = self.mapBuffer.getScreenshot()
        mapNode = NodePath()
        cm = CardMaker('map-image')
        cm.setFrame(-1.5, 1.5, -1.0, 1.0)
        mapImg = mapNode.attachNewNode(cm.generate())
        mapImg.setTexture(mapTexture, 1)

        texture = self.mapBuffer.getScreenshot()
        self.image = DirectFrame(geom = mapImg,
                                 frameColor = Vec4(1, 1, 1, 1),
                                 frameSize = (-1.1, 1.1, -0.75, 0.75),
                                 geom_scale = 0.7,
                                 pos = (0, 0, 0.05))
        self.image.reparentTo(aspect2dp, DGG.NO_FADE_SORT_INDEX)

        gui = loader.loadModel('phase_14.5/models/gui/ttoff_m_gui_mg_prophunt')
        self.propsAreHidingText = OnscreenImage(image = gui.find('**/ph_hunter_grace'),
                                                scale = (1, 1, 0.3), # what the hell
                                                pos = (0, 0, -0.65))
        self.propsAreHidingText.reparentTo(aspect2dp, DGG.NO_FADE_SORT_INDEX)

    def destroy(self):
        base.transitions.noFade()
        base.graphicsEngine.removeWindow(self.mapBuffer)
        self.mapCam.removeNode()
        self.image.removeNode()
        self.propsAreHidingText.removeNode()
