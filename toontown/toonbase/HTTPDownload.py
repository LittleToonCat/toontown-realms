from panda3d.core import *

from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.showbase.DirectObject import DirectObject


class HTTPDownload(DirectObject):
    notify = directNotify.newCategory('HTTPDownload')

    ThrottleDownload = config.GetBool('http-download-throttle', False)

    # Header of a PNG file; checking this is common enough to where I put it here
    PNGHeader = '89504e470d0a1a0a'
    JPGHeader = 'ffd8'
    GIFHeader = '474946'

    def __init__(self, url, maxFileSize=-1, persistentChannel=False):
        DirectObject.__init__(self)

        self.maxFileSize = maxFileSize

        self.dataStream = None

        http = HTTPClient.getGlobalPtr()  # type: HTTPClient
        self.url = DocumentSpec(url)
        self.ch = http.makeChannel(persistentChannel)  # type: HTTPChannel

        if self.ThrottleDownload:
            self.ch.setDownloadThrottle(1)
            self.ch.setMaxBytesPerSecond(2000)

    def uniqueName(self, baseStr):
        return baseStr + '-' + str(id(self))

    def beginGetHeader(self):
        self.ch.beginGetHeader(self.url)
        self.addTask(self.__downloadTask, self.uniqueName('downloadHeaderTask'))

    def beginGetDocument(self):
        self.ch.beginGetDocument(self.url)
        self.addTask(self.__downloadTask, self.uniqueName('downloadDocumentTask'))

    def downloadHeaderToStream(self):
        self.dataStream = StringStream()
        self.ch.beginGetHeader(self.url)
        self.ch.downloadToStream(self.dataStream)
        self.addTask(self.__downloadTask, self.uniqueName('downloadHeaderToStreamTask'))

    def downloadHeaderToFile(self, file):
        self.ch.beginGetHeader(self.url)
        self.ch.downloadToFile(file)
        self.addTask(self.__downloadTask, self.uniqueName('downloadHeaderToFileTask'))

    def downloadDocumentToStream(self):
        self.dataStream = StringStream()
        self.ch.beginGetDocument(self.url)
        self.ch.downloadToStream(self.dataStream)
        self.addTask(self.__downloadTask, self.uniqueName('downloadDocumentToStreamTask'))

    def downloadDocumentToFile(self, file):
        self.ch.beginGetDocument(self.url)
        self.ch.downloadToFile(file)
        self.addTask(self.__downloadTask, self.uniqueName('downloadDocumentToFileTask'))

    def __cleanupDataStream(self):
        if self.dataStream:
            self.dataStream.clearData()
            del self.dataStream

    def __downloadTask(self, task):
        self._taskRan()

        result = self.ch.run()

        if self.maxFileSize != -1:
            if self.ch.getFileSize() > self.maxFileSize * 1000000:
                self.notify.warning(f'File data is exceeding limit of {self.maxFileSize}MB! Stopping Download. '
                                    f'({self.url.url} @ {self.ch.getFileSize() / 1000000.}MB)')

                self.__cleanupDataStream()
                return task.done

        if result == 0:
            if self.ch.getStatusCode() != 200:
                return task.done

            self._handleDownloadComplete(task.name)
            return task.done
        return task.cont

    def _taskRan(self):
        # Sometimes we want to do something each time the task runs
        pass

    def _handleDownloadComplete(self, taskName):
        self.notify.info(f'{taskName} completed. Error: {self.ch.getStatusCode()} ({self.ch.getStatusString()})')
        self.__cleanupDataStream()

    # Check for header of a PNG file; checking this is common enough to where I put it here
    def isPNGFile(self) -> bool:
        if not self.dataStream.getDataSize():
            # No data so obviously not a PNG
            return False
        return self.dataStream.getData()[0:8].hex().lower() == self.PNGHeader

    def isJPGFile(self) -> bool:
        if not self.dataStream.getDataSize():
            # No data so obviously not
            return False
        return self.dataStream.getData()[0:2].hex().lower() == self.JPGHeader
