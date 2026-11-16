import time

from direct.directnotify import DirectNotifyGlobal
from direct.distributed.ClockDelta import globalClockDelta
from direct.distributed.DistributedObjectAI import DistributedObjectAI
from direct.showbase import GarbageReport

from .GarbageLeakServerEventAggregatorAI import GarbageLeakServerEventAggregatorAI
from otp.otpbase import OTPGlobals


class TimeManagerAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('TimeManagerAI')

    def __init__(self, air):
        DistributedObjectAI.__init__(self, air)
        self.avId2disconnectcode = {}
        self.avId2exceptioninfo = {}
        self._lastZombieContext = None

        if not __debug__:
            # double-check that we're not implementing a client-sendable debug DC method in production
            if hasattr(self, 'checkForGarbageLeaks'):
                self.notify.error('checkForGarbageLeaks should not be defined outside of __debug__')

    def requestServerTime(self, context):
        avId = self.air.getAvatarIdFromSender()
        if not avId:
            return

        self.sendUpdateToAvatarId(avId, 'serverTime',
                                  [context, globalClockDelta.getRealNetworkTime(bits=32), int(time.time())])

    def setDisconnectReason(self, disconnectCode):
        avId = self.air.getAvatarIdFromSender()
        if not avId:
            return

        self.avId2disconnectcode[avId] = disconnectCode
        self.air.writeServerEvent('disconnect-reason', avId=avId,
                                  reason=OTPGlobals.DisconnectReasons.get(disconnectCode, 'unknown'))

    def setExceptionInfo(self, info):
        avId = self.air.getAvatarIdFromSender()
        if not avId:
            return

        self.avId2exceptioninfo[avId] = info
        self.air.writeServerEvent('client-exception', avId=avId, info=info)

    def checkAvOnDistrict(self, context, doId):
        self._lastZombieContext = context
        present = self.air.doId2do.get(doId) is not None
        self.sendUpdate('checkAvOnDistrictResult', [context, doId, present])

    if __debug__:
        def refreshModules(self):
            sender = self.air.getMsgSender()
            response = self.air.refresh()
            self.notify.info(response)
            self.sendUpdateToChannel(sender, 'refreshResponse', [response])

        def checkForGarbageLeaks(self, wantReply):
            senderId = self.air.getAvatarIdFromSender()
            self.notify.info("checking for garbage leaks requested by %s" % senderId)
            numLeaks = GarbageReport.checkForGarbageLeaks()
            if wantReply:
                requesterId = self.air.getAvatarIdFromSender()
                self.sendUpdateToAvatarId(requesterId, 'setNumAIGarbageLeaks', [numLeaks])

        def setClientGarbageLeak(self, num, description):
            messenger.send(GarbageLeakServerEventAggregatorAI.ClientLeakEvent, [num, description])
