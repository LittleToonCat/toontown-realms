from direct.gui.OnscreenImage import OnscreenImage
from panda3d.core import *
from direct.directnotify import DirectNotifyGlobal

from toontown.toontowngui.AnimatedButton import AnimatedButton
from toontown.toonbase.HTTPDownload import HTTPDownload

MaxFileSizeMB = 3


class MiniserverIconBase(HTTPDownload):
    def __init__(self, url):
        HTTPDownload.__init__(self, url, MaxFileSizeMB)

        self.setTransparency(TransparencyAttrib.MAlpha)

        self.downloadDocumentToStream()

    def destroy(self):
        self.removeAllTasks()

    def _taskRan(self):
        self.setR(self.getR() + (10 * globalClock.getDt()))

    def _handleDownloadComplete(self, taskName):
        # Handle not being a PNG - there was the one time the website
        # was taken down so these images disappeared from the web server
        if self.isPNGFile() or self.isJPGFile():
            # Construct a PNM image from the datastream

            img = PNMImage()
            img.read(data=self.dataStream)

            img.addAlpha()

            # Generate a circular mask image
            maskImage = PNMImage(img.getXSize(), img.getYSize(), 1)

            # this creates the circle itself
            maskImage.renderSpot(fg=VBase4(1.0), bg=VBase4(0.0), min_radius=1, max_radius=1)

            # take the alpha channel from the mask image, and set as the channel for the actual image
            img.copyChannel(maskImage, 0, 3)
            tex = Texture('iconTex')
            tex.load(img)
            self['image'] = tex

            # We have to call this again for some reason
            self.setTransparency(TransparencyAttrib.MAlpha)

            maskImage.clear()
            del maskImage
            self.setR(0)
        else:
            self.notify.warning('Miniserver icon is not a PNG or JPG file!')

        HTTPDownload._handleDownloadComplete(self, taskName)


class MiniserverIcon(OnscreenImage, MiniserverIconBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('MiniserverIcon')

    def __init__(self, url, parent=aspect2d, pos=None, scale=None):
        OnscreenImage.__init__(self, image='phase_3/maps/cog.png', parent=parent, pos=pos, scale=scale)
        MiniserverIconBase.__init__(self, url)

    def destroy(self):
        MiniserverIconBase.destroy(self)
        OnscreenImage.destroy(self)


class MiniserverIconButton(AnimatedButton, MiniserverIconBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('MiniserverIconButton')

    def __init__(self, url, parent=aspect2d, scale=None, **kwargs):
        optiondefs = (('relief', None, None), ('image', 'phase_3/maps/cog.png', None), ('scale', scale, None))
        self.defineoptions(kwargs, optiondefs)
        AnimatedButton.__init__(self, parent=parent, scale=scale)
        self.initialiseoptions(MiniserverIconButton)
        MiniserverIconBase.__init__(self, url)

    def destroy(self):
        MiniserverIconBase.destroy(self)
        AnimatedButton.destroy(self)
