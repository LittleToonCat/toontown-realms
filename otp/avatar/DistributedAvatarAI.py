from typing import List, Dict, Tuple, Optional
from otp.ai.AIBaseGlobal import *
from otp.otpbase import OTPGlobals
from direct.fsm import ClassicFSM
from direct.fsm import State
from direct.distributed import DistributedNodeAI
from direct.task import Task
from toontown.battle.StatusEffect import StatusEffect

class DistributedAvatarAI(DistributedNodeAI.DistributedNodeAI):

    def __init__(self, air):
        DistributedNodeAI.DistributedNodeAI.__init__(self, air)
        self.hp = 0
        self.maxHp = 0
        self.statusEffects: Dict[str, StatusEffect] = {}
        self.needsStatusUpdate: bool = False

    def b_setName(self, name):
        self.setName(name)
        self.d_setName(name)

    def d_setName(self, name):
        self.sendUpdate('setName', [name])

    def setName(self, name):
        self.name = name

    def getName(self):
        return self.name

    def b_setMaxHp(self, maxHp):
        self.d_setMaxHp(maxHp)
        self.setMaxHp(maxHp)

    def d_setMaxHp(self, maxHp):
        self.sendUpdate('setMaxHp', [maxHp])

    def setMaxHp(self, maxHp):
        self.maxHp = maxHp

    def getMaxHp(self):
        return self.maxHp

    def b_setHp(self, hp):
        self.d_setHp(hp)
        self.setHp(hp)

    def d_setHp(self, hp):
        self.sendUpdate('setHp', [hp])

    def setHp(self, hp):
        self.hp = hp

    def getHp(self):
        return self.hp

    def b_setLocationName(self, locationName):
        self.d_setLocationName(locationName)
        self.setLocationName(locationName)

    def d_setLocationName(self, locationName):
        pass

    def setLocationName(self, locationName):
        self.locationName = locationName

    def getLocationName(self):
        return self.locationName

    def b_setActivity(self, activity):
        self.d_setActivity(activity)
        self.setActivity(activity)

    def d_setActivity(self, activity):
        pass

    def setActivity(self, activity):
        self.activity = activity

    def getActivity(self):
        return self.activity

    def toonUp(self, num):
        if self.hp >= self.maxHp:
            return
        self.hp = min(self.hp + num, self.maxHp)
        self.b_setHp(self.hp)

    def getRadius(self):
        return OTPGlobals.AvatarDefaultRadius

    def checkAvOnShard(self, avId):
        senderId = self.air.getAvatarIdFromSender()
        onShard = False
        if simbase.air.doId2do.get(avId):
            onShard = True
        self.sendUpdateToAvatarId(senderId, 'confirmAvOnShard', [avId, onShard])

    def d_setLoop(self, anim, start, end, part):
        self.sendUpdate('setLoop', [anim, start, end, part])

    def d_setPingPong(self, anim, start, end, part):
        self.sendUpdate('setPingPong', [anim, start, end, part])

    def d_setPose(self, anim, frame, part):
        self.sendUpdate('setPose', [anim, frame, part])

    def d_setLeftHand(self, prop):
        self.sendUpdate('setLeftHand', [prop])

    def d_setRightHand(self, prop):
        self.sendUpdate('setRightHand', [prop])

    def setStatusEffects(self, statusEffects: List[StatusEffect]):
        for statusEffect in statusEffects:
            self.addStatusEffect(statusEffect)

    def addStatusEffect(self, effect: StatusEffect):
        self.statusEffects[effect.getId()] = effect
        self.needsStatusUpdate = True

    # TODO: removing a status effect should reverse certain environmental effects such as weather
    # but we don't have to worry about that for now
    def removeStatusEffect(self, identifier: str):
        if identifier in self.statusEffects:
            del self.statusEffects[identifier]
            self.needsStatusUpdate = True

    def clearStatusEffects(self):
        if self.statusEffects:
            self.statusEffects = {}
            self.d_setStatusEffects()

    def decStatusEffectRounds(self) -> List[str]:
        removedStatusEffects = []
        for identifier in list(self.statusEffects.keys()):
            effect = self.statusEffects[identifier]
            if effect.getRounds() > 0:
                effect.setRounds(effect.getRounds() - 1)
                if effect.getRounds() == 0:
                    del self.statusEffects[identifier]
                    removedStatusEffects.append(identifier)
                self.needsStatusUpdate = True
        if self.needsStatusUpdate:
            self.d_setStatusEffects()
            self.needsStatusUpdate = False
        return removedStatusEffects

    def getStatusEffects(self) -> List[Tuple[str, int, List[float]]]:
        statusEffects = []
        for identifier, effect in list(self.statusEffects.items()):
            statusEffects.append((identifier, effect.getRounds(), effect.getArgs()))
        return statusEffects

    def d_setStatusEffects(self):
        statusEffects = self.getStatusEffects()
        self.sendUpdate('setStatusEffects', [statusEffects])

    def b_setStatusEffects(self, effectIds: List[StatusEffect]):
        self.setStatusEffects(effectIds)
        self.d_setStatusEffects()

    def hasStatusEffect(self, identifier: str) -> bool:
        return identifier in self.statusEffects

    def getStatusEffect(self, identifier: str) -> Optional[StatusEffect]:
        if self.hasStatusEffect(identifier):
            return self.statusEffects[identifier]
        return None
