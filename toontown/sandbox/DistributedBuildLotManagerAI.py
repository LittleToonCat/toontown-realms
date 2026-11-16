"""
DistributedBuildLotManager AI Side • Created by Drew @ 12/17/2022
Authorized for use ONLY in Toontown Realms
"""
import glob
import json
import os
from typing import Dict

from direct.distributed.DistributedObjectAI import DistributedObjectAI
from direct.directnotify import DirectNotifyGlobal

from toontown.sandbox.BuildLotGlobals import BuildLotThemes, CREATION_ERROR_ALREADY_OPEN, PRIVACY_MODE_PUBLIC
from toontown.sandbox.DistributedBuildLotAI import DistributedBuildLotAI
from toontown.toon.DistributedToonAI import DistributedToonAI
from toontown.toonbase import TTLocalizer


class DistributedBuildLotManagerAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory("DistBuildLotMGRAI")
    notify.setDebug(1)

    def __init__(self, air):
        DistributedObjectAI.__init__(self, air)

        self.avIdToBuildLots: Dict[int, DistributedBuildLotAI] = {}

    def delete(self):
        self.ignoreAll()
        for lot in self.avIdToBuildLots.values():
            lot.requestDelete()

    def requestCreateLot(self, theme: BuildLotThemes, saveToLoad: str, name:str, privacyMode: int = PRIVACY_MODE_PUBLIC):
        ownerId = self.air.getAvatarIdFromSender()

        if saveToLoad == '':
            saveToLoad = None

        privModesToDebug = ('Public', 'Friends Only', 'Private')
        if saveToLoad:
            self.notify.debug(f'{privModesToDebug[privacyMode]} lot creation requested by '
                              f'{ownerId} w/ theme {theme} using save "/lots/{ownerId}/{saveToLoad}.json"')
        else:
            self.notify.debug(f'{privModesToDebug[privacyMode]} lot creation requested by {ownerId} w/ theme {theme} w/ clean slate')

        if ownerId in self.avIdToBuildLots.keys():
            self.sendUpdateToAvatarId(ownerId, 'requestCreateErrorResponse', [CREATION_ERROR_ALREADY_OPEN])

            self.notify.debug(f'Lot creation requested by {ownerId} DENIED - AV already has an open one! (CODE 000)')
            return

        # Allocate the zone ID & Spawn the lot
        zoneId = self.air.allocateZone()

        lotAI = DistributedBuildLotAI(self.air, ownerId, zoneId, theme, privacyMode, name, saveToLoad)
        lotAI.generateWithRequired(zoneId)
        self.avIdToBuildLots[ownerId] = lotAI

        self.notify.debug(f'{privModesToDebug[privacyMode]} lot creation requested by '
                          f'{ownerId} success - zone {zoneId} w/ doID {lotAI.doId}')
        self.sendUpdateToAvatarId(ownerId, 'requestCreateSuccessResponse', [zoneId])

    def destroyBuildLot(self, ownerId: int):
        if ownerId not in self.avIdToBuildLots:
            self.notify.warning(f'Lot owned by {ownerId} was attempted to be deleted, but doesn\'t actually exist!')

        lotAI = self.avIdToBuildLots.get(ownerId)
        zoneId = lotAI.zoneId

        lotAI.requestDelete()
        del self.avIdToBuildLots[ownerId]

        # Deallocate the zone ID we used
        self.air.deallocateZone(zoneId)

    def requestTeleport(self, ownerId: int):
        if ownerId in self.avIdToBuildLots:
            self.sendUpdateToAvatarId(self.air.getAvatarIdFromSender(), 'requestTeleportResponse',
                                      [self.avIdToBuildLots[ownerId].zoneId, ownerId])

    def requestMySaves(self):
        avId = self.air.getAvatarIdFromSender()
        if os.path.exists(f'buildlots/player/{avId}'):
            saves = []
            for filename in os.listdir(f'buildlots/player/{avId}'):
                with open(f'buildlots/player/{avId}/{filename}') as file:
                    try:
                        data = json.load(file)
                        saves.append((filename, data.get('name', TTLocalizer.BuildLotDefaultName), data.get('theme', 0), data.get('privacy', 0), data.get('last_edit', 0)))
                    except:
                        self.notify.warning(f'Error loading buildlots/player/{avId}/{filename}')

            self.sendUpdateToAvatarId(avId, 'requestMySavesResponse', [saves])

    def deleteMySave(self, save):
        avId = self.air.getAvatarIdFromSender()
        filename = f'buildlots/player/{avId}/{save}'
        if os.path.exists(filename):
            os.remove(filename)

    """ === List === """
    def requestOpenLots(self):
        lots = []
        for avId, lotAI in self.avIdToBuildLots.items():
            if lotAI.canUsersJoin:
                if avId in self.air.doId2do:
                    av: DistributedToonAI = self.air.doId2do.get(avId)
                    ownerName = av.getName()
                    dna = av.getDNAString()
                    hat = av.getHat()
                    glasses = av.getGlasses()
                else:
                    ownerName = 'ERROR RETRIEVING OWNER NAME'
                    dna = b'None'
                    hat = (0, 0, 0)
                    glasses = (0, 0, 0)

                lots.append((avId, ownerName, lotAI.lotName, lotAI.privacy, lotAI.theme, len(lotAI.getToonsInLot()), dna, hat, glasses))

        self.sendUpdateToAvatarId(self.air.getAvatarIdFromSender(), 'requestOpenLotsResponse', [lots])
