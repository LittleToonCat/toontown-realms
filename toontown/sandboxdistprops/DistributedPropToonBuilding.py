# Distributed TestBuilding == Client Side
# Created by drewc Oct 11 2023
# PROTOTYPE
from direct.directnotify import DirectNotifyGlobal
from typing import Optional

from panda3d.core import NodePath

from panda3d.toontown import DNADoor

from toontown.sandboxdistprops.DistributedProp import DistributedProp
from toontown.toonbase.ToonBaseGlobal import base


class DistributedPropToonBuilding(DistributedProp):
    notify = DirectNotifyGlobal.directNotify.newCategory('Dist Prop Test : Building W Interior 01')
    notify.setDebug(True)

    def __init__(self, cr):
        DistributedProp.__init__(self, cr)

        self.buildingModel: Optional[NodePath] = None
        self.doorOrigin: Optional[NodePath] = None

    def announceGenerate(self):
        DistributedProp.announceGenerate(self)
        self.cr.propGenBuildings[self.doId] = self
        self.load()

    def load(self):
        self.notify.debug(f'LOAD {self.doId}')
        self.buildingModel = base.loader.loadModel('phase_3.5/models/modules/TT_A1')
        self.buildingModel.reparentTo(self)
        self.reparentTo(base.render)
        self.__setupDoor()

    def __setupDoor(self):
        self.notify.debug(f'Setup Door {self.doId}')
        doorModel = base.loader.loadModel('phase_3.5/models/modules/doors_practical')
        door = doorModel.find('**/door_double_curved_ur')

        self.doorOrigin = self.buildingModel.find('**/*door_origin')
        self.doorOrigin.setHpr(0, 0, 0)
        self.doorOrigin.setPos(self.doorOrigin, 0.0, -0.2, 0.0)

        door.reparentTo(self.doorOrigin)

        doorModel.removeNode()
        del doorModel

        DNADoor.setupDoor(door, self.buildingModel, self.doorOrigin, self.cr.playGame.dnaStore, str(self.doId), (1.0, 1.0, 1.0, 1.0))

    def unload(self):
        self.notify.debug(f'UNLOADING {self.doId}')
        self.ignoreAll()
        self.removeAllTasks()

    def delete(self):
        if self.doId in self.cr.propGenBuildings:
            del self.cr.propGenBuildings[self.doId]
        self.unload()
        DistributedProp.delete(self)