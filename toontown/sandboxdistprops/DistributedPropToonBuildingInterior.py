# Distributed TestBuildingInterior == Client Side
# Created by drewc Oct 11 2023

from direct.distributed.DistributedObject import DistributedObject
from panda3d.toontown import DNADoor

from toontown.toonbase.ToonBaseGlobal import base
from toontown.toonbase.ToontownTypes import TColoredTexture


class DistributedPropToonBuildingInterior(DistributedObject):

    def __init__(self, cr):
        DistributedObject.__init__(self, cr)
        self.buildingId: int = 0

    def setInteriorStyle(self,
                         interiorModel: str,
                         wallpaper: TColoredTexture,
                         floor: TColoredTexture,
                         molding: TColoredTexture,
                         wainscoting: TColoredTexture,
                         wallpaperBorder: TColoredTexture):
        ...

    def announceGenerate(self):
        DistributedObject.announceGenerate(self)
        self.load()

    def load(self):
        self.notify.debug(f'LOAD {self.doId}')
        self.interiorModel = base.loader.loadModel('phase_3.5/models/modules/toon_interior_L')
        self.interiorModel.reparentTo(base.render)
        self.__setupDoor()

    def __setupDoor(self):
        self.notify.debug(f'Setup Door {self.doId}')
        doorModel = base.loader.loadModel('phase_3.5/models/modules/doors_practical')
        door = doorModel.find('**/door_double_curved_ur')

        self.doorOrigin = self.interiorModel.find('**/*door_origin')
        self.doorOrigin.setHpr(180, 0, 0)
        self.doorOrigin.setPos(self.doorOrigin, 0.0, -.1, 0.0)

        door.reparentTo(self.doorOrigin)

        doorModel.removeNode()
        del doorModel

        DNADoor.setupDoor(door, self.interiorModel, self.doorOrigin, self.cr.playGame.dnaStore, str(self.buildingId), (1.0, 1.0, 1.0, 1.0))

    def setBuildingId(self, index: int):
        self.buildingId = index

    def delete(self):
        self.ignoreAll()
        self.removeAllTasks()
        self.interiorModel.removeNode()
        del self.interiorModel
