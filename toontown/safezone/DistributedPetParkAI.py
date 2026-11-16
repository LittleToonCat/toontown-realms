from direct.distributed.DistributedObjectAI import DistributedObjectAI
from toontown.toon.DistributedToonAI import DistributedToonAI


class DistributedPetParkAI(DistributedObjectAI):
    def __init__(self, air):
        DistributedObjectAI.__init__(self, air)
        self.pets = []

    def announceGenerate(self):
        DistributedObjectAI.announceGenerate(self)

        taskMgr.add(self.__collisionLoop, self.uniqueName('collisionLoop'), sort=30)
        self.accept(DistributedToonAI.staticGetLogicalZoneChangeAllEvent(), self.__handleAvatarZoneChangeEvent)

    def delete(self):
        self.ignoreAll()
        taskMgr.remove(self.uniqueName('collisionLoop'))

        DistributedObjectAI.delete(self)

    def __handleAvatarZoneChangeEvent(self, newZoneId, oldZoneId, av):
        petId = av.getPetId()
        if newZoneId == self.zoneId:
            if not av.ghostMode and petId:
                self.air.petParkMgr.handleLoadPet(self, av)
                self.acceptOnce(self.air.getAvatarExitEvent(av.doId), self.air.petParkMgr.handleUnloadPet,
                                extraArgs=[petId])
            av.enterPark()
        elif oldZoneId == self.zoneId and newZoneId not in self.air.estateMgr.getEstateZones(av.doId):
            if petId:
                self.air.petParkMgr.handleUnloadPet(petId)
            av.exitPark()

    def __collisionLoop(self, task):
        for pet in self.pets:
            if not pet:
                continue

            collTrav = pet.getCollTrav()
            if collTrav:
                collTrav.traverse(self.getRender())

        return task.cont
