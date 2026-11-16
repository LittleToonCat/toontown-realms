from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI
from direct.fsm.FSM import FSM


class LoadPetOperation(FSM):
    def __init__(self, mgr, park, toon, callback):
        FSM.__init__(self, 'LoadPetFSM')
        self.mgr = mgr
        self.park = park
        self.toon = toon
        self.callback = callback
        self.done = False
        self.petId = 0

    def start(self):
        if type(self.toon) == dict:
            self.petId = self.toon['setPetId'][0]
        else:
            self.petId = self.toon.getPetId()

        if self.petId not in self.mgr.air.doId2do:
            self.mgr.air.sendActivate(self.petId, self.mgr.air.districtId, self.park.zoneId)
            self.acceptOnce('generate-%d' % self.petId, self.__generated)
        else:
            self.__generated(self.mgr.air.doId2do[self.petId])

    def __generated(self, pet):
        self.pet = pet
        self.park.pets.append(pet)
        self.demand('Off')

    def enterOff(self):
        self.ignore('generate-%d' % self.petId)
        self.done = True
        self.callback()


class PetParkManagerAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('PetParkManagerAI')

    def __init__(self, air):
        DistributedObjectAI.__init__(self, air)
        self.petOperations = []
        self.parks = {}

    def handleLoadPet(self, park, toon):
        petOperation = LoadPetOperation(self, park, toon, self.__handlePetLoaded)
        self.petOperations.append(petOperation)
        petOperation.start()

    def handleUnloadPet(self, petId):
        pet = self.air.doId2do.get(petId)
        if pet and not pet.leashMode:
            pet.requestDelete()

    def __handlePetLoaded(self):
        # A pet operation just finished! Let's see if all of them are done:
        if all(petOperation.done for petOperation in self.petOperations):
            self.petOperations = []
