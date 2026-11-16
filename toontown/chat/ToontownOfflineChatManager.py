import re

from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObject import DistributedObject

from otp.otpbase import OTPGlobals
from panda3d.toontown import WhisperPopup

from toontown.toonbase import TTLocalizer


class ToontownOfflineChatManager(DistributedObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToontownOfflineChatManager')
    neverDisable = 1

    def generate(self):
        self.cr.chatManager = self
        DistributedObject.generate(self)

    def delete(self):
        self.cr.chatManager = None
        DistributedObject.delete(self)

    def sendChatMessage(self, message):
        toon = base.cr.doId2do.get(base.localAvatar.doId)
        if not toon:
            return

        if not toon.getMuted():
            self.sendUpdate('chatMessage', [message[:OTPGlobals.MaxChatLength]])

    def sendWhisperMessage(self, message, receiverAvId):
        toon = base.cr.doId2do.get(base.localAvatar.doId)
        if not toon:
            return

        if not toon.getMuted():
            self.sendUpdate('whisperMessage', [message[:OTPGlobals.MaxChatLength], receiverAvId])

    def sendWhisperSCMessage(self, msgType, msgIndex, receiverAvId):
        self.sendUpdate('whisperSCMessage', [msgType, msgIndex, receiverAvId])

    def sendWhisperSCToontask(self, taskId, toNpcId, toonProgress, msgIndex, receiverAvId):
        messenger.send('wakeup')
        self.sendUpdate('whisperSCToontaskMessage', [taskId,
                                                     toNpcId,
                                                     toonProgress,
                                                     msgIndex,
                                                     receiverAvId])

    def sendCogMessage(self, cogType, quoteTypeIndex, quoteIndex, displayType):
        self.sendUpdate('cogMessage', [cogType, quoteTypeIndex, quoteIndex, displayType])

    def sendWhisperCogMessage(self, cogType, quoteTypeIndex, quoteIndex, receiverAvId):
        self.sendUpdate('whisperCogMessage', [cogType, quoteTypeIndex, quoteIndex, receiverAvId])

    def sendBattleSOS(self, receiverAvId):
        self.sendUpdate('battleSOS', [receiverAvId])

    def sendSleepAutoReply(self, receiverAvId):
        self.sendUpdate('sleepAutoReply', [receiverAvId])       

    def sendGlobalMessage(self, message):
        toon = base.cr.doId2do.get(base.localAvatar.doId)
        if not toon:
            return

        if not toon.getMuted():
            self.sendUpdate('globalMessage', [message[:OTPGlobals.MaxChatLength]])

    def receiveGlobalMessage(self, fromId, message):
        if base.globalChatWhispers and hasattr(base, 'localAvatar'):
            if fromId in base.cr.onlineAvatars:
                handle = base.cr.onlineAvatars[fromId]
                avName = handle.getName()
            elif fromId == base.localAvatar.doId:
                avName = base.localAvatar.getName()
            else:
                avName = 'Toon'

            message = base.localAvatar.filterChatString(message, fromId)

            print('receiveGlobalMessage %s %s %s' % (fromId, avName, message.encode('utf-8')))
            messenger.send('addToLog', [avName.split('\n')[0], fromId, None, None, 'cobalt', message.strip(),
                                        WhisperPopup.WTGlobal])

            base.localAvatar.setSystemMessage(0, avName.split('\n')[0] + ': ' + message.strip(), WhisperPopup.WTGlobal)

    def globalMessageWarning(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.GlobalChatWarning, WhisperPopup.WTSystem)

    def whisperMessageWarning(self):
        base.localAvatar.setSystemMessage(0, TTLocalizer.WhisperWarning, WhisperPopup.WTSystem)
