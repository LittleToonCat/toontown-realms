from panda3d.core import NodePath, Texture, PNMImage, TextureStage
from toontown.toonbase.HTTPDownload import HTTPDownload


class MainMenuBillboard(NodePath, HTTPDownload):
    # TODO: This file doesn't actually exist rn - put this up when we want to start using the billboard
    BillboardUrl = base.config.GetString('billboard-url', 'https://toontownrealms.com/images/billboard-main-menu.png')

    def __init__(self):
        NodePath.__init__(self, 'mainMenuBillboard')
        HTTPDownload.__init__(self, self.BillboardUrl)

        self.board = loader.loadModel('phase_3/models/props/ttoff_m_mainmenu_billboard')
        self.board.reparentTo(self)

        self.downloadDocumentToStream()

    def _handleDownloadComplete(self, taskName):
        # Handle not being a PNG
        if self.isPNGFile():
            # Construct a PNM image from the datastream

            img = PNMImage()
            img.read(data=self.dataStream)
            tex = Texture('billboardTex')
            tex.load(img)

            ts = TextureStage('BillboardMap')
            ts.setPriority(100)

            scr = self.find('**/board')  # type: NodePath
            scr.setColorScaleOff()
            scr.setTexture(ts, tex)
        else:
            self.notify.warning('Billboard image is not a PNG file!')

        HTTPDownload._handleDownloadComplete(self, taskName)

    def removeNode(self):
        self.removeAllTasks()
        NodePath.removeNode(self)
