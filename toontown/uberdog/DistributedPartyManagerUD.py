import datetime, json, os
from copy import deepcopy
from math import floor

from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectGlobalUD import DistributedObjectGlobalUD
from panda3d.core import UniqueIdAllocator

from toontown.catalog import CatalogItem, CatalogBeanItem
from toontown.parties import PartyGlobals
from toontown.parties.InviteInfo import InviteInfoBase
from toontown.parties.PartyInfo import PartyInfoAI
from toontown.parties.CalendarBackup import PartyBackup

from toontown.toonbase import ToontownGlobals


class DistributedPartyManagerUD(DistributedObjectGlobalUD):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedPartyManagerUD')
    serverDataFolder = simbase.config.GetString('server-data-folder', '')

    def __init__(self, air):
        DistributedObjectGlobalUD.__init__(self, air)
        self.partyManagers = {} # shardId: partyMgrId
        self.partyIdAllocator = UniqueIdAllocator(10000000, 20000000)
        self.host2party = {} # hostId: [partyId, partyInfo, inviteeIds, inviteKey]
        self.guest2host = {} # avId: hostId
        self.publicParties = {}
        self.partyDoIds = set()
        default = 0
        if __debug__:
            default = 1
        self.wantInstantParties = config.GetBool('want-instant-parties', default)

        self.inviteKeyAllocator = UniqueIdAllocator(1, 65535)
        self.inviteStatusForAvatar = {} # avId: [inviteStruct]
        self.inviteRepliesForParty = {} # partyId: [[inviteeId, status]]
        self.partiesInvitedToAvatar = {} # avId: [partyInfo]
        self.partyBackups = None
        self.backupData = {}    # hostId: [hostId, [startTime data], [endTime data], [inviteeIDs], isPrivate, theme,
                                #          status]

    def announceGenerate(self):
        DistributedObjectGlobalUD.announceGenerate(self)
        self.__startPartiesTask()
        self.partyManagerUdStartingUp()

    def delete(self):
        taskMgr.remove(self.uniqueName('parties-task'))
        DistributedObjectGlobalUD.delete(self)

    def sendUpdateToAV(self, avId, field, args=[]):
        dg = self.air.dclassesByName['DistributedToonUD'].getFieldByName(field).aiFormatUpdate(avId, avId,
                                                                                               simbase.air.ourChannel,
                                                                                               args)
        self.air.send(dg)

    def __startPartiesTask(self):
        now = datetime.datetime.now(tz=self.air.toontownTimeManager.serverTimeZone)
        delay = (60 - now.second) + 60 * (4 - (now.minute % 5))
        taskMgr.doMethodLater(delay, self.__partiesTask, self.uniqueName('parties-task'))

    def __partiesTask(self, task):
        now = datetime.datetime.now(tz=self.air.toontownTimeManager.serverTimeZone)
        for party in list(self.host2party.values()):
            partyInfo = party[1]
            partyId = partyInfo.partyId
            hostId = partyInfo.hostId
            deleted = False
            if self.canStartParty(partyInfo) and partyInfo.status == PartyGlobals.PartyStatus.Pending:
                partyInfo.status = PartyGlobals.PartyStatus.CanStart
                self.sendUpdateToAV(hostId, 'setPartyCanStart', [partyId])
                self.notify.debug("Party CanStart: host data={}, backup data={}".format(party, self.backupData.get(hostId)))
            elif self.isTooLate(partyInfo) and partyInfo.status in (PartyGlobals.PartyStatus.Pending,
                                                                    PartyGlobals.PartyStatus.CanStart):
                partyInfo.status = PartyGlobals.PartyStatus.NeverStarted
                self.notify.debug("Party TooLate: host data={}, backup data={}".format(party, self.backupData.get(hostId)))
                # it's too late to start now, so might as well delete this party

                # Refund if the party was never started; this was actually a behavior in TTO
                # (it was added super late in sv1.0.47.31 on June 27, 2013)
                beansRefunded = PartyGlobals.getCostOfParty(partyInfo) * PartyGlobals.PartyRefundPercentage
                self.__giveRefund(beansRefunded, hostId)

                self.partyHasFinished(hostId, partyId)
                deleted = True

            if not deleted:
                # don't send an update of a 'never started' party to the calendar this way
                # note: nvm, I dunno what I was looking at when I commented the above, but
                # there is still no need to do so, and will likely end up sending unnecessary
                # info anyways
                self.sendUpdateToAV(hostId, 'setPartyStatus', [partyId, partyInfo.status])
            else:
                self.sendUpdateToAV(hostId, 'setPartyTimedOut', [])

        task.delayTime = (60 - now.second) + 60 * (4 - (now.minute % 5))
        return task.again

    def canStartParty(self, partyInfo):
        return self.wantInstantParties or partyInfo.startTime < datetime.datetime.now(
            tz=self.air.toontownTimeManager.serverTimeZone)

    def isTooLate(self, partyInfo):
        now = datetime.datetime.now(tz=self.air.toontownTimeManager.serverTimeZone)
        delta = datetime.timedelta(minutes=PartyGlobals.PartyStartTimeout)
        endStartable = partyInfo.startTime + delta
        return endStartable < now

    def __giveRefund(self, beansRefunded, hostId):
        # CatalogBeanItem expects an int; the default algorithm returns a float
        refundItem = CatalogBeanItem.CatalogBeanItem(int(beansRefunded), ToontownGlobals.GIFT_partyrefund)
        # Set this so it will show the party refund message
        refundItem.giftTag = 0
        refundItemBlob = refundItem.getBlob(store=CatalogItem.Customization)
        simbase.air.deliveryManager.giveGiftItemToAvatar(refundItemBlob, hostId)

    def addParty(self, partyMgrId, hostId, startTime, endTime, isPrivate, inviteTheme, activities, decorations,
                 inviteeIds, cost, startup=False, startDate=None, endDate=None, partyId=None, inviteKey=None):
        if not startup and not startDate and not endDate:
            partyTimeFormat = '%Y-%m-%d %H:%M:%S'
            startDate = datetime.datetime.strptime(startTime, partyTimeFormat)
            endDate = datetime.datetime.strptime(endTime, partyTimeFormat)

        partyArray = self.host2party.setdefault(hostId, [0, None, None, None])

        party = partyArray[1]
        if party and not startup:
            self.sendUpdateToAI(partyMgrId, 'addPartyResponseUdToAi',
                                [hostId, PartyGlobals.AddPartyErrorCode.TooManyHostedParties, 0])
            return

        if not partyId:
            partyId = self.partyIdAllocator.allocate()
        else:
            self.partyIdAllocator.initialReserveId(partyId)
        self.host2party[hostId][PartyGlobals.PartyId] = partyId
        partyInfo = PartyInfoAI(self.host2party[hostId][PartyGlobals.PartyId], hostId, startDate.year, startDate.month,
                                startDate.day, startDate.hour, startDate.minute, endDate.year, endDate.month,
                                endDate.day, endDate.hour, endDate.minute, isPrivate, inviteTheme, activities,
                                decorations, PartyGlobals.PartyStatus.Pending)

        self.host2party[hostId][PartyGlobals.PartyInfo] = partyInfo
        self.host2party[hostId][PartyGlobals.PartyInvitees] = inviteeIds
        if not inviteKey:
            inviteKey = self.inviteKeyAllocator.allocate()
        else:
            self.inviteKeyAllocator.initialReserveId(inviteKey)
        self.host2party[hostId][PartyGlobals.PartyInviteKey] = inviteKey

        filename = self.getFilename(self.host2party[hostId][PartyGlobals.PartyId])
        partyData = {self.host2party[hostId][PartyGlobals.PartyId]: [(hostId, startDate.year, startDate.month,
                                                                     startDate.day, startDate.hour, startDate.minute,
                                                                     endDate.year, endDate.month, endDate.day,
                                                                     endDate.hour, endDate.minute, isPrivate,
                                                                     inviteTheme, activities, decorations,
                                                                     PartyGlobals.PartyStatus.Pending), inviteeIds,
                                                                     self.host2party[hostId][PartyGlobals.PartyInviteKey]]}
        # append to calendar party data in form of following:
        # [hostId, [startTime data], [endTime data], [inviteeIDs], isPrivate, theme, status]
        self.backupData[hostId] = [hostId,
                                   [startDate.year, startDate.month, startDate.day, startDate.hour, startDate.minute],
                                   [endDate.year, endDate.month, endDate.day, endDate.hour, endDate.minute],
                                   deepcopy(inviteeIds),
                                   isPrivate,
                                   inviteTheme,
                                   PartyGlobals.PartyStatus.NeverStarted]
        self.updateParties(filename, partyData)

        if not startup:
            self.sendUpdateToAV(hostId, 'setHostedParties', [[partyInfo]])

        if inviteeIds:
            self.inviteGuestsForParty(partyInfo, inviteeIds, self.host2party[hostId][3])

        if not startup:
            self.sendUpdateToAI(partyMgrId, 'addPartyResponseUdToAi',
                                [hostId, PartyGlobals.AddPartyErrorCode.AllOk, cost])

        if self.wantInstantParties:
            taskMgr.remove(self.uniqueName('parties-task'))
            taskMgr.doMethodLater(15, self.__partiesTask, self.uniqueName('parties-task'))

    def inviteGuestsForParty(self, partyInfo, inviteeIds, inviteKey):
        inviteInfo = InviteInfoBase(inviteKey, partyInfo.partyId, PartyGlobals.InviteStatus.NotRead)

        # Setup initial reply info for host:
        replies = []
        for inviteeId in inviteeIds:
            partyReply = [inviteeId, inviteInfo.status]
            replies.append(partyReply)

        self.inviteRepliesForParty[inviteInfo.partyId] = replies
        # Now we send this to the host.
        repliesForOnePartyStruct = [[inviteInfo.partyId, replies]]
        self.sendUpdateToAV(partyInfo.hostId, 'setPartyReplies', [repliesForOnePartyStruct])

        def __gotInviteeActivated(inviteeId, activated):
            if inviteeId not in inviteeIds:
                self.notify.warning('Got fields from unknown invitee id {}'.format(inviteeId))
                return

            if activated:
                self.air.getFieldsFromActiveObject(inviteeId, self.air.dclassesByName['DistributedToonUD'],
                                                   ['setInvites', 'setPartiesInvitedTo'], __gotInviteeFields)

        def __gotInviteeFields(inviteeId, success, fields):
            if inviteeId not in inviteeIds:
                self.notify.warning('Got fields from unknown invitee id {}'.format(inviteeId))
                return

            invites = fields.get('setInvites', [[]])[0]
            partiesInvited = fields.get('setPartiesInvitedTo', [[]])[0]

            if inviteInfo not in invites:
                invites.append(inviteInfo)
                self.sendUpdateToAV(inviteeId, 'setInvites', [invites])

            if partyInfo not in partiesInvited:
                partiesInvited.append(partyInfo)
                self.sendUpdateToAV(inviteeId, 'setPartiesInvitedTo', [partiesInvited])

        for inviteeId in inviteeIds:
            self.inviteStatusForAvatar.setdefault(inviteeId, []).append(inviteInfo)
            self.partiesInvitedToAvatar.setdefault(inviteeId, []).append(partyInfo)
            self.air.getActivated(inviteeId, __gotInviteeActivated)

    def updatePartyStatusForAvatar(self, avId):
        # Called by GameServicesManagerUD to get party info for the newly
        # activated Avatar.
        party = self.host2party.get(avId)
        if party:
            partyInfo = party[1]

            self.sendUpdateToAV(avId, 'setHostedParties', [[partyInfo]])
            if partyInfo.status == PartyGlobals.PartyStatus.CanStart:
                self.sendUpdateToAV(avId, 'setPartyCanStart', [partyInfo.partyId])

            if partyInfo.partyId in self.inviteRepliesForParty:
                replies = self.inviteRepliesForParty[partyInfo.partyId]
                repliesForOnePartyStruct = [[partyInfo.partyId, replies]]
                self.sendUpdateToAV(avId, 'setPartyReplies', [repliesForOnePartyStruct])

        if avId in self.inviteStatusForAvatar:
            invites = []
            for invite in self.inviteStatusForAvatar[avId]:
                invites.append(invite)
            self.sendUpdateToAV(avId, 'setInvites', [invites])

        if avId in self.partiesInvitedToAvatar:
            partiesInvited = []
            for partyInfo in self.partiesInvitedToAvatar.get(avId, []):
                partiesInvited.append(partyInfo)
            self.sendUpdateToAV(avId, 'setPartiesInvitedTo', [partiesInvited])

    def markInviteAsReadButNotReplied(self, partyMgrId, avId, inviteKey):
        # Normally, clients are informed that they have mail if they have an invite in their inbox.
        # This function is used to tell the client, "Hey, we know you already checked the invite so we won't bother letting you know about it again."
        # TODO: Add functionality that saves whether an invite was marked as read but not replied
        self.sendUpdateToAI(partyMgrId, 'markInviteAsReadButNotReplied', [avId, inviteKey])

    def respondToInvite(self, partyMgrId, avId, context, inviteKey, response):
        inviteeIds = []
        for partyIndices in list(self.host2party.values()):
            if partyIndices[3] == inviteKey:
                partyId = partyIndices[0]
                hostId = partyIndices[1].hostId
                inviteeIds = partyIndices[2]
                break

        if not inviteeIds:
            return

        if avId not in inviteeIds:
            return

        if partyId in self.inviteRepliesForParty:
            reply = None
            for replies in self.inviteRepliesForParty[partyId]:
                if replies[0] == avId:
                    reply = replies
                    break
            if reply:
                reply[1] = response

                repliesForOnePartyStruct = [[partyId, self.inviteRepliesForParty[partyId]]]
                self.sendUpdateToAV(hostId, 'setPartyReplies', [repliesForOnePartyStruct])

        mailboxResponse = None
        if response == PartyGlobals.InviteStatus.ReadButNotReplied:
            mailboxResponse = ToontownGlobals.P_ItemInMailbox
            self.markInviteAsReadButNotReplied(partyMgrId, avId, inviteKey)
        if response in (PartyGlobals.InviteStatus.Accepted, PartyGlobals.InviteStatus.Rejected):
            mailboxResponse = ToontownGlobals.P_ItemAvailable

        if mailboxResponse:
            self.sendUpdateToAI(partyMgrId, 'respondToInviteResponse',
                                [avId, context, inviteKey, mailboxResponse, response])

    def changePrivateRequest(self, todo0, todo1):
        pass

    def changePrivateRequestAiToUd(self, hostId, partyId, newPrivateStatus):
        party = self.host2party.get(hostId)
        partyInfo = party[1]

        if party is None:
            self.changePrivateResponseUdToAi(hostId, partyId, newPrivateStatus,
                                             PartyGlobals.ChangePartyFieldErrorCode.ValidationError)
            return
        if partyInfo.hostId != hostId:
            self.changePrivateResponseUdToAi(hostId, partyId, newPrivateStatus,
                                             PartyGlobals.ChangePartyFieldErrorCode.ValidationError)
            return
        if partyInfo.status not in (PartyGlobals.PartyStatus.CanStart, PartyGlobals.PartyStatus.Pending):
            self.changePrivateResponseUdToAi(hostId, partyId, newPrivateStatus,
                                             PartyGlobals.ChangePartyFieldErrorCode.AlreadyStarted)
            return

        partyInfo.isPrivate = newPrivateStatus
        self.host2party[hostId] = party

        if partyId in list(self.publicParties.keys()):
            publicPartyInfo = self.publicParties[partyId]
            self.updateToPublicPartyInfoUdToAllAi(hostId, partyId, publicPartyInfo['shardId'],
                                                  publicPartyInfo['zoneId'], publicPartyInfo['numberOfGuests'],
                                                  partyInfo.isPrivate, publicPartyInfo['hostName'],
                                                  partyInfo.getActivityIds(), publicPartyInfo['started'])

        self.sendUpdateToAV(hostId, 'setHostedParties', [[partyInfo]])
        self.changePrivateResponseUdToAi(hostId, partyId, newPrivateStatus,
                                         PartyGlobals.ChangePartyFieldErrorCode.AllOk)

    def changePrivateResponseUdToAi(self, hostId, partyId, newPrivateStatus, errorCode):
        partyDoId = self.air.getMsgSender()
        self.sendUpdateToAI(partyDoId, 'changePrivateResponseUdToAi', [hostId, partyId, newPrivateStatus, errorCode])

    def changePrivateResponse(self, todo0, todo1, todo2):
        pass

    def changePartyStatusRequest(self, todo0, todo1):
        pass

    def changePartyStatusRequestAiToUd(self, hostId, partyId, newPartyStatus):
        party = self.host2party.get(hostId)
        partyInfo = party[1]

        if party is None:
            self.changePrivateResponseUdToAi(hostId, partyId, newPartyStatus,
                                             PartyGlobals.ChangePartyFieldErrorCode.ValidationError)
            return
        if partyInfo.hostId != hostId:
            self.changePrivateResponseUdToAi(hostId, partyId, newPartyStatus,
                                             PartyGlobals.ChangePartyFieldErrorCode.ValidationError)
            return
        if newPartyStatus == PartyGlobals.PartyStatus.Cancelled and \
                partyInfo.status not in (PartyGlobals.PartyStatus.CanStart, PartyGlobals.PartyStatus.Pending):
            self.changePrivateResponseUdToAi(hostId, partyId, newPartyStatus,
                                             PartyGlobals.ChangePartyFieldErrorCode.AlreadyStarted)
            return
        if newPartyStatus == PartyGlobals.PartyStatus.Cancelled and \
                partyInfo.status == PartyGlobals.PartyStatus.NeverStarted:
            self.changePrivateResponseUdToAi(hostId, partyId, PartyGlobals.PartyStatus.NeverStarted,
                                             PartyGlobals.ChangePartyFieldErrorCode.AlreadyRefunded)
            return

        partyInfo.status = newPartyStatus
        self.sendUpdateToAV(hostId, 'setHostedParties', [[partyInfo]])

        if newPartyStatus == PartyGlobals.PartyStatus.Cancelled:
            beansRefunded = PartyGlobals.getCostOfParty(party[1]) * PartyGlobals.PartyRefundPercentage

            self.__giveRefund(beansRefunded, hostId)

            self.changePartyStatusResponseUdToAi(partyId, newPartyStatus, PartyGlobals.ChangePartyFieldErrorCode.AllOk,
                                                 beansRefunded)
        if newPartyStatus in (PartyGlobals.PartyStatus.Cancelled, PartyGlobals.PartyStatus.Finished):
            self.backupData[hostId][6] = newPartyStatus
            self.partyHasFinished(hostId, partyId)

    def changePartyStatusResponseUdToAi(self, partyId, newPartyStatus, errorCode, beansRefunded):
        partyDoId = self.air.getMsgSender()
        self.sendUpdateToAI(partyDoId, 'changePartyStatusResponseUdToAi', [partyId, newPartyStatus, errorCode, beansRefunded])

    def changePartyStatusResponse(self, todo0, todo1, todo2, todo3):
        pass

    def partyInfoOfHostRequestAiToUd(self, partyMgrId, hostId):
        avId = self.air.getAvatarIdFromSender()
        if hostId in self.host2party and hostId not in self.guest2host:
            partyInfo = self.host2party[hostId][1]
            if partyInfo.status == PartyGlobals.PartyStatus.CanStart:
                inviteeIds = self.host2party[hostId][2]
                self.guest2host[hostId] = hostId
                self.sendUpdateToAI(partyMgrId, 'partyInfoOfHostResponseUdToAi', [partyInfo, inviteeIds])
                return

        if hostId in self.guest2host:
            # Get the actual host id.
            hostId = self.guest2host[hostId]

        # TODO: figure out when this isn't true, yet partyInfoOfHostRequestAiToUd() is called
        if hostId and hostId in self.host2party:
            partyId = self.host2party[hostId][1].partyId
            party = self.publicParties[partyId]
            zoneId = party['zoneId']

            self.sendUpdateToAvatarId(avId, 'receivePartyZone', [hostId, partyId, zoneId], fromDoId=partyMgrId)
        else:
            self.notify.warning('partyInfoOfHostRequestAiToUd() - hostId {} not in self.host2party.'.format(hostId))
            # Even though it is very likely the host itself, might as well have the client determine what message
            # to post to the user
            self.sendUpdateToAvatarId(avId, 'receivePartyZone', [hostId, 0, 0], fromDoId=partyMgrId)

    def partyInfoOfHostFailedResponseUdToAi(self, todo0):
        pass

    def givePartyRefundResponse(self, todo0, todo1, todo2, todo3, todo4):
        pass

    def freeZoneIdFromPlannedParty(self, todo0, todo1):
        pass

    def sendAvToPlayground(self, todo0, todo1):
        pass

    def exitParty(self, todo0):
        pass

    def removeGuest(self, todo0, todo1):
        pass

    def partyManagerAIStartingUp(self, doId, shardId):
        self.notify.debug('Got PartyManager AI {} from shard {}.'.format(doId, shardId))
        self.partyManagers[shardId] = doId

        self.updateAllPublicPartyInfoToAi(doId)

    def partyManagerAIGoingDown(self, doId, shardId):
        self.notify.debug('Got PartyManager Shutdown from AI {} from shard {}.'.format(doId, shardId))
        partyId = self.partyManagers.get(shardId)
        if not partyId:
            self.notify.warning('Got goingDown message from unknown shard {}.'.format(shardId))
            return
        if partyId != doId:
            self.notify.warning('Got goingDown message from AI {} but we have {} instead.'.format(doId, partyId))
            return

        del self.partyManagers[shardId]

    def partyHasStartedAiToUd(self, partyId, shardId, zoneId, hostId, hostName):
        self.publicParties[partyId] = {
            'shardId': shardId,
            'zoneId': zoneId,
            'hostId': hostId,
            'numberOfGuests': 1,
            'hostName': hostName,
            'started': int(floor(self.air.time.now()))
        }

        party = self.host2party[hostId]
        partyInfo = party[1]
        self.updateToPublicPartyInfoUdToAllAi(hostId, partyId, shardId, zoneId,
                                              self.publicParties[partyId]['numberOfGuests'], partyInfo.isPrivate,
                                              hostName, partyInfo.getActivityIds(),
                                              self.publicParties[partyId]['started'])
        party[1].status = PartyGlobals.PartyStatus.Started

        # backup 'Started' state in case UD dies, and restarts after party expires, so calendar gets a 'Finished'
        # state, instead of 'Never Started' state.
        s = party[PartyGlobals.PartyInfo].startTime
        e = party[PartyGlobals.PartyInfo].endTime
        p = party[PartyGlobals.PartyInfo]
        i = party[PartyGlobals.PartyInvitees]
        # NOTE: we don't set backup data status until it finishes (we don't care for the 'Started' state in
        # archived data)
        filename = self.getFilename(party[PartyGlobals.PartyId])
        partyData = {party[PartyGlobals.PartyId]: [(hostId,
                                                    s.year, s.month, s.day, s.hour, s.minute,
                                                    e.year, e.month, e.day, e.hour, e.minute,
                                                    p.isPrivate,
                                                    p.inviteTheme,
                                                    [[x.activityId, x.x, x.y, x.h] for x in p.activityList],
                                                    [[x.decorId, x.x, x.y, x.h] for x in p.decors],
                                                    PartyGlobals.PartyStatus.Started),
                                                   deepcopy(i),
                                                   party[PartyGlobals.PartyInviteKey]]}
        self.updateParties(filename, partyData)

        self.sendUpdateToAV(hostId, 'setPartyStatus', [partyId, party[1].status])

        for inviteeId in party[2]:
            self.sendUpdateToAV(inviteeId, 'setPartyStatus', [partyId, party[1].status])


    def toonHasEnteredPartyAiToUd(self, avId, partyId, gateId):
        # TODO: fix potential issue where Toon requests to enter party, guestNo is incremented, but Toon never actually
        # arrives (example: crash before zone change), and number never gets decremented to account for that
        if partyId not in self.publicParties:
            return PartyGlobals.PartyGateDenialReasons.Unavailable

        party = self.publicParties[partyId]
        if avId not in self.guest2host or (self.guest2host[avId] in self.host2party and
                                           self.host2party[self.guest2host[avId]][0] != partyId):
            # do *not* increment count if avId is teleporting to a friend in the same party
            if party['numberOfGuests'] >= PartyGlobals.MaxToonsAtAParty:
                return PartyGlobals.PartyGateDenialReasons.Full

            party['numberOfGuests'] += 1
        shardId = party['shardId']
        zoneId = party['zoneId']
        hostId = party['hostId']
        hostName = party['hostName']
        partyInfo = self.host2party.get(hostId)[1]
        self.updateToPublicPartyInfoUdToAllAi(hostId, partyId, shardId, zoneId, party['numberOfGuests'],
                                              partyInfo.isPrivate, hostName, partyInfo.getActivityIds(),
                                              party['started'])

        partyInfoTuple = [party['shardId'], party['zoneId'], party['numberOfGuests'], party['hostName'],
                          partyInfo.getActivityIds(), 0]

        self.guest2host[avId] = hostId

        self.toonHasEnteredPartyUdToAI(avId, gateId, partyInfoTuple)

    def toonHasEnteredPartyUdToAI(self, avId, gateId, partyInfoTuple):
        if gateId:
            partyDoId = self.air.getMsgSender()
            self.sendUpdateToAI(partyDoId, 'toonHasEnteredPartyUdToAI', [avId, gateId, partyInfoTuple])

    def toonHasExitedPartyAiToUd(self, avId):
        self.notify.debug('toonHasExitedPartyAiToUd: {}'.format(avId))
        hostId = self.guest2host.get(avId, None)
        # make sure avId is in this dict, otherwise we risk a UD crash
        if hostId is not None:
            del self.guest2host[avId]

            if not self.host2party.get(hostId):
                # This party has been deleted (presumbly because it has ended).
                # So, let's not do anything.
                return

            partyId = self.host2party[hostId][1].partyId

            party = self.publicParties[partyId]
            # *sigh* :facepalm:
            # this kind of reminds me of the "lets not give level 7s in battle if inventory is full, despite them not
            # counting against the gag space limitations!" thing...
            # what happens if a Toon exits the party, and the party is full?
            '''if party['numberOfGuests'] >= PartyGlobals.MaxToonsAtAParty:
                return'''
            # oh well, let's fix this so it makes sense...
            if party['numberOfGuests'] < 1:
                return

            party['numberOfGuests'] -= 1
            shardId = party['shardId']
            zoneId = party['zoneId']
            hostId = party['hostId']
            hostName = party['hostName']
            partyInfo = self.host2party.get(hostId)[1]
            self.updateToPublicPartyInfoUdToAllAi(hostId, partyId, shardId, zoneId, party['numberOfGuests'],
                                                  partyInfo.isPrivate, hostName, partyInfo.getActivityIds(),
                                                  party['started'])

    def __removeInvitees(self, partyInfo, inviteeIds, inviteKey):
        def __gotInviteeActivated(inviteeId, activated):
            if inviteeId not in inviteeIds:
                self.notify.warning('Got fields from unknown invitee id {}'.format(inviteeId))
                return

            if activated:
                self.air.getFieldsFromActiveObject(inviteeId, self.air.dclassesByName['DistributedToonUD'],
                                                   ['setInvites', 'setPartiesInvitedTo'], __gotInviteeFields)

        def __gotInviteeFields(inviteeId, success, fields):
            if inviteeId not in inviteeIds:
                self.notify.warning('Got fields from unknown invitee id {}'.format(inviteeId))
                return

            invites = fields.get('setInvites', [[]])[0]
            partiesInvited = fields.get('setPartiesInvitedTo', [[]])[0]

            # note: we do it this way to remove any invite, regardless of invite status
            tmp = []
            for invite in invites:
                # if invite has our inviteKey (should be unique), don't add to list
                if invite[0] == inviteKey:
                    continue
                tmp.append(invite)
            self.sendUpdateToAV(inviteeId, 'setInvites', [tmp])

            # note: this one is just to make sure to get the party, even if the invitee doesn't have the updated
            # partyInfo for some reason
            tmp = []
            for party in partiesInvited:
                if party[0] == partyInfo.partyId and party[1] == partyInfo.hostId:
                    continue
                tmp.append(party)
            self.sendUpdateToAV(inviteeId, 'setPartiesInvitedTo', [tmp])

        for inviteeId in inviteeIds:
            if inviteeId in self.inviteStatusForAvatar:
                tmp = []
                for invite in self.inviteStatusForAvatar[inviteeId]:
                    # note: should be InviteInfoBase, since this is a UD only dict, but just in case
                    if isinstance(invite, InviteInfoBase):
                        if invite.inviteKey == inviteKey:
                            continue
                    else:
                        if invite[0] == inviteKey:
                            continue
                    tmp.append(invite)
                self.inviteStatusForAvatar[inviteeId] = tmp
            if inviteeId in self.partiesInvitedToAvatar:
                tmp = []
                for party in self.partiesInvitedToAvatar[inviteeId]:
                    # note: should be PartyInfoAI, since this is a UD only dict, but just in case
                    if isinstance(party, PartyInfoAI):
                        if party.partyId == partyInfo.partyId and party.hostId == partyInfo.hostId:
                            continue
                    else:
                        if party[0] == partyInfo.partyId and party[1] == partyInfo.hostId:
                            continue
                    tmp.append(party)
                self.partiesInvitedToAvatar[inviteeId] = tmp
            self.air.getActivated(inviteeId, __gotInviteeActivated)
        if partyInfo.partyId in self.inviteRepliesForParty:
            del self.inviteRepliesForParty[partyInfo.partyId]

    def partyHasFinished(self, hostId, partyId):
        if hostId in self.host2party:
            # remove invites from invitees mailboxes and stuff
            self.__removeInvitees(deepcopy(self.host2party[hostId][PartyGlobals.PartyInfo]),
                                  deepcopy(self.host2party[hostId][PartyGlobals.PartyInvitees]),
                                  self.host2party[hostId][PartyGlobals.PartyInviteKey])
            # then delete host2party
            del self.host2party[hostId]
            self.sendUpdateToAV(hostId, 'setHostedParties', [[]])
        if partyId in self.publicParties:
            del self.publicParties[partyId]

        filename = self.getFilename(partyId)
        if os.path.exists(filename):
            # Remove the backup, since we don't need it anymore.
            os.remove(filename)

        if hostId in self.backupData:
            self.notify.debug('backup data = {}'.format(self.backupData[hostId]))
            self.partyBackups.addData(self.backupData[hostId])
            del self.backupData[hostId]
            self.sendUpdateToAllAI('reloadPartyBackups', [])
        else:
            self.notify.warning('Host ID {} party data somehow not in backup dict; cannot archive party!'.format(hostId)
                                )

        self.sendUpdateToAllAI('partyHasFinishedUdToAllAi', [partyId])

    def updateAllPublicPartyInfoToAi(self, partyMgrId):
        for partyId, party in self.publicParties.items():
            partyInfo = self.host2party.get(party['hostId'])[1]

            actIds = partyInfo.getActivityIds()

            self.sendUpdateToAI(partyMgrId, 'updateToPublicPartyInfoUdToAllAi', [party['hostId'], partyId, party['shardId'],
                                                                                 party['zoneId'], party['numberOfGuests'],
                                                                                 partyInfo.isPrivate, party['hostName'],
                                                                                 actIds, party['started']])

    def updateToPublicPartyInfoUdToAllAi(self, hostId, partyId, shardId, zoneId, numberOfGuests, isPrivate, hostName,
                                         activityIds, started):
        self.sendUpdateToAllAI('updateToPublicPartyInfoUdToAllAi', [hostId, partyId, shardId, zoneId, numberOfGuests,
                                                                    isPrivate, hostName, activityIds, started])

    def updateToPublicPartyCountUdToAllAi(self, todo0, todo1):
        pass

    def requestShardIdZoneIdForHostId(self, hostId):
        avId = self.air.getAvatarIdFromSender()
        if hostId not in self.host2party:
            # This party has been deleted (presumbly because it has ended).
            # So, let's not do anything.
            self.sendShardIdZoneIdToAvatar(0, 0)
            return
        partyId = self.host2party[hostId][1].partyId
        party = self.publicParties[partyId]
        shardId = party['shardId']
        zoneId = party['zoneId']
        party['numberOfGuests'] += 1

        self.guest2host[avId] = hostId
        self.updateAllPublicPartyInfoToAi(self.air.getAccountIdFromSender())

        self.sendShardIdZoneIdToAvatar(shardId, zoneId)

    def sendShardIdZoneIdToAvatar(self, shardId, zoneId):
        avId = self.air.getAvatarIdFromSender()
        partyMgrId = self.air.getAccountIdFromSender()
        self.sendUpdateToAvatarId(avId, 'sendShardIdZoneIdToAvatar', [shardId, zoneId], fromDoId=partyMgrId)

    def partyManagerUdStartingUp(self):
        # The UberDog is starting up! Woohoo! Let's load any parties we have saved
        # Iterate over each file in the backups/parties directory
        if not os.path.exists(self.serverDataFolder):
            os.mkdir(self.serverDataFolder)
        if not os.path.exists(self.serverDataFolder + 'parties/'):
            os.mkdir(self.serverDataFolder + 'parties/')
        self.partyBackups = PartyBackup()
        for filename in os.listdir(self.serverDataFolder + 'parties/'):
            # Load the party data
            data = self.loadParties(self.serverDataFolder + 'parties/' + filename)
            # Retrieve the list chocked full of data: partyInfo, inviteeIds, and inviteKey
            key = None
            partyData = None
            for key in data:
                partyData = data.get(key)
                break
            if not partyData or not key:
                break
            # We have our Party ID and list of information, so let's continue on
            # First, are we past the date and time when the party should've ended?
            partyInfo = partyData[0]
            startTime = datetime.datetime(partyInfo[1], partyInfo[2], partyInfo[3], partyInfo[4], partyInfo[5],
                                          tzinfo=self.air.toontownTimeManager.serverTimeZone)
            endTime = datetime.datetime(partyInfo[6], partyInfo[7], partyInfo[8], partyInfo[9], partyInfo[10])
            currentTime = datetime.datetime.now(tz=self.air.toontownTimeManager.serverTimeZone)
            delta = datetime.timedelta(minutes=15)
            endStartable = startTime + delta
            if endStartable < currentTime:
                # Well, looks like it's too late to start the Party now. Let's just delete it
                os.remove(self.serverDataFolder + 'parties/' + filename)
                # append to calendar party data in form of following:
                # [hostId, [startTime data], [endTime data], [inviteeIDs], isPrivate, theme, status]
                status = partyInfo[15]
                if status in (PartyGlobals.PartyStatus.Pending, PartyGlobals.PartyStatus.CanStart):
                    status = PartyGlobals.PartyStatus.NeverStarted
                elif status == PartyGlobals.PartyStatus.Started:
                    status = PartyGlobals.PartyStatus.Finished
                pdata = [partyInfo[0],
                         [partyInfo[1], partyInfo[2], partyInfo[3], partyInfo[4], partyInfo[5]],
                         [partyInfo[6], partyInfo[7], partyInfo[8], partyInfo[9], partyInfo[10]],
                         partyData[1],
                         partyInfo[11],
                         partyInfo[12],
                         status]
                self.partyBackups.addData(pdata)
                continue
            # If we're at this point, that means the party is still valuable, and should be added to the pipeline
            self.addParty(0, partyInfo[0], 0, 0, partyInfo[11], partyInfo[12], partyInfo[13], partyInfo[14],
                          partyData[1], 0, True, startTime, endTime, int(key), partyData[2])

    def rezParties(self, partyMgrId, shardId, parties):
        self.notify.debug('Heroes ALWAYS die!')

        if self.wantInstantParties:
            taskMgr.remove(self.uniqueName('parties-task'))

        def finishStart(pdata):
            hostId = pdata[0]
            partyId = pdata[1]
            startDate = datetime.datetime(pdata[2][0], pdata[2][1], pdata[2][2], pdata[2][3], pdata[2][4], tzinfo=stz)
            endDate = datetime.datetime(pdata[3][0], pdata[3][1], pdata[3][2], pdata[3][3], pdata[3][4], tzinfo=stz)
            isPrivate = pdata[4]
            inviteTheme = pdata[5]
            activities = pdata[6]
            decorations = pdata[7]
            inviteeIds = pdata[8]
            inviteKey = pdata[9]
            zoneId = pdata[10]
            numGuests = pdata[11]
            hostName = pdata[12]
            started = pdata[13]
            avIdsAtParty = pdata[14]

            self.publicParties[partyId] = {
                'shardId': shardId,
                'zoneId': zoneId,
                'hostId': hostId,
                'numberOfGuests': numGuests,
                'hostName': hostName,
                'started': started
            }

            for avId in inviteeIds:
                self.guest2host[avId] = hostId

            # append to calendar party data in form of following:
            # [hostId, [startTime data], [endTime data], [inviteeIDs], isPrivate, theme, status]
            if hostId not in self.backupData:
                self.backupData[hostId] = [hostId,
                                           [startDate.year, startDate.month, startDate.day, startDate.hour,
                                            startDate.minute],
                                           [endDate.year, endDate.month, endDate.day, endDate.hour, endDate.minute],
                                           deepcopy(inviteeIds),
                                           isPrivate,
                                           inviteTheme,
                                           PartyGlobals.PartyStatus.NeverStarted]
            else:
                self.backupData[hostId][6] = PartyGlobals.PartyStatus.NeverStarted

            filename = self.getFilename(self.host2party[hostId][PartyGlobals.PartyId])
            partyData = {self.host2party[hostId][PartyGlobals.PartyId]: [(hostId, startDate.year, startDate.month,
                                                                          startDate.day, startDate.hour,
                                                                          startDate.minute,
                                                                          endDate.year, endDate.month, endDate.day,
                                                                          endDate.hour, endDate.minute, isPrivate,
                                                                          inviteTheme, activities, decorations,
                                                                          PartyGlobals.PartyStatus.Started), inviteeIds,
                                                                         self.host2party[hostId][
                                                                             PartyGlobals.PartyInviteKey]]}
            # re-insert/update party data in party backup folder
            self.updateParties(filename, partyData)
            # and remove archived party data, if any
            self.partyBackups.deleteData(self.backupData[hostId])

            self.notify.debug('rezParties() hostId {} party added with partyId {}'.format(hostId, partyId))

        stz = self.air.toontownTimeManager.serverTimeZone
        for pdata in parties:
            # [hostId, partyId, [start time data], [end time data], isPrivate, inviteTheme, activities, decorations,
            # inviteIds, inviteKey, zoneId, numGuests, hostName, started, avIdsAtParty
            if pdata[0] in self.host2party:
                # set a couple of things
                self.host2party[pdata[0]][PartyGlobals.PartyInfo].status = PartyGlobals.PartyStatus.Started
                # and just finish off anything not created
                finishStart(pdata)
                continue
            hostId = pdata[0]
            partyId = pdata[1]
            startDate = datetime.datetime(pdata[2][0], pdata[2][1], pdata[2][2], pdata[2][3], pdata[2][4], tzinfo=stz)
            endDate = datetime.datetime(pdata[3][0], pdata[3][1], pdata[3][2], pdata[3][3], pdata[3][4], tzinfo=stz)
            isPrivate = pdata[4]
            inviteTheme = pdata[5]
            activities = pdata[6]
            decorations = pdata[7]
            inviteeIds = pdata[8]
            inviteKey = pdata[9]
            # the rest of the stuff here are not used until called via finishStart()
            '''zoneId = pdata[10]
            numGuests = pdata[11]
            hostName = pdata[12]
            started = pdata[13]
            avIdsAtParty = pdata[14]'''

            self.host2party[hostId] = [0, None, None, None]

            self.partyIdAllocator.initialReserveId(partyId)     # this should be unique
            self.host2party[hostId][PartyGlobals.PartyId] = partyId
            partyInfo = PartyInfoAI(self.host2party[hostId][PartyGlobals.PartyId], hostId, startDate.year,
                                    startDate.month,
                                    startDate.day, startDate.hour, startDate.minute, endDate.year, endDate.month,
                                    endDate.day, endDate.hour, endDate.minute, isPrivate, inviteTheme, activities,
                                    decorations, PartyGlobals.PartyStatus.Started)

            self.host2party[hostId][PartyGlobals.PartyInfo] = partyInfo
            self.host2party[hostId][PartyGlobals.PartyInvitees] = inviteeIds
            self.inviteKeyAllocator.initialReserveId(inviteKey)     # this should also be unique
            self.host2party[hostId][PartyGlobals.PartyInviteKey] = inviteKey

            # and finally, finish start stuff
            finishStart(pdata)

        if self.wantInstantParties:
            taskMgr.remove(self.uniqueName('parties-task'))
            taskMgr.doMethodLater(15, self.__partiesTask, self.uniqueName('parties-task'))
        else:
            self.__startPartiesTask()

    def loadParties(self, filename):
        try:
            with open(filename, 'r') as partiesFile:
                partiesData = json.load(partiesFile)
            return partiesData
        except Exception:
            return {}

    def updateParties(self, filename, data):
        try:
            if not os.path.exists(os.path.dirname(filename)):
                os.makedirs(os.path.dirname(filename))

            with open(filename, 'w') as partiesFile:
                json.dump(data, partiesFile, indent=4)
        except Exception:
            pass

    def getFilename(self, partyId):
        return '%s%s%s%s.json' % (self.serverDataFolder, 'parties/', 'party_', partyId)

    def updateAllPartyInfoToUd(self, hostId, partyId, todo2, todo3, todo4, todo5, todo6, todo7, todo8):
        return

    def forceCheckStart(self):
        pass

    def sendUpdateToAI(self, doId, field, args=[]):
        dg = self.dclass.aiFormatUpdate(field, doId, doId, self.doId, args)
        self.air.send(dg)

    def sendUpdateToAllAI(self, field, args=[]):
        for partyMgrId in list(self.partyManagers.values()):
            self.sendUpdateToAI(partyMgrId, field, args)

    def sendUpdateToAvatarId(self, avId, field, args=[], fromDoId=None):
        channel = self.GetPuppetConnectionChannel(avId)
        dg = self.dclass.aiFormatUpdate(field, self.doId if not fromDoId else fromDoId, channel, self.air.ourChannel, args)
        self.air.send(dg)
