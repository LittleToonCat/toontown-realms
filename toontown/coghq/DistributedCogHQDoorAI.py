from otp.ai.AIBaseGlobal import *
from direct.distributed.ClockDelta import *
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM
from toontown.building import DistributedDoorAI
from direct.fsm import State
from toontown.toonbase import ToontownGlobals
from . import CogDisguiseGlobals
from toontown.building import FADoorCodes
from toontown.building import DoorTypes
from toontown.suit import SuitDNA

class DistributedCogHQDoorAI(DistributedDoorAI.DistributedDoorAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedCogHQDoorAI')

    def __init__(self, air, blockNumber, doorType, destinationZone, doorIndex = 0, lockValue = FADoorCodes.SB_DISGUISE_INCOMPLETE, swing = 3):
        DistributedDoorAI.DistributedDoorAI.__init__(self, air, blockNumber, doorType, doorIndex, lockValue, swing)
        self.destinationZone = destinationZone

    def requestEnter(self):
        avatarID = self.air.getAvatarIdFromSender()
        dept = ToontownGlobals.cogHQZoneId2deptIndex(self.destinationZone)
        av = self.air.doId2do.get(avatarID)
        if av:
            if self.doorType == DoorTypes.EXT_COGHQ and self.isLockedDoor():
                parts = av.getCogParts()
                if CogDisguiseGlobals.isSuitComplete(parts, dept):
                    allowed = 1
                else:
                    allowed = 0
            else:
                allowed = 1
            if not allowed:
                self.sendReject(avatarID, self.isLockedDoor())
            else:
                self.enqueueAvatarIdEnter(avatarID)
                self.sendUpdateToAvatarId(avatarID, 'setOtherZoneIdAndDoId', [self.destinationZone, self.otherDoor.getDoId()])

    def requestExit(self):
        avatarID = self.air.getAvatarIdFromSender()
        if avatarID in self.avatarsWhoAreEntering:
            del self.avatarsWhoAreEntering[avatarID]
        if avatarID not in self.avatarsWhoAreExiting:
            self.avatarsWhoAreExiting[avatarID] = 1
            self.sendUpdate('avatarExit', [avatarID])
            self.openDoor(self.exitDoorFSM)
            if self.lockedDoor:
                av = self.air.doId2do[avatarID]
                if self.doorType == DoorTypes.EXT_COGHQ:
                    av.b_setCogIndex('', 0, 0, 2)
                else:
                    deptIndex = ToontownGlobals.cogHQZoneId2deptIndex(self.destinationZone)
                    cogIndex = av.cogTypes[deptIndex] + SuitDNA.suitsPerDept * deptIndex
                    cogShorthand = SuitDNA.suitHeadTypes[cogIndex]
                    av.b_setCogIndex(cogShorthand, 0, 0, 2)
