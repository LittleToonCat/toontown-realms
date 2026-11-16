from . import DistributedDoorAI, FADoorCodes
from . import DistributedArcadeInteriorAI
from . import DoorTypes
from toontown.toon import NPCToons


class ArcadeBuildingAI:

    def __init__(self, air, exteriorZone, interiorZone, blockNumber):
        self.air = air
        self.exteriorZone = exteriorZone
        self.interiorZone = interiorZone
        self.setup(blockNumber)

    def cleanup(self):
        for npc in self.npcs:
            npc.requestDelete()

        del self.npcs
        self.door.requestDelete()
        del self.door
        self.insideDoor.requestDelete()
        del self.insideDoor
        self.interior.requestDelete()
        del self.interior

    def setup(self, blockNumber):
        self.interior = DistributedArcadeInteriorAI.DistributedArcadeInteriorAI(blockNumber, self.air,
                                                                                self.interiorZone)
        self.npcs = NPCToons.createNpcsInZone(self.air, self.interiorZone)
        self.interior.generateWithRequired(self.interiorZone)

        door = DistributedDoorAI.DistributedDoorAI(self.air, blockNumber, DoorTypes.EXT_STANDARD)
        insideDoor = DistributedDoorAI.DistributedDoorAI(self.air, blockNumber, DoorTypes.INT_STANDARD)

        # Lock the door if we don't have the experimental features enabled
        # until its deemed ready
        if not simbase.config.GetBool('experimental-features', False):
            door.setDoorLock(FADoorCodes.ARCADE_EXPERIMENTAL)

        door.setOtherDoor(insideDoor)
        insideDoor.setOtherDoor(door)

        door.zoneId = self.exteriorZone
        insideDoor.zoneId = self.interiorZone
        door.generateWithRequired(self.exteriorZone)
        insideDoor.generateWithRequired(self.interiorZone)

        self.door = door
        self.insideDoor = insideDoor
