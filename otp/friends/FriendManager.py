from panda3d.core import *
from direct.distributed import DistributedObject
from direct.directnotify import DirectNotifyGlobal
from otp.otpbase import OTPGlobals

class FriendManager(DistributedObject.DistributedObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('FriendManager')
    neverDisable = 1

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)
        self.__available = 0
        self.gameSpecificFunction = None

    def setAvailable(self, available):
        self.__available = available
        if self.__available and self.gameSpecificFunction:
            self.gameSpecificFunction()

    def getAvailable(self):
        return self.__available

    def setGameSpecificFunction(self, function):
        self.gameSpecificFunction = function

    def executeGameSpecificFunction(self):
        if self.__available and self.gameSpecificFunction:
            self.gameSpecificFunction()

    def generate(self):
        if base.cr.friendManager != None:
            base.cr.friendManager.delete()
        base.cr.friendManager = self
        DistributedObject.DistributedObject.generate(self)

    def disable(self):
        base.cr.friendManager = None
        DistributedObject.DistributedObject.disable(self)

    def delete(self):
        self.gameSpecificFunction = None
        base.cr.friendManager = None
        DistributedObject.DistributedObject.delete(self)

    def up_requestSecret(self):
        self.notify.warning('Sending Request')
        self.sendUpdate('requestSecret', [])

    def requestSecretResponse(self, result, secret):
        messenger.send('requestSecretResponse', [result, secret])

    def up_submitSecret(self, secret):
        self.sendUpdate('submitSecret', [secret])

    def submitSecretResponse(self, result, avId, avName):
        messenger.send('submitSecretResponse', [result, avId, avName])
