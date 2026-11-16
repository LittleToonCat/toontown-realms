import functools
import json
from base64 import b64encode

from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectGlobalUD import DistributedObjectGlobalUD
from direct.distributed.PyDatagram import *
from direct.fsm.FSM import FSM

from toontown.social.SocialGlobals import VisibilityTypes


class GetAvatarInfoOperation(FSM):

    def __init__(self, mgr, senderId, avId, callback):
        FSM.__init__(self, 'GetAvatarInfoOperation')
        self.mgr = mgr
        self.senderId = senderId
        self.avId = avId
        self.callback = callback
        self.isPet = False

    def start(self):
        self.demand('GetAvatarInfo')

    def enterGetAvatarInfo(self):
        self.mgr.air.dbInterface.queryObject(self.mgr.air.dbId, self.avId, self.__gotAvatarInfo)

    def __gotAvatarInfo(self, dclass, fields):
        if dclass not in (
                self.mgr.air.dclassesByName['DistributedToonUD'], self.mgr.air.dclassesByName['DistributedPetAI']):
            self.demand('Failure', 'Invalid dclass for avId %d' % self.avId)
            return

        self.isPet = dclass == self.mgr.air.dclassesByName['DistributedPetAI']
        self.fields = fields
        self.fields['avId'] = self.avId
        self.demand('Finished')

    def enterFinished(self):
        if not self.isPet:
            self.mgr.avBasicInfoCache[self.avId] = [self.avId,
                                                    self.fields['setName'][0],
                                                    self.fields['setDNAString'][0],
                                                    self.fields['setPetId'][0],
                                                    self.fields['setHat'],
                                                    self.fields['setGlasses'],
                                                    self.fields['setBackpack'],
                                                    self.fields['setShoes'],
                                                    self.fields.get('setProfileBackground', [0])[0],
                                                    self.fields.get('setProfilePose', [0])[0],
                                                    VisibilityTypes.INVISIBLE]

        self.callback(success=True, avId=self.senderId, fields=self.fields, isPet=self.isPet)

    def enterFailure(self, reason):
        self.mgr.notify.warning(reason)
        self.callback(success=False, avId=None, fields=None, isPet=False)


class GetOfflineFriendsOperation(FSM):

    def __init__(self, mgr, avId, callback):
        FSM.__init__(self, 'GetOfflineFriendsOperation')
        self.mgr = mgr
        self.avId = avId
        self.callback = callback
        self.friendsDetails = []
        self.iterated = 0
        self.operations = {}

    def start(self):
        self.demand('GetFriendsList')

    def enterGetFriendsList(self):
        self.mgr.air.dbInterface.queryObject(self.mgr.air.dbId, self.avId, self.__gotFriendsList)

    def __gotFriendsList(self, dclass, fields):
        if self.state != 'GetFriendsList':
            self.demand('Failure', '__gotFriendsList called when looking for friends list, avId %d' % self.avId)
            return

        if dclass != self.mgr.air.dclassesByName['DistributedToonUD']:
            self.demand('Failure', 'Invalid dclass for avId %d' % self.avId)
            return

        self.friendsList = fields['setFriendsList'][0]
        self.demand('GetOfflineFriendDetails')

    def enterGetOfflineFriendDetails(self):
        if len(self.friendsList) <= 0:
            self.callback(success=False, avId=self.avId, friendsDetails=None)
            return

        for friendId, trueFriend in self.friendsList:
            if friendId in self.mgr.onlineAvatars:
                self.iterated += 1
                self.__testFinished()
                continue
            details = self.mgr.avBasicInfoCache.get(friendId)
            if details:
                self.friendsDetails.append(details)
                self.iterated += 1
                self.__testFinished()
                continue

            newOperation = GetAvatarInfoOperation(self.mgr, self.avId, friendId, self.__gotAvatarInfo)
            newOperation.start()
            self.operations[friendId] = newOperation

    def __gotAvatarInfo(self, success, avId, fields, isPet):
        if fields['avId'] in self.operations:
            del self.operations[fields['avId']]

        if not success:
            self.demand('Failure', '__gotAvatarInfo received unsuccessful callback, avId=%d' % self.avId)
            return

        if self.state != 'GetOfflineFriendDetails':
            self.demand('Failure', '__gotAvatarInfo while not looking for friends details, avId=%d' % self.avId)
            return

        if avId != self.avId:
            self.demand('Failure',
                        '__gotAvatarInfo response for wrong requester. wrongId=%d, rightId=%d' % (self.avId, avId))
            return

        self.iterated += 1
        self.friendsDetails.append(
            [fields['avId'],
             fields['setName'][0],
             fields['setDNAString'][0],
             fields['setPetId'][0],
             fields['setHat'],
             fields['setGlasses'],
             fields['setBackpack'],
             fields['setShoes'],
             fields.get('setProfileBackground', [0])[0],
             fields.get('setProfilePose', [0])[0],
             VisibilityTypes.INVISIBLE
             ])
        self.__testFinished()

    def __testFinished(self):
        if self.iterated >= len(self.friendsList) and len(self.operations) == 0:
            self.demand('Finished')

    def enterFinished(self):
        self.callback(success=True, avId=self.avId, friendsDetails=self.friendsDetails)

    def enterFailure(self, reason):
        self.mgr.notify.warning(reason)
        self.callback(success=False, avId=self.avId, friendsDetails=None)


class UpdateAvatarFieldOperation(FSM):

    def __init__(self, mgr, senderId, avId, callback):
        FSM.__init__(self, 'UpdateAvatarFieldOperation')
        self.mgr = mgr
        self.senderId = senderId
        self.avId = avId
        self.callback = callback
        self.field = None
        self.value = None

    def start(self, field, value):
        self.field = field
        self.value = value
        self.demand('GetAvatarOnline')

    def enterGetAvatarOnline(self):
        self.mgr.air.getActivated(self.avId, self.__avatarOnlineResp)

    def __avatarOnlineResp(self, avId, activated):
        if self.state != 'GetAvatarOnline':
            self.demand('Failure', 'Received __avatarOnlineResp while not in GetAvatarOnline state.')
            return

        self.online = activated
        self.demand('UpdateAvatarField')

    def enterUpdateAvatarField(self):
        if self.online:
            dg = self.mgr.air.dclassesByName['DistributedToonUD'].aiFormatUpdate(self.field, self.avId, self.avId,
                                                                                 self.mgr.air.ourChannel, [self.value])
            self.mgr.air.send(dg)
        else:
            self.mgr.air.dbInterface.updateObject(self.mgr.air.dbId, self.avId,
                                                  self.mgr.air.dclassesByName['DistributedToonUD'],
                                                  {self.field: [self.value]})

        self.demand('Finished')

    def enterFinished(self):
        self.callback(success=True, avId=self.senderId, online=self.online)

    def enterFailure(self, reason):
        self.mgr.notify.warning(reason)
        self.callback(success=False)


class TTRMSocialManagerUD(DistributedObjectGlobalUD):
    notify = DirectNotifyGlobal.directNotify.newCategory('TTRMSocialManagerUD')

    def __init__(self, air):
        DistributedObjectGlobalUD.__init__(self, air)
        self.operations = {}
        self.avBasicInfoCache = {}
        self.onlineAvatars = []

    def addOnlineAvatar(self, avId):
        if avId in self.avBasicInfoCache:
            del self.avBasicInfoCache[avId]

        self.onlineAvatars.append(avId)

    def removeOnlineAvatar(self, avId):
        if avId in self.onlineAvatars:
            self.onlineAvatars.remove(avId)

    def deleteOperation(self, avId):
        operation = self.operations.get(avId)
        if not operation:
            self.notify.debug('%s tried to delete non-existent operation!' % avId)
            return

        if operation.state != 'Off':
            operation.demand('Off')

        del self.operations[avId]

    def requestOfflineFriends(self):
        avId = self.air.getAvatarIdFromSender()
        if not avId:
            return

        if avId in self.operations:
            return

        newOperation = GetOfflineFriendsOperation(self, avId, self.__gotOfflineFriends)
        newOperation.start()
        self.operations[avId] = newOperation

    def __gotOfflineFriends(self, success, avId, friendsDetails):
        self.deleteOperation(avId)
        if not success:
            return

        self.sendUpdateToAvatarId(avId, 'offlineFriendsResp', [friendsDetails])

    def getAvatarDetails(self, avId):
        senderId = self.air.getAvatarIdFromSender()
        if not senderId:
            return

        if senderId in self.operations:
            return

        newOperation = GetAvatarInfoOperation(self, senderId, avId, self.__gotAvatarDetails)
        newOperation.start()
        self.operations[senderId] = newOperation

    def __gotAvatarDetails(self, success, avId, fields, isPet):
        self.deleteOperation(avId)
        if not success:
            return

        if isPet:
            details = [
                ['setTraitSeed', fields['setTraitSeed'][0]],
                ['setSafeZone', fields['setSafeZone'][0]],
                ['setLastSeenTimestamp', fields.get('setLastSeenTimestamp', [0])[0]],
                ['setHead', fields['setHead'][0]],
                ['setEars', fields['setEars'][0]],
                ['setNose', fields['setNose'][0]],
                ['setTail', fields['setTail'][0]],
                ['setBodyTexture', fields['setBodyTexture'][0]],
                ['setColor', fields['setColor'][0]],
                ['setColorScale', fields['setColorScale'][0]],
                ['setEyeColor', fields['setEyeColor'][0]],
                ['setGender', fields['setGender'][0]],
                ['setOwnerId', fields['setOwnerId'][0]],
                ['setPetName', fields['setPetName'][0]]
            ]
        else:
            # This is here to handle Toons that have not yet logged in since the addition of these fields
            # Since we can't get anything from their db entry, we default to a specific value.
            setLastZone = fields.get('setLastZone', [0])
            setLaffMeterTextColor = fields.get('setLaffMeterTextColor', [0, 0, 0])
            profileBackground = fields.get('setProfileBackground', [0])
            profilePose = fields.get('setProfilePose', [0])

            details = [
                ['setName', fields['setName'][0]],
                ['setExperience', b64encode(fields['setExperience'][0]).decode()],
                ['setTrackAccess', fields['setTrackAccess'][0]],
                ['setTrackBonusLevel', fields['setTrackBonusLevel'][0]],
                ['setInventory', b64encode(fields['setInventory'][0]).decode()],
                ['setHp', fields['setHp'][0]],
                ['setMaxHp', fields['setMaxHp'][0]],
                ['setLaffMeterTextColor', setLaffMeterTextColor[0], setLaffMeterTextColor[1], setLaffMeterTextColor[2]],
                ['setDefaultShard', fields['setDefaultShard'][0]],
                ['setLastHood', fields['setLastHood'][0]],
                ['setLastZone', setLastZone[0]],
                ['setDNAString', b64encode(fields['setDNAString'][0]).decode()],
                ['setMailboxContents', b64encode(fields['setMailboxContents'][0]).decode()],
                ['setAwardMailboxContents', b64encode(fields['setAwardMailboxContents'][0]).decode()],
                ['setGiftSchedule', b64encode(fields['setGiftSchedule'][0]).decode()],
                ['setDeliverySchedule', b64encode(fields['setDeliverySchedule'][0]).decode()],
                ['setAwardSchedule', fields['setAwardSchedule'][0].decode()],
                ['setHat', fields['setHat'][0], fields['setHat'][1], fields['setHat'][2]],
                ['setGlasses', fields['setGlasses'][0], fields['setGlasses'][1], fields['setGlasses'][2]],
                ['setBackpack', fields['setBackpack'][0], fields['setBackpack'][1], fields['setBackpack'][2]],
                ['setShoes', fields['setShoes'][0], fields['setShoes'][1], fields['setShoes'][2]],
                ['setHatList', fields['setHatList'][0]],
                ['setGlassesList', fields['setGlassesList'][0]],
                ['setBackpackList', fields['setBackpackList'][0]],
                ['setShoesList', fields['setShoesList'][0]],
                ['setProfileBackground', profileBackground[0]],
                ['setProfilePose', profilePose[0]],
                ['setCustomMessages', fields['setCustomMessages'][0]],
                ['setEmoteAccess', fields['setEmoteAccess'][0]],
                ['setClothesTopsList', fields['setClothesTopsList'][0]],
                ['setClothesBottomsList', fields['setClothesBottomsList'][0]],
                ['setPetTrickPhrases', fields['setPetTrickPhrases'][0]]
            ]

        self.sendUpdateToAvatarId(avId, 'avatarDetailsResp', [fields['avId'], json.dumps(details)])

    def clearList(self, avId):
        newOperation = GetAvatarInfoOperation(self, avId, avId, self.__handleClearListGotFriendsList)
        newOperation.start()
        self.operations[avId] = newOperation

    def __handleClearListGotFriendsList(self, success, avId, fields, isPet):
        if not success:
            return

        if avId != fields['avId']:
            return

        friendIds = fields['setFriendsList'][0][:]
        friendIds.append((avId, 1))
        if friendIds[0][0] == avId:
            return

        newOperation = GetAvatarInfoOperation(self, avId, friendIds[0][0],
                                              functools.partial(self.__handleClearListGotFriendData,
                                                                friendIds=friendIds[1:]))
        newOperation.start()
        self.operations[avId] = newOperation

    def __handleClearListGotFriendData(self, success, avId, fields, isPet, friendIds=[]):
        self.deleteOperation(avId)
        if not success:
            if friendIds:
                newOperation = GetAvatarInfoOperation(self, avId, friendIds[0][0],
                                                      functools.partial(self.__handleClearListGotFriendData,
                                                                        friendIds=friendIds[1:]))
                newOperation.start()
                self.operations[avId] = newOperation
            else:
                return

        friendsIds = fields['setFriendsList'][0][:]
        if avId == fields['avId']:
            friendsIds = []
        else:
            for friend in friendsIds:
                if friend[0] == avId:
                    friendsIds.remove(friend)

        newOperation = UpdateAvatarFieldOperation(self, avId, fields['avId'],
                                                  functools.partial(self.__handleClearListUpdatedAvatarField,
                                                                    friendId=fields['avId'], friendIds=friendIds[1:]))
        newOperation.start('setFriendsList', friendsIds)
        self.operations[avId] = newOperation

    def __handleClearListUpdatedAvatarField(self, success, avId, online=False, friendId=None, friendIds=[]):
        self.deleteOperation(avId)
        if success and online:
            self.sendUpdateToAvatarId(friendId, 'friendWasRemoved', [avId, 1])

        if not friendIds:
            return

        newOperation = GetAvatarInfoOperation(self, avId, friendIds[0][0],
                                              functools.partial(self.__handleClearListGotFriendData,
                                                                friendIds=friendIds[1:]))
        newOperation.start()
        self.operations[avId] = newOperation
