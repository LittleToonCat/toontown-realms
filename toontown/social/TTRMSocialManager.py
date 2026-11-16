import json
from base64 import b64decode

from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectGlobal import DistributedObjectGlobal

from toontown.toon import ToonHead
from toontown.toonbase import TTLocalizer

from toontown.social.SocialGlobals import FriendRequestResponses

import functools

class TTRMSocialManager(DistributedObjectGlobal):
    notify = DirectNotifyGlobal.directNotify.newCategory('TTRMSocialManager')

    def __init__(self, cr):
        DistributedObjectGlobal.__init__(self, cr)
        self.cooldownAvIds = {}

    def receiveFriendRequestCooldowns(self, cooldownAvIds):
        for i in range(len(cooldownAvIds)):
            avId = cooldownAvIds[i][0]
            reason = cooldownAvIds[i][1]
            self.cooldownAvIds[avId] = reason

    def getAvIdCooldown(self, avId):
        if avId in self.cooldownAvIds:
            return self.cooldownAvIds[avId]
        return None

    def receiveFriendRequestCooldown(self, cooldownData, add):
        avId = cooldownData[0]
        reason = cooldownData[1]
        if add:
            self.cooldownAvIds[avId] = reason
        else:
            if avId in self.cooldownAvIds:
                del self.cooldownAvIds[avId]

        messenger.send(f'friend-request-cooldown-{avId}', [reason, add])

    def d_getAvatarDetails(self, avId):
        self.sendUpdate('getAvatarDetails', [avId])

    def avatarDetailsResp(self, avId, details):
        fields = json.loads(details)
        for currentField in fields:
            if currentField[0] in (
                    'setExperience', 'setInventory', 'setDNAString', 'setMailboxContents',
                    'setAwardMailboxContents', 'setGiftSchedule', 'setDeliverySchedule',
                    'setAwardSchedule'):
                currentField[1] = b64decode(currentField[1])

        base.cr.handleGetAvatarDetailsResp(avId, fields=fields)

    def d_requestOfflineFriends(self):
        self.sendUpdate('requestOfflineFriends')

    def offlineFriendsResp(self, resp):
        base.cr.handleGetOfflineFriends(resp)

    def d_sendFriendRequest(self, receiverId):
        self.sendUpdate('sendFriendRequest', [receiverId])

    def receiveFriendRequestResponse(self, response: int, receiverId: int):
        handle = base.cr.identifyAvatar(receiverId)
        if not handle:
            return

        id = "friend_request-{}".format(receiverId)

        if response == FriendRequestResponses.SUCCESS:
            title = TTLocalizer.NotificationTitleFriendAdded
            body = TTLocalizer.NotificationBodyFriendAdded.format(handle.getName())
            messenger.send(f'friend-request-success-{receiverId}')
        elif response == FriendRequestResponses.SUCCESS_RECEIVER:
            title = TTLocalizer.NotificationTitleFriendAdded
            body = TTLocalizer.NotificationBodyFriendAddedReceiver.format(handle.getName())
            messenger.send(f'friend-request-success-{receiverId}')
        elif response == FriendRequestResponses.REJECT:
            # TODO: make it visually clear on profile panel, that we can't add bc of a recent reject
            title = TTLocalizer.NotificationTitleFriendRejected
            body = TTLocalizer.NotificationBodyFriendRequestResponseRejected.format(handle.getName())
        elif response == FriendRequestResponses.LOGGED_OUT:
            title = TTLocalizer.NotificationTitleFriendFailed
            body = TTLocalizer.NotificationBodyFriendRequestResponseLoggedOut.format(handle.getName())
        elif response == FriendRequestResponses.FAILURE_TUTORIAL:
            title = TTLocalizer.NotificationTitleFriendFailed
            body = TTLocalizer.NotificationBodyFriendRequestResponseFailTutorial.format(handle.getName())
        elif response == FriendRequestResponses.FAILURE_IGNORE:
            title = TTLocalizer.NotificationTitleFriendFailed
            body = TTLocalizer.NotificationBodyFriendRequestResponseFailIgnore.format(handle.getName())
        elif response == FriendRequestResponses.FAILURE_NOT_ACCEPTING:
            title = TTLocalizer.NotificationTitleFriendFailed
            body = TTLocalizer.NotificationBodyFriendRequestResponseFailNotAccepting.format(handle.getName())
        else:
            title = TTLocalizer.NotificationTitleFriendFailed
            body = TTLocalizer.NotificationBodyFriendRequestResponseFail.format(handle.getName())

        icon = ToonHead.ToonHead()
        icon.setupHead(handle.getStyle(), forGui = 1)
        icon.generateHat(*handle.getHat())
        icon.generateGlasses(*handle.getGlasses())
        icon.setH(180.0)
        base.localAvatar.sendNotification(
            title = title,
            body = body,
            icon = icon,
            id = id,
            allowDuplicateIds = False
        )

    def d_sendFriendRequestResponse(self, response: int, requesterId: int):
        self.sendUpdate('sendFriendRequestResponse', [response, requesterId])

    def receiveFriendRequest(self, requesterId: int):
        if not hasattr(base, 'localAvatar'):
            self.d_sendFriendRequestResponse(FriendRequestResponses.FAILURE, requesterId)
            return
        elif hasattr(base.cr, 'tutorialManager') and base.cr.tutorialManager.getActive():
            self.d_sendFriendRequestResponse(FriendRequestResponses.FAILURE_TUTORIAL, requesterId)
            return
        elif base.cr.avatarFriendsManager.checkIgnored(requesterId):
            self.d_sendFriendRequestResponse(FriendRequestResponses.FAILURE_IGNORE, requesterId)
            return
        elif not base.localAvatar.acceptingNewFriends:
            self.d_sendFriendRequestResponse(FriendRequestResponses.FAILURE_NOT_ACCEPTING, requesterId)
            return

        handle = base.cr.identifyAvatar(requesterId)
        if not handle:
            return

        icon = ToonHead.ToonHead()
        icon.setupHead(handle.getStyle(), forGui = 1)
        icon.generateHat(*handle.getHat())
        icon.generateGlasses(*handle.getGlasses())
        icon.setH(180.0)
        # TODO: uhhh is there any case where this would break
        # maybe we need a queue if we receive this before notifications is loaded or just send a rejection notification to the requesterId
        base.localAvatar.sendNotification(
            title = TTLocalizer.NotificationTitleFriendRequest,
            body = TTLocalizer.NotificationBodyFriendRequest.format(handle.getName()),
            icon = icon,
            id = "friend_request-{}".format(requesterId),
            subId = "friend_request_add",
            allowDuplicateIds = False,
            dismissButton2Text = TTLocalizer.NotificationReject,
            dismissButton2Action = functools.partial(self.d_sendFriendRequestResponse, FriendRequestResponses.REJECT, requesterId),
            button2Text = TTLocalizer.NotificationAccept,
            button2Action = functools.partial(self.d_sendFriendRequestResponse, FriendRequestResponses.SUCCESS, requesterId)
        )

    def d_handleIgnore(self, avId):
        self.sendUpdate('handleIgnore', [avId])

    def d_removeFriend(self, friendId):
        self.sendUpdate('removeFriend', [friendId])

    def friendWasRemoved(self, avId, wantIval):
        messenger.send(f'friend-removed-{avId}', [wantIval])