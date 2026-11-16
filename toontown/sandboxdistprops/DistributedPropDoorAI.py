# Distributed Door == AI Side
# Created by drewc Oct 14 2023
import hashlib
from typing import Optional, Dict, Any, List, Tuple

from direct.distributed.DistributedObjectAI import DistributedObjectAI

from otp.avatar.DistributedPlayerAI import DistributedPlayerAI
from toontown.building.DistributedDoorAI import DistributedDoorAI
from toontown.sandboxdistprops.DistributedPropAI import DistributedPropAI
from toontown.toonbase import TTLocalizer


class DistributedPropDoorAI(DistributedPropAI):

    def __init__(self,
                 air,
                 generator,
                 name: str,
                 uuid: str,
                 data: Optional[Dict[str, Any]] = None):
        DistributedPropAI.__init__(self, air, generator, name, uuid, data)
        self.targetDoId: int = 0
        self.targetZoneId: int = 0
        self.targetDoorId: int = 0

        self.isRightDoorOpen = False
        self.enteringAvIds: List[int] = []
        self.isLeftDoorOpen = False
        self.exitingAvIds: List[int] = []

        self.doorId = int(hashlib.sha1(self.uuid.encode('UTF-8')).hexdigest(), 16) % 10 ** 6

    def announceGenerate(self):
        DistributedPropAI.announceGenerate(self)

        # If its just being generated and already has a target, its probably
        # being loaded from a backup, very likely from server start
        # the target zone might not have been loaded in yet so we need to wait a little.
        if self.data.get('target_door', None):
            self.doMethodLater(3, lambda e: self.setTarget(), 'initialTarget')

    def setTarget(self, requestedBy: Optional[DistributedPlayerAI] = None):
        doId = 0
        if self.data.get('target_door', None):
            doId = self.getDoIdForDoorId(self.data.get('target_door'))

        if doId is not None:
            self.b_setTargetDoorDoIdAndZone(doId)
        elif requestedBy:
            requestedBy.d_setSystemMessage(0, TTLocalizer.PropDoor_ErrorNotFound)

    def getDoIdForDoorId(self, doorId: int) -> int:
        for do in self.cr.doId2do.values():
            if isinstance(do, DistributedPropDoorAI):
                if do.doorId == doorId:
                    self.notify.info(f'Found door {doorId} as {do.getDoId()}')
                    return do.getDoId()

    def delete(self):
        DistributedPropAI.delete(self)

    def requestDataChange(self, key: str, valueType: int, values: List[str]):
        avId: int = self.air.getAvatarIdFromSender()
        av: DistributedPlayerAI = self.air.doId2do.get(avId)
        DistributedPropAI.requestDataChange(self, key, valueType, values)
        if key == 'target_door':
            self.setTarget(av)

    def b_setTargetDoorDoIdAndZone(self, doId: int):
        door: DistributedObjectAI = self.air.doId2do.get(doId, None)
        if door is None:
            self.notify.warning(f'Door {doId} does not exist.')
            return

        if isinstance(door, (DistributedPropDoorAI, DistributedDoorAI)):
            zone = door.zoneId

            self.d_setTargetDoorDoIdAndZone(doId, zone, door.doorId)
            self.setTargetDoorDoIdAndZone(doId, zone, door.doorId)
            return
        self.notify.warning(f'{doId} is not a PropDoor or Door.')

    def d_setTargetDoorDoIdAndZone(self, doId: int, zone: int, doorId: int):
        self.sendUpdate('setTargetDoorDoIdAndZone', [doId, zone, doorId])

    def setTargetDoorDoIdAndZone(self, doId: int, zone: int, doorId: int):
        self.targetDoId = doId
        self.targetZoneId = zone
        self.targetDoorId = doorId

    def getTargetDoorDoIdAndZone(self) -> Tuple[int, int, int]:
        return self.targetDoId, self.targetZoneId, self.targetDoorId

    def getDoorId(self) -> int:
        return self.doorId

    def requestEnter(self):
        avId: int = self.air.getAvatarIdFromSender()
        self.sendUpdate('avatarEnter', [avId])
        if avId not in self.enteringAvIds:
            self.enteringAvIds.append(avId)

        self.doMethodLater(1.5, self.doneEntering, f"enter{avId}", extraArgs = [avId])
        if not self.isRightDoorOpen:
            self.isRightDoorOpen = True
            self.sendUpdate('setDoorState', [1, True])

    def requestExit(self):
        avId: int = self.air.getAvatarIdFromSender()
        self.sendUpdate('avatarExit', [avId])
        if avId not in self.exitingAvIds:
            self.exitingAvIds.append(avId)

        self.doMethodLater(1.2, self.doneExiting, f"exit{avId}", extraArgs = [avId])
        if not self.isLeftDoorOpen:
            self.isLeftDoorOpen = True
            self.sendUpdate('setDoorState', [0, True])


    def doneEntering(self, avId: int):
        if avId in self.enteringAvIds:
            self.enteringAvIds.remove(avId)

        if len(self.enteringAvIds) == 0:
            self.isRightDoorOpen = False

            self.sendUpdate('setDoorState', [1, False])

    def doneExiting(self, avId: int):
        if avId in self.exitingAvIds:
            self.exitingAvIds.remove(avId)

        if len(self.exitingAvIds) == 0:
            self.isLeftDoorOpen = False

        self.sendUpdate('setDoorState', [0, False])
