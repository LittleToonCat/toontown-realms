from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI
from toontown.parties import PartyGlobals


class DistributedPartyGateAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedPartyGateAI')

    def getPartyList(self, avId):
        self.sendUpdateToAvatarId(avId, 'listAllPublicParties', [self.air.partyManager.getPublicParties()])

    def partyChoiceRequest(self, avId, shardId, zoneId):
        publicParties = self.air.partyManager.publicParties
        for partyId in publicParties:
            party = publicParties[partyId]
            # it could just be me, but i'm *fairly* certain this is the wrong way to check shardId...
            #if party.get('shardId', 0 == shardId and party.get('zoneId', 0) == zoneId):
            # i'm *pretty* sure the 'if' below is correct...
            # if not, remove the below 'if' and uncomment the one above
            if party.get('shardId', 0) == shardId and party.get('zoneId', 0) == zoneId:
                retCode = self.air.partyManager.toonHasEnteredPartyAiToUd(avId, partyId, self.doId)
                if retCode:
                    self.sendUpdateToAvatarId(avId, 'partyRequestDenied', [retCode])
                return
        self.sendUpdateToAvatarId(avId, 'partyRequestDenied', [PartyGlobals.PartyGateDenialReasons.Unavailable])

    def setParty(self, avId, partyInfoTuple):
        self.sendUpdateToAvatarId(avId, 'setParty', [partyInfoTuple])
