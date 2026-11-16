from direct.showbase import GarbageReport
from otp.ai.AIBaseGlobal import *
from otp.avatar import DistributedAvatarAI
from otp.avatar import PlayerBase
from otp.distributed.ClsendTracker import ClsendTracker
from otp.otpbase import OTPGlobals
from panda3d.toontown import WhisperPopup

class DistributedPlayerAI(DistributedAvatarAI.DistributedAvatarAI, PlayerBase.PlayerBase, ClsendTracker):

    def __init__(self, air):
        DistributedAvatarAI.DistributedAvatarAI.__init__(self, air)
        PlayerBase.PlayerBase.__init__(self)
        ClsendTracker.__init__(self)
        self.friendsList = []
        self.teleportGreeting = 0 
        self.DISLname = ''
        self.DISLid = 0
        self.accessLevel = 0

    if __dev__:

        def generate(self):
            self._sentExitServerEvent = False
            DistributedAvatarAI.DistributedAvatarAI.generate(self)

    def announceGenerate(self):
        DistributedAvatarAI.DistributedAvatarAI.announceGenerate(self)
        ClsendTracker.announceGenerate(self)
        self._doPlayerEnter()

    def _announceArrival(self):
        self.sendUpdate('arrivedOnDistrict', [self.air.districtId])

    def _announceExit(self):
        self.sendUpdate('arrivedOnDistrict', [0])

    def _sendExitServerEvent(self):
        self.air.writeServerEvent('avatarExit', self.doId, '')
        if __dev__:
            self._sentExitServerEvent = True

    def delete(self):
        if __dev__:
            del self._sentExitServerEvent
        self._doPlayerExit()
        ClsendTracker.destroy(self)
        if __dev__:
            GarbageReport.checkForGarbageLeaks()
        DistributedAvatarAI.DistributedAvatarAI.delete(self)

    def isPlayerControlled(self):
        return True

    def setLocation(self, parentId, zoneId):
        DistributedAvatarAI.DistributedAvatarAI.setLocation(self, parentId, zoneId)
        if self.isPlayerControlled():
            if not self.air._isValidPlayerLocation(parentId, zoneId):
                self.notify.info('booting player %s for doing setLocation to (%s, %s)' % (self.doId, parentId, zoneId))
                self.air.writeServerEvent('suspicious', self.doId, 'invalid setLocation: (%s, %s)' % (parentId, zoneId))
                self.requestDelete()

    def _doPlayerEnter(self):
        self._announceArrival()

    def _doPlayerExit(self):
        self._announceExit()

    def b_setChat(self, chatString, chatFlags):
        self.setChat(chatString, chatFlags)
        self.d_setChat(chatString, chatFlags)

    def d_setChat(self, chatString, chatFlags):
        self.sendUpdate('setChat', [chatString, chatFlags])

    def setChat(self, chatString, chatFlags):
        pass

    def d_setMaxHp(self, maxHp):
        DistributedAvatarAI.DistributedAvatarAI.d_setMaxHp(self, maxHp)
        self.air.writeServerEvent('setMaxHp', self.doId, '%s' % maxHp)

    def b_setTeleportGreeting(self, teleportGreeting):
        self.setTeleportGreeting(teleportGreeting)
        self.d_setTeleportGreeting(teleportGreeting)

    def d_setTeleportGreeting(self, teleportGreeting):
        self.sendUpdate('setTeleportGreeting', [teleportGreeting])

    def setTeleportGreeting(self, teleportGreeting):
        self.teleportGreeting = teleportGreeting

    def getTeleportGreeting(self):
        return self.teleportGreeting

    def d_setSystemMessage(self, aboutId, chatString, whisperType = WhisperPopup.WTSystem):
        self.sendUpdate('setSystemMessage', [aboutId, chatString, whisperType])

    def d_setCommonChatFlags(self, flags):
        self.sendUpdate('setCommonChatFlags', [flags])

    def setCommonChatFlags(self, flags):
        pass

    def setAccountName(self, accountName):
        self.accountName = accountName

    def getAccountName(self):
        return self.accountName

    def setDISLid(self, id):
        self.DISLid = id

    def d_setFriendsList(self, friendsList):
        self.sendUpdate('setFriendsList', [friendsList])

    def setFriendsList(self, friendsList):
        self.friendsList = friendsList
        self.notify.debug('setting friends list to %s' % self.friendsList)

    def getFriendsList(self):
        return self.friendsList

    def setAccessLevel(self, accessLevel):
        # TODO: Disallow access level being set to staff levels when website API is finished
        self.accessLevel = accessLevel

    def getAccessLevel(self):
        # TODO: Disallow access level being set to staff levels when website API is finished
        return self.accessLevel

    def extendFriendsList(self, friendId, friendCode):
        for i in range(len(self.friendsList)):
            friendPair = self.friendsList[i]
            if friendPair[0] == friendId:
                self.friendsList[i] = (friendId, friendCode)
                return

        self.friendsList.append((friendId, friendCode))

    def partyCheck(self, avId, partyId):
        # exploit the ever-loving shit out of partyManager.toonHasEnteredParty...() stuff for teleports
        if self.air.doId2do.get(avId) is not None:
            self.air.partyManager.toonHasEnteredPartyAiToUd(avId, partyId, self.doId)

    def setParty(self, avId, partyInfoTuple):
        # pretend to be a gate in terms of function usage, but have different logic
        if partyInfoTuple[0] == 0:
            self.sendUpdate('partyResponse', [avId, 0])
        else:
            self.sendUpdate('partyResponse', [avId, 1])
