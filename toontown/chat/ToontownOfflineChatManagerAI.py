from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI
from direct.task import Task

from toontown.toonbase import TTLocalizer


class ToontownOfflineChatManagerAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToontownOfflineChatManagerAI')

    def __init__(self, air):
        DistributedObjectAI.__init__(self, air)
        self.recentAvatars = {}
        self.warnedAvatars = {}

    def announceGenerate(self):
        DistributedObjectAI.announceGenerate(self)
        taskMgr.doMethodLater(1.0, self.globalCooldown, self.uniqueName('globalCooldown'))

    def chatMessage(self, message):
        avId = self.air.getAvatarIdFromSender()
        av = self.air.doId2do.get(avId)
        if not av:
            self.air.writeServerEvent('suspicious', avId = avId, issue = 'AV not present when sending a chat message.',
                                      message=message)
            return
        if av.getMuted()[0]:
            self.air.writeServerEvent('suspicious', avId = avId, issue = 'AV sent a chat message while muted.',
                                      message = message)
            return

        accId = self.air.getAccountIdFromSender()
        senderName = av.getName()
        av.sendUpdate('setTalk', [avId, accId, senderName, message])
        self.air.logEvent(0, avId, senderName, accId, message)
        self.air.writeServerEvent('chat-message-said', avId = avId, message = message)

    def whisperMessage(self, message, receiverAvId):
        accId = self.air.getAccountIdFromSender()
        avId = self.air.getAvatarIdFromSender()
        av = self.air.doId2do.get(avId)
        if not av:
            self.air.writeServerEvent('suspicious', avId = avId, issue = 'AV not present when sending a whisper.',
                                      message=message)
            return
        if av.getMuted()[0]:
            self.air.writeServerEvent('suspicious', avId = avId, issue = 'AV sent a whisper while muted.',
                                      message = message)
            return
        receiver = self.air.doId2do.get(receiverAvId)
        if not receiver:
            return

        if avId in self.recentAvatars:
            if self.recentAvatars.get(avId) >= 3:
                self.sendUpdateToAvatarId(avId, 'whisperMessageWarning', [])
                if avId in self.warnedAvatars:
                    self.warnedAvatars[avId] += 1
                if avId not in self.warnedAvatars:
                    self.warnedAvatars[avId] = 1
                if self.warnedAvatars.get(avId) >= 10:
                    self.deliverBan(av)
                    self.air.writeServerEvent('suspicious', accId = accId, issue = f'Banned a user for a potential exploit with avId of {avId}!', message = message)
                return
            self.recentAvatars[avId] += 1
        if avId not in self.recentAvatars:
            self.recentAvatars[avId] = 1

        senderName = av.getName()
        receiver.sendUpdate('setTalkWhisper', [avId, accId, senderName, message])

        self.air.logEvent(2, avId, senderName, accId, message, receiverAvId)

        self.air.writeServerEvent('whisper-message-said', avId = avId, receiverAvId = receiverAvId, message = message)

    def whisperSCMessage(self, msgType, msgIndex, receiverAvId):
        fromId = self.air.getAvatarIdFromSender()
        if fromId == receiverAvId:
            return

        receiver = self.air.doId2do.get(receiverAvId)
        if receiver:
            receiver.sendUpdate('setWhisperSCFrom', [fromId, msgType, msgIndex])

    def whisperSCToontaskMessage(self, taskId, toNpcId, toonProgress, msgIndex, receiverAvId):
        fromId = self.air.getAvatarIdFromSender()
        if fromId == receiverAvId:
            return

        receiver = self.air.doId2do.get(receiverAvId)
        if receiver:
            receiver.sendUpdate('setWhisperSCToontaskFrom', [fromId, taskId, toNpcId, toonProgress, msgIndex])

    def cogMessage(self, cogType, quoteTypeIndex, quoteIndex, displayType):
        avId = self.air.getAvatarIdFromSender()
        av = self.air.doId2do.get(avId)
        if not av:
            self.air.writeServerEvent('suspicious', avId = avId, issue = 'AV not present when sending a cog message.',
                                      message=message)
            return

        av.sendUpdate('setTalkCog', [avId, cogType, quoteTypeIndex, quoteIndex, displayType])

    def whisperCogMessage(self, cogType, quoteTypeIndex, quoteIndex, receiverAvId):
        fromId = self.air.getAvatarIdFromSender()
        if fromId == receiverAvId:
            return

        receiver = self.air.doId2do.get(receiverAvId)
        if receiver:
            receiver.sendUpdate('setWhisperSCCogFrom', [fromId, cogType, quoteTypeIndex, quoteIndex])

    def battleSOS(self, receiverAvId):
        fromId = self.air.getAvatarIdFromSender()
        if fromId == receiverAvId:
            return

        receiver = self.air.doId2do.get(receiverAvId)
        if receiver:
            receiver.sendUpdate('receiveBattleSOS', [fromId])

    def sleepAutoReply(self, receiverAvId):
        fromId = self.air.getAvatarIdFromSender()
        if fromId == receiverAvId:
            return

        receiver = self.air.doId2do.get(receiverAvId)
        if receiver:
            receiver.sendUpdate('setSleepAutoReply', [fromId])

    def globalMessage(self, message):
        if not self.air.wantGlobalChat:
            return
        avId = self.air.getAvatarIdFromSender()
        av = self.air.doId2do.get(avId)
        if not av:
            self.air.writeServerEvent('suspicious', avId = avId, issue = 'AV not present when sending a global message.',
                                      message=message)
            return
        if av.getMuted()[0]:
            self.air.writeServerEvent('suspicious', avId = avId, issue = 'AV sent a global message while muted.',
                                      message = message)
            return

        if avId in self.recentAvatars:
            if self.recentAvatars.get(avId) >= 3:
                self.sendUpdateToAvatarId(avId, 'globalMessageWarning', [])
                if avId in self.warnedAvatars:
                    self.warnedAvatars[avId] += 1
                if avId not in self.warnedAvatars:
                    self.warnedAvatars[avId] = 1
                if self.warnedAvatars.get(avId) >= 10:
                    self.deliverBan(av)
                    accId = self.air.getAccountIdFromSender()
                    self.air.writeServerEvent('suspicious', accId = accId, issue = f'Banned a user for a potential exploit with avId of {avId}!', message = message)
                return
            self.recentAvatars[avId] += 1
        if avId not in self.recentAvatars:
            self.recentAvatars[avId] = 1

        self.sendUpdate('receiveGlobalMessage', [avId, message])
        accId = self.air.getAccountIdFromSender()
        senderName = av.getName()
        self.air.logEvent(1, avId, senderName, accId, message)
        self.air.writeServerEvent('global-message-said', avId = avId, message = message)

    def globalCooldown(self, task):
        for avId in list(self.recentAvatars.keys()):
            self.recentAvatars[avId] -= 1
            if self.recentAvatars.get(avId) <= 0:
                del self.recentAvatars[avId]

        for avId in list(self.warnedAvatars.keys()):
            self.warnedAvatars[avId] -= 1
            if self.warnedAvatars.get(avId) <= 0:
                del self.warnedAvatars[avId]

        return Task.again

    def deliverBan(self, toon):
        toon.sendSetBan(TTLocalizer.ChatSpamBanMessage, toon, minutes=60)
