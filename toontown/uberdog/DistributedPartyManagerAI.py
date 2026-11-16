import datetime
from math import floor

from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI

from otp.distributed.OtpDoGlobals import *
from toontown.estate.DistributedMailboxAI import DistributedMailboxAI
from toontown.parties import PartyGlobals
from toontown.parties.DistributedPartyAI import DistributedPartyAI
from toontown.parties.PartyInfo import PartyInfoAI

from direct.discord_rpc.util.utils import iter_items


class DistributedPartyManagerAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedPartyManagerAI')

    def __init__(self, air):
        DistributedObjectAI.__init__(self, air)
        self.host2party = {} # hostId: [partyId, partyInfo, inviteeIds, inviteKey]
        self.party2host = {} # partyInfo: hostId
        self.publicParties = {}
        self.__ignorePublicPartyUpdates = False

    def announceGenerate(self):
        DistributedObjectAI.announceGenerate(self)
        # Let the UberDOG know that we now exist.
        self.sendUpdateToUD('partyManagerAIStartingUp', [self.doId, self.air.districtId])

        # Now we add the shutdown message as a post remove.
        dg = self.prepareUpdateToUD('partyManagerAIGoingDown', [self.doId, self.air.districtId])
        self.air.addPostRemove(dg)
        # listen for UD online messages; this likely means a UD restarted during our lifetime
        self.air.netMessenger.accept('UdOnline', self, self.__udRestarted)

    def addPartyRequest(self, hostId, startTime, endTime, isPrivate, inviteTheme, activities, decorations, inviteeIds,
                        free=False):
        senderId = self.air.getAvatarIdFromSender()
        av = self.air.doId2do.get(hostId)

        self.notify.debug('addPartyRequest: {}, {}, {}, {}, {}, {}, {}, {}'.format(hostId, startTime, endTime, isPrivate,
                                                                                    inviteTheme, activities, decorations,
                                                                                    inviteeIds))

        if not av:
            self.notify.warning('Toon {} tried to create a party but does not exist on the server!'.format(senderId))
            self.air.writeServerEvent('suspicious', avId=senderId,
                                      issue='Toon tried to create a party but does not exist on the server!')
            self.sendUpdateToAvatarId(senderId, 'addPartyResponse', [hostId, PartyGlobals.AddPartyErrorCode.ValidationError])
            return
        if hostId != senderId:
            self.notify.warning('Toon {} tried to create a party as someone else!'.format(senderId))
            self.air.writeServerEvent('suspicious', avId=senderId,
                                      issue='Toon tried to create a party as someone else!')
            self.sendUpdateToAvatarId(senderId, 'addPartyResponse', [hostId, PartyGlobals.AddPartyErrorCode.ValidationError])
            return

        startDate = datetime.datetime.strptime(startTime, '%Y-%m-%d %H:%M:%S')
        endDate = datetime.datetime.strptime(endTime, '%Y-%m-%d %H:%M:%S')
        partyInfo = PartyInfoAI(0, hostId, startDate.year, startDate.month, startDate.day,
                                startDate.hour, startDate.minute, endDate.year, endDate.month, endDate.day,
                                endDate.hour, endDate.minute, isPrivate, inviteTheme, activities, decorations,
                                PartyGlobals.PartyStatus.Pending)

        cost = PartyGlobals.getCostOfParty(partyInfo) if not free else 0
        self.sendUpdateToUD('addParty',
                            [self.doId, hostId, startTime, endTime, isPrivate, inviteTheme, activities,
                             decorations, inviteeIds, cost])

    def addPartyResponseUdToAi(self, hostId, errorCode, cost):
        host = self.air.doId2do.get(hostId)
        if host and cost:
            host.takeMoney(cost)
        self.sendUpdateToAvatarId(hostId, 'addPartyResponse', [hostId, errorCode])

    def markInviteAsReadButNotReplied(self, avId, inviteKey):
        if not avId:
            return

        av = self.air.doId2do.get(avId)
        if not av:
            return

        av.updateInvite(inviteKey, PartyGlobals.InviteStatus.ReadButNotReplied)

    def d_respondToInvite(self, avId, response, context, inviteKey):
        self.sendUpdateToUD('respondToInvite', [self.doId, avId, context, inviteKey, response])

    def respondToInviteResponse(self, avId, context, inviteKey, response, inviteStatus):
        if not avId:
            return

        av = self.air.doId2do.get(avId)
        if not av:
            return

        invites = []
        for invite in av.invites:
            if invite.inviteKey == inviteKey:
                invite.status = inviteStatus

            invites.append([invite.inviteKey, invite.partyId, invite.status])

        av.b_setInvites(invites)

        mailbox = None
        for do in list(simbase.air.doId2do.values()):
            if isinstance(do, DistributedMailboxAI):
                if avId == do.house.getAvatarId():
                    mailbox = do
                    break
        if mailbox:
            if inviteStatus == PartyGlobals.InviteStatus.Accepted:
                mailbox.sendUpdateToAvatarId(avId, 'acceptItemResponse', [context, response])
            elif inviteStatus == PartyGlobals.InviteStatus.Rejected:
                mailbox.sendUpdateToAvatarId(avId, 'discardItemResponse', [context, response])
        else:
            self.notify.warning('Couldn\'t find mailbox for {}!  Not sending invite response.'.format(avId))

    def changePrivateRequest(self, partyId, newPrivateStatus):
        hostId = self.air.getAvatarIdFromSender()
        self.changePrivateRequestAiToUd(hostId, partyId, newPrivateStatus)

    def changePrivateRequestAiToUd(self, hostId, partyId, newPrivateStatus):
        self.sendUpdateToUD('changePrivateRequestAiToUd', [hostId, partyId, newPrivateStatus])

    def changePrivateResponseUdToAi(self, hostId, partyId, newPrivateStatus, errorCode):
        self.changePrivateResponse(hostId, partyId, newPrivateStatus, errorCode)

    def changePrivateResponse(self, hostId, partyId, newPrivateStatus, errorCode):
        av = self.air.doId2do.get(hostId)
        if not av:
            return

        self.sendUpdateToAvatarId(hostId, 'changePrivateResponse', [partyId, newPrivateStatus, errorCode])

    def changePartyStatusRequest(self, partyId, newPartyStatus):
        hostId = self.air.getAvatarIdFromSender()
        self.changePartyStatusRequestAiToUd(hostId, partyId, newPartyStatus)

    def changePartyStatusRequestAiToUd(self, hostId, partyId, newPartyStatus, confirmFinished=False):
        if partyId not in self.party2host:
            self.party2host[partyId] = hostId
        if newPartyStatus == PartyGlobals.PartyStatus.Finished and not confirmFinished:
            self.notify.warning('Unauthorized attempt to set party state to Finished!')
            return
        self.sendUpdateToUD('changePartyStatusRequestAiToUd', [hostId, partyId, newPartyStatus])

    def changePartyStatusResponseUdToAi(self, partyId, newPartyStatus, errorCode, beansRefunded):
        self.changePartyStatusResponse(partyId, newPartyStatus, errorCode, beansRefunded)

    def changePartyStatusResponse(self, partyId, newPartyStatus, errorCode, beansRefunded):
        hostId = self.party2host[partyId]

        av = self.air.doId2do.get(hostId)
        if not av:
            return

        self.sendUpdateToAvatarId(hostId, 'changePartyStatusResponse', [partyId, newPartyStatus, errorCode,
                                                                        beansRefunded])

    def partyInfoOfHostFailedResponseUdToAi(self, todo0):
        pass

    def partyInfoOfHostResponseUdToAi(self, partyStruct, inviteeIds):
        partyInfo = PartyInfoAI(*partyStruct)
        partyId = partyInfo.partyId
        hostId = partyInfo.hostId
        host = self.air.doId2do.get(hostId)
        if not host:
            return

        self.host2party[hostId] = [partyId, partyInfo, inviteeIds, None, None, None]

        zoneId, partyId = self.createParty(hostId, partyInfo)

        self.sendUpdateToAvatarId(hostId, 'receivePartyZone', [hostId, partyId, zoneId])

    def givePartyRefundResponse(self, todo0, todo1, todo2, todo3, todo4):
        pass

    def getPartyZone(self, avId, zoneId, planningParty):
        senderId = self.air.getAvatarIdFromSender()
        if planningParty:
            self.sendUpdateToAvatarId(senderId, 'receivePartyZone', [avId, 0, zoneId])
        else:
            self.sendUpdateToUD('partyInfoOfHostRequestAiToUd', [self.doId, avId], sender=self.air.getMsgSender())

    def freeZoneIdFromPlannedParty(self, todo0, todo1):
        pass

    def sendAvToPlayground(self, todo0, todo1):
        pass

    def exitParty(self, zoneId):
        # senderId = self.air.getAvatarIdFromSender()
        hosterId = 0
        for partyId in list(self.publicParties.keys()):
            partyInfo = self.publicParties[partyId]
            if zoneId == partyInfo['zoneId']:
                hosterId = partyInfo['hostId']
                break

        if not hosterId:
            return

        # party handles this
        # self.toonHasExitedPartyAiToUd(senderId)

    def removeGuest(self, todo0, todo1):
        pass

    def partyHasStartedAiToUd(self, partyId, shardId, zoneId, hostId, hostName):
        self.sendUpdateToUD('partyHasStartedAiToUd', [partyId, shardId, zoneId, hostId, hostName])

    def toonHasEnteredPartyAiToUd(self, avId, partyId, gateId):
        self.sendUpdateToUD('toonHasEnteredPartyAiToUd', [avId, partyId, gateId])

    def toonHasEnteredPartyUdToAI(self, avId, gateId, partyInfoTuple):
        if gateId:
            gate = self.air.doId2do.get(gateId)
            if gate:
                gate.setParty(avId, partyInfoTuple)

    def toonHasExitedPartyAiToUd(self, avId):
        self.sendUpdateToUD('toonHasExitedPartyAiToUd', [avId])

    def partyHasFinishedUdToAllAi(self, partyId):
        if partyId in self.party2host:
            del self.party2host[partyId]
        for hostId in [hostId for hostId in list(self.host2party.keys()) if self.host2party[hostId][0] == partyId]:
            del self.host2party[hostId]
        if partyId in self.publicParties:
            del self.publicParties[partyId]

    def updateToPublicPartyInfoUdToAllAi(self, hostId, partyId, shardId, zoneId, numberOfGuests, isPrivate, hostName,
                                         activityIds, started):
        if not self.__ignorePublicPartyUpdates:
            # only update when we aren't ignore updates (basically UD restart while AI lived)
            self.publicParties[partyId] = {
                'shardId': shardId,
                'zoneId': zoneId,
                'hostId': hostId,
                'numberOfGuests': numberOfGuests,
                'hostName': hostName,
                'activityIds': activityIds,
                'started': started,
                'isPrivate': isPrivate
            }

    def updateToPublicPartyCountUdToAllAi(self, todo0, todo1):
        pass

    def requestShardIdZoneIdForHostId(self, hostId):
        avId = self.air.getAvatarIdFromSender()
        self.sendUpdateToUD('requestShardIdZoneIdForHostId', [hostId], sender=self.doId << 32 | avId)

    def sendShardIdZoneIdToAvatar(self, shardId, zoneId):
        avId = self.air.getAvatarIdFromSender()
        self.sendUpdateToAvatarId(avId, 'sendShardIdZoneIdToAvatar', [shardId, zoneId])

    def partyManagerUdStartingUp(self):
        pass

    def forceCheckStart(self):
        pass

    def canBuyParties(self):
        return True

    def getPublicParties(self):
        publicPartiesList = []
        for partyId in self.publicParties:
            party = self.publicParties[partyId]
            if party['isPrivate']:
                continue
            minLeft = int(((party['started'] + PartyGlobals.PARTY_DURATION) - self.air.time.now()) / 60)
            if minLeft <= 0:
                continue
            guests = max(0, min(party.get('numberOfGuests', 0), 255))
            publicPartiesList.append([party['shardId'], party['zoneId'], guests, party.get('hostName', ''),
                                      party.get('activityIds', []), minLeft])

        return publicPartiesList

    def createParty(self, hostId, partyInfo):
        host = self.air.doId2do.get(hostId)
        if not host:
            return

        zoneId = self.air.allocateZone(owner=self)
        self.host2party[hostId][3] = zoneId

        partyId = partyInfo.partyId

        party = DistributedPartyAI(self.air, hostId, zoneId, self.host2party[hostId][1])
        for activity in party.partyInfo.activityList:
            if activity.activityId == PartyGlobals.ActivityIds.PartyClock:
                party.setPartyClockInfo(activity.x, activity.y, activity.h)

        party.setInviteeIds(self.host2party[hostId][2])
        party.setPartyState(False)
        party.setPartyStartedTime(self.air.toontownTimeManager.getCurServerDateTime().strftime('%Y-%m-%d %H:%M:%S'))
        party.setHostName(host.getName())
        party.generateWithRequired(zoneId)
        self.host2party[hostId][4] = party

        self.partyHasStartedAiToUd(partyId, self.air.districtId, zoneId, hostId, host.getName())

        return zoneId, partyId

    def endParty(self, party):
        partyId = self.host2party[party.hostId][0]
        self.changePartyStatusRequestAiToUd(party.hostId, partyId, PartyGlobals.PartyStatus.Finished, confirmFinished=True)
        for avId in party.avIdsAtParty:
            self.sendUpdateToAvatarId(avId, 'sendAvToPlayground', [avId, 0])
        party.b_setPartyState(True)
        taskMgr.doMethodLater(PartyGlobals.DelayBeforeAutoKick, self.kickAvsFromPartyAndDelete, party.uniqueName('kickAvsFromParty'), extraArgs=[party])

    def kickAvsFromPartyAndDelete(self, party):
        for avId in party.avIdsAtParty:
            self.sendUpdateToAvatarId(avId, 'sendAvToPlayground', [avId, 1])
        taskMgr.doMethodLater(10, lambda: party.requestDelete(), party.uniqueName('deleteParty'), extraArgs=[])

    def prepareUpdateToUD(self, field, args=[], sender=None):
        return self.dclass.aiFormatUpdate(field, OTP_DO_ID_TOONTOWN_PARTY_MANAGER, OTP_DO_ID_TOONTOWN_PARTY_MANAGER,
                                          self.doId if sender == None else sender, args)

    def sendUpdateToUD(self, field, args=[], sender=None):
        dg = self.prepareUpdateToUD(field, args, sender)
        self.air.send(dg)

    def getPartyIdFromHostId(self, hostId):
        if hostId in self.host2party:
            return self.host2party[hostId][0]
        return None

    def reloadPartyBackups(self):
        # basically use this to keep file reloading to a minimum
        if hasattr(self.air, 'partyBackups'):
            self.air.partyBackups.reloadData()
            messenger.send('archivedPartyDataUpdate', [])
        else:
            self.notify.warning('Unable to reload archived party data!')

    def __udRestarted(self):
        # Welp, looks like the UD died and resurrected (restarted); resend all the important bits
        # Let the UberDOG know that we *still* exist.
        self.notify.debug('Experience nothingness...')
        self.__ignorePublicPartyUpdates = True if len(self.host2party) > 0 else False
        self.sendUpdateToUD('partyManagerAIStartingUp', [self.doId, self.air.districtId])

        # tell UD of any parties that are essentially dead in its eyes
        # self.host2party - hostId: [partyId, partyInfo, inviteeIds, inviteKey, DistributedParty()]
        if len(self.host2party) > 0:
            parties = []
            for hostId, partyData in iter_items(self.host2party):
                if partyData[0] not in self.publicParties:
                    self.notify.warning('Cannot find related public party data; continuing.')
                    continue
                # [hostId, partyId, [start time data], [end time data], isPrivate, inviteTheme, activities,
                # decorations, inviteIds, inviteKey, zoneId, numGuests, hostName, started, avIdsAtParty
                partyInfo = partyData[1]
                s = partyInfo.startTime
                e = partyInfo.endTime
                priv = partyInfo.isPrivate
                theme = partyInfo.inviteTheme
                alist = [[x.activityId, x.x, x.y, x.h] for x in partyInfo.activityList]
                dlist = [[x.decorId, x.x, x.y, x.h] for x in partyInfo.decors]
                avIdsAtParty = partyData[4].avIdsAtParty
                if self.publicParties[partyData[0]].get('numberOfGuests', 0) != len(avIdsAtParty):
                    # avIds at party count should be more accurate than numberOfGuests, so use that
                    guests = len(avIdsAtParty)
                else:
                    # otherwise, use numberOfGuests
                    guests = self.publicParties[partyData[0]].get('numberOfGuests', 0)
                guests = max(0, min(guests, 255))
                started = self.publicParties[partyData[0]].get('started', int(floor(self.air.time.now())))
                name = self.publicParties[partyData[0]].get('hostName', '')
                parties.append([hostId,
                                partyData[0],
                                [s.year, s.month, s.day, s.hour, s.minute],
                                [e.year, e.month, e.day, e.hour, e.minute],
                                priv,
                                theme,
                                alist,
                                dlist,
                                partyData[2],
                                partyData[3],
                                partyData[4].zoneId,
                                guests,
                                name,
                                started,
                                avIdsAtParty])
            self.__ignorePublicPartyUpdates = False
            self.sendUpdateToUD('rezParties', [self.doId, self.air.districtId, parties])
