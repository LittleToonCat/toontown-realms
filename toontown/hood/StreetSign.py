from panda3d.core import *

from direct.directnotify.DirectNotifyGlobal import directNotify

from toontown.toonbase.HTTPDownload import HTTPDownload


class StreetSign(HTTPDownload):
    StreetSignFileName = config.GetString('street-sign-filename', 'texture.png')
    StreetSignBaseDir = config.GetString('street-sign-base-dir', 'sign')
    StreetSignUrl = base.config.GetString('street-sign-url', 'https://toontownrealms.com/images/')
    notify = directNotify.newCategory('StreetSign')

    def __init__(self):
        HTTPDownload.__init__(self, self.StreetSignUrl + self.StreetSignFileName, persistentChannel=True)

        self.notify.info('Street sign url is %s' % self.StreetSignUrl)

        # Make street sign directory if doesn't exist
        Filename(self.StreetSignBaseDir + '/.').makeDir()

        self.isPNG = False

        # Download header before check so we can see if it's a PNG first
        self.downloadHeaderToStream()

        self.__checkIfUpToDate()

    def __checkIfUpToDate(self):
        # Handle not being a PNG
        if not self.isPNG:
            self.notify.warning('Street Sign image is not a PNG file!')
            return

        localFilename = Filename(self.StreetSignBaseDir, self.StreetSignFileName)

        size = self.ch.getFileSize()
        doc = self.ch.getDocumentSpec()

        localSize = localFilename.getFileSize()

        outOfDate = True

        # Do the sizes match?
        if size == localSize:
            # Does the file even have a date to compare with?
            if doc.hasDate():
                date = doc.getDate()
                localDate = HTTPDate(localFilename.getTimestamp())
                # Do the file timestamps match?
                if localDate.compareTo(date) > 0:
                    outOfDate = False
                    self.notify.info('Street Sign is up to date')

        if outOfDate:
            # If neither of these match, download new version
            self.downloadDocumentToFile(localFilename)

    def _handleDownloadComplete(self, taskName):
        # Gotta do the PNG check here before the StringStream is cleaned up
        if taskName == self.uniqueName('downloadHeaderToStreamTask'):
            # Store so we can have this information later
            self.isPNG = self.isPNGFile()
        HTTPDownload._handleDownloadComplete(self, taskName)
