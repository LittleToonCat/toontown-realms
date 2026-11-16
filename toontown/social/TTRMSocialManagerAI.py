from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectGlobalAI import DistributedObjectGlobalAI

from toontown.social.SocialGlobals import FriendRequestResponses, CooldownReasons
from toontown.toon.DistributedToonAI import DistributedToonAI
from toontown.toonbase import ToontownGlobals

from typing import List, Dict, Tuple

class TTRMSocialManagerAI(DistributedObjectGlobalAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('TTRMSocialManagerAI')
    FRIEND_REQUEST_COOLDOWN = 300 # 5 mins

    def __init__(self, air):
        DistributedObjectGlobalAI.__init__(self, air)
        self.avId2Cooldowns: Dict[int, List[Tuple[int, int]]] = {}
        self.nonInteractedFriendRequests: Dict[int, List[int]] = {}

    def announceGenerate(self):
        DistributedObjectGlobalAI.announceGenerate(self)

        self.accept('avatarEntered', self.handleAvatarLoggedIn)
        self.accept('avatarExited', self.handleAvatarLoggedOut)

    def delete(self):
        self.ignoreAll()
        self.removeAllTasks()
        del self.avId2Cooldowns

        DistributedObjectGlobalAI.delete(self)

    def handleAvatarLoggedIn(self, avatar: DistributedToonAI):
        avId = avatar.doId
        if avId in self.avId2Cooldowns:
            self.sendUpdateToAvatarId(
                    avId,
                    'receiveFriendRequestCooldowns', 
                    [list(self.avId2Cooldowns[avId].items())]
            )

    def handleAvatarLoggedOut(self, avatar: DistributedToonAI):
        avId = avatar.doId
        # We have not interacted with this friend request, so remove any cooldowns that the requester has on us.
        if avId in self.nonInteractedFriendRequests:
            for requesterId in self.nonInteractedFriendRequests[avId]:
                self.sendUpdateToAvatarId(requesterId, 'receiveFriendRequestResponse', [FriendRequestResponses.LOGGED_OUT, avId])
                self.removeFriendRequestCooldown(requesterId, avId)
                self.removeRequesterFromNonInteractedRequests(avId, requesterId)

    def removeFriendRequestCooldown(self, requesterId: int, receiverId: int):
        taskName = f'friendRequestCooldown-{requesterId}-{receiverId}'
        self.removeTask(taskName)

        if requesterId in self.avId2Cooldowns:
            if receiverId in self.avId2Cooldowns[requesterId]:
                del self.avId2Cooldowns[requesterId][receiverId]
            if not self.avId2Cooldowns[requesterId]:
                del self.avId2Cooldowns[requesterId]

        self.sendUpdateToAvatarId(requesterId, 'receiveFriendRequestCooldown', [(receiverId, CooldownReasons.NONE), 0])

    def startFriendRequestCooldownTask(self, requesterId: int, receiverId: int):
        """
        Receiver dismissed or rejected the requesters friend request.
        Therefore, we must start a task to keep the cooldown in place until a specific amount of time has passed by.
        """
        taskName = f'friendRequestCooldown-{requesterId}-{receiverId}'
        self.addTask(
                self.removeFriendRequestCooldown,
                taskName,
                delay = self.FRIEND_REQUEST_COOLDOWN,
                extraArgs = [requesterId, receiverId],
                appendTask = False
        )

    def updateFriendRequestCooldown(self, requesterId: int, receiverId: int, reason: int = CooldownReasons.NONE):
        """
        Prevent the requester from friending the receiver until further notice.
        This cooldown is permament until the receiver logs out OR the receiver rejects the friend request,
        and then we initiate a task that lifts the cooldown after a while.
        """
        if requesterId not in self.avId2Cooldowns:
            self.avId2Cooldowns[requesterId] = {}
        self.avId2Cooldowns[requesterId][receiverId] = reason

        self.sendUpdateToAvatarId(requesterId, 'receiveFriendRequestCooldown', [(receiverId, reason), 1])

    def removeRequesterFromNonInteractedRequests(self, receiverId, requesterId):
        if receiverId in self.nonInteractedFriendRequests and requesterId in self.nonInteractedFriendRequests[receiverId]:
            self.nonInteractedFriendRequests[receiverId].remove(requesterId)    
            if not self.nonInteractedFriendRequests[receiverId]:
                del self.nonInteractedFriendRequests[receiverId]            

    def sendFriendRequest(self, receiverId: int):
        requesterId = self.air.getAvatarIdFromSender()
        if not requesterId:
            return
        if receiverId == requesterId:
            return
        receiver = self.air.doId2do.get(receiverId)
        if not receiver:
            return
        if not isinstance(receiver, DistributedToonAI):
            return

        if requesterId in self.avId2Cooldowns and receiverId in self.avId2Cooldowns[requesterId]:
            return

        if requesterId in self.nonInteractedFriendRequests and receiverId in self.nonInteractedFriendRequests[requesterId]:
            self.sendFriendRequestResponse(FriendRequestResponses.SUCCESS, receiverId)
            self.removeFriendRequestCooldown(receiverId, requesterId)
            return

        self.updateFriendRequestCooldown(requesterId, receiverId, CooldownReasons.REQUEST_PENDING)

        if receiverId not in self.nonInteractedFriendRequests:
            self.nonInteractedFriendRequests[receiverId] = []
        self.nonInteractedFriendRequests[receiverId].append(requesterId)

        self.sendUpdateToAvatarId(receiverId, 'receiveFriendRequest', [requesterId])

    def sendFriendRequestResponse(self, response: int, requesterId: int):
        receiverId = self.air.getAvatarIdFromSender()
        receiver = self.air.doId2do.get(receiverId)
        if not receiver:
            return

        if response != FriendRequestResponses.SUCCESS:
            self.sendUpdateToAvatarId(requesterId, 'receiveFriendRequestResponse', [response, receiverId])
            if response != FriendRequestResponses.FAILURE_TUTORIAL:
                self.updateFriendRequestCooldown(requesterId, receiverId, CooldownReasons.REQUEST_REJECTED)
                self.startFriendRequestCooldownTask(requesterId, receiverId)
            self.removeRequesterFromNonInteractedRequests(receiverId, requesterId)
            return

        receiverFriendsList = receiver.getFriendsList()
        if len(receiverFriendsList) >= ToontownGlobals.MaxFriends:
            # The client should have warned us about this already.
            # Do not bother sending a response.
            return

        requester = self.air.doId2do.get(requesterId)
        if requester:
            if not isinstance(receiver, DistributedToonAI):
                return
            requesterName = requester.getName()
            requesterDna = requester.getDNAString()
            requesterFriendsList = receiver.getFriendsList()

            if len(requesterFriendsList) >= ToontownGlobals.MaxFriends:
                # Our requester has a full list.
                self.sendUpdateToAvatarId(receiverId, 'receiveFriendRequestResponse', [FriendRequestResponses.FAILURE_FRIENDS, requesterId])
                return

            receiver.extendFriendsList(requester.getDoId(), 0)
            requester.extendFriendsList(receiver.getDoId(), 0)

            receiver.d_setFriendsList(receiver.getFriendsList())
            requester.d_setFriendsList(requester.getFriendsList())

            self.sendUpdateToAvatarId(receiverId, 'receiveFriendRequestResponse', [FriendRequestResponses.SUCCESS_RECEIVER, requesterId])
            self.sendUpdateToAvatarId(requesterId, 'receiveFriendRequestResponse', [FriendRequestResponses.SUCCESS, receiverId])

            self.removeFriendRequestCooldown(requesterId, receiverId)
            self.removeRequesterFromNonInteractedRequests(receiverId, requesterId)
            messenger.send(f'friendChange-{requesterId}', [receiverId, 0])
            messenger.send(f'friendChange-{receiverId}', [requesterId, 0])
        else:
            def handleOfflineAvatar(dclass, fields):
                if dclass != self.air.dclassesByName['DistributedToonAI']:
                    return
                newFriendsList = []
                oldFriendsList = fields['setFriendsList'][0]
                if len(oldFriendsList) >= ToontownGlobals.MaxFriends:
                    # Our requester has a full list.
                    self.sendUpdateToAvatarId(receiverId, 'receiveFriendRequestResponse', [FriendRequestResponses.FAILURE_FRIENDS, requesterId])
                    return

                for oldFriend in oldFriendsList:
                    newFriendsList.append(oldFriend)

                newFriendsList.append((receiverId, 1))
                self.air.dbInterface.updateObject(self.air.dbId, requesterId,
                                                  self.air.dclassesByName['DistributedToonAI'],
                                                  {'setFriendsList': [newFriendsList]})
                receiver.extendFriendsList(requesterId, 1)
                receiver.d_setFriendsList(receiver.getFriendsList())
                self.sendUpdateToAvatarId(receiverId, 'receiveFriendRequestResponse', [FriendRequestResponses.SUCCESS_RECEIVER, requesterId])
                self.removeFriendRequestCooldown(requesterId, receiverId)
                self.removeRequesterFromNonInteractedRequests(receiverId, requesterId)
                messenger.send(f'friendChange-{requesterId}', [receiverId, 0])
                messenger.send(f'friendChange-{receiverId}', [requesterId, 0])

            self.air.dbInterface.queryObject(self.air.dbId, requesterId, handleOfflineAvatar,
                                             self.air.dclassesByName['DistributedToonAI'])

    def removeFriend(self, friendId: int):
        avId = self.air.getAvatarIdFromSender()
        if not avId:
            return
        av = self.air.doId2do[avId]

        friend = self.air.doId2do.get(friendId)
        if friend:
            avFriendsList = av.getFriendsList()
            friendFriendsList = friend.getFriendsList()
            inFriendsList = False
            for index, friendTuple in enumerate(friendFriendsList):
                if friendTuple[0] == avId:
                    del friendFriendsList[index]
                    inFriendsList = True
                    break
            for index, friendTuple in enumerate(avFriendsList):
                if friendTuple[0] == friendId:
                    del avFriendsList[index]
                    inFriendsList = True
                    break
            if not inFriendsList:
                return
            friend.d_setFriendsList(friendFriendsList)
            av.d_setFriendsList(avFriendsList)

            # Let us know that deleting this friend was successful.
            self.sendUpdateToAvatarId(avId, 'friendWasRemoved', [friendId, 1])
            # Let them know that we deleted them.
            self.sendUpdateToAvatarId(friendId, 'friendWasRemoved', [avId, 0])
            messenger.send(f'friendChange-{avId}', [friendId, 1])
            messenger.send(f'friendChange-{friendId}', [avId, 1])
        else:
            def handleOfflineAvatar(dclass, fields):
                if dclass != self.air.dclassesByName['DistributedToonAI']:
                    return
                avFriendsList = av.getFriendsList()
                friendFriendsList = fields['setFriendsList'][0]
                inFriendsList = False

                for index, friendTuple in enumerate(friendFriendsList):
                    if friendTuple[0] == avId:
                        del friendFriendsList[index]
                        inFriendsList = True
                        break

                for index, friendTuple in enumerate(avFriendsList):
                    if friendTuple[0] == friendId:
                        del avFriendsList[index]
                        inFriendsList = True
                        break

                if not inFriendsList:
                    return

                self.air.dbInterface.updateObject(self.air.dbId, friendId,
                                                  self.air.dclassesByName['DistributedToonAI'],
                                                  {'setFriendsList': [friendFriendsList]})
                av.d_setFriendsList(avFriendsList)

                # Let us know that deleting this friend was successful.
                self.sendUpdateToAvatarId(avId, 'friendWasRemoved', [avId, 1])
                messenger.send(f'friendChange-{avId}', [friendId, 1])
                messenger.send(f'friendChange-{friendId}', [avId, 1])

            self.air.dbInterface.queryObject(self.air.dbId, friendId, handleOfflineAvatar,
                                             self.air.dclassesByName['DistributedToonAI'])

    def handleIgnore(self, avId: int):
        senderId = self.air.getAvatarIdFromSender()
        if not senderId:
            return
        sender = self.air.doId2do[senderId]

        # We ignored someone who we received a request from.
        # Reject the friend request that we sent.
        # And tell that avatar that the friend request was rejected.
        if senderId in self.nonInteractedFriendRequests and avId in self.nonInteractedFriendRequests[senderId]:
            self.sendUpdateToAvatarId(avId, 'receiveFriendRequestResponse', [FriendRequestResponses.REJECT, senderId])
            sender.d_removeNotificationsMatching("friend_request-{}".format(avId))
            self.startFriendRequestCooldownTask(senderId, avId)
            self.updateFriendRequestCooldown(senderId, avId, CooldownReasons.REQUEST_REJECTED)
            self.removeRequesterFromNonInteractedRequests(avId, senderId)

        av = self.air.doId2do.get(avId)
        if not isinstance(av, DistributedToonAI):
            return
        # We ignored the avatar we sent a request to.
        # Invalidate the friend request that we sent them.
        if avId in self.nonInteractedFriendRequests and senderId in self.nonInteractedFriendRequests[avId]:
            av.d_removeNotificationsMatching("friend_request-{}".format(senderId))
            self.startFriendRequestCooldownTask(senderId, avId)
            self.updateFriendRequestCooldown(senderId, avId, CooldownReasons.REQUEST_REJECTED)
            self.removeRequesterFromNonInteractedRequests(avId, senderId)
