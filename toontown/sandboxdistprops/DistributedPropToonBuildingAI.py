# Distributed TestBuilding == AI Side
# Created by drewc Oct 11 2023
# PROTOTYPE
from typing import Optional, Dict, Any

from toontown.building import DoorTypes
from toontown.building.DistributedDoorAI import DistributedDoorAI
from toontown.sandboxdistprops.DistributedPropAI import DistributedPropAI
from toontown.sandboxdistprops.DistributedPropToonBuildingInteriorAI import DistributedPropToonBuildingInteriorAI


class DistributedPropToonBuildingAI(DistributedPropAI):

    def __init__(self,
                 air,
                 generator,
                 name: str,
                 uuid: str,
                 data: Optional[Dict[str, Any]] = None):
        DistributedPropAI.__init__(self, air, generator, name, uuid, data)

        self.uuid: str = uuid

        self.interior: Optional[DistributedPropToonBuildingInteriorAI] = None
        self.interiorZoneId: Optional[int] = None

        self.door: Optional[DistributedDoorAI] = None
        self.insideDoor: Optional[DistributedDoorAI] = None

    def announceGenerate(self):
        DistributedPropAI.announceGenerate(self)
        self.setupInterior()

    def setupInterior(self):
        self.interiorZoneId = self.air.allocateZone()

        # Outside door:
        self.door = DistributedDoorAI(self.air, self.doId, DoorTypes.EXT_STANDARD)

        # Inside door:
        self.insideDoor = DistributedDoorAI(self.air, self.doId, DoorTypes.INT_STANDARD)

        # Link them
        self.door.setOtherDoor(self.insideDoor)
        self.insideDoor.setOtherDoor(self.door)
        self.door.zoneId = self.zoneId
        self.insideDoor.zoneId = self.interiorZoneId

        # Generate them
        self.door.generateWithRequired(self.zoneId)
        self.insideDoor.generateWithRequired(self.interiorZoneId)

        # Generate the interior
        if self.interior is not None:
            self.interior.requestDelete()
            self.interior = None

        self.interior = DistributedPropToonBuildingInteriorAI(self.air, self.doId, self.interiorZoneId, self)
        self.interior.generateWithRequired(self.interiorZoneId)

    def destroyInterior(self):
        self.air.deallocateZone(self.interiorZoneId)
        self.interior.requestDelete()
        self.interior = None
        self.door.requestDelete()
        self.door = None
        self.insideDoor.requestDelete()
        self.insideDoor = None
