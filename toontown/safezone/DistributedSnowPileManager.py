from panda3d.core import CollisionSphere, CollisionNode

from direct.distributed.DistributedObject import DistributedObject

from toontown.toonbase import ToontownGlobals

import random


class DistributedSnowPileManager(DistributedObject):

    def __init__(self, cr):
        DistributedObject.__init__(self, cr)

        self.piesRestockSfx = loader.loadSfx('phase_9/audio/sfx/CHQ_SOS_pies_restock.ogg')
        self.snowPiles = []

    def announceGenerate(self):
        DistributedObject.announceGenerate(self)

        self.__loadSnowPiles()

        self.accept('enterSnowPile', self.__touchedSnow)

    def disable(self):
        self.ignore('enterSnowPile')
        self.__unloadSnowPiles()

        DistributedObject.disable(self)

    def setPileInfo(self, pileInfo):
        self.pileInfo = pileInfo

    def __loadSnowPiles(self):
        for pos in self.pileInfo:
            pile = loader.loadModel('phase_14.5/models/props/snow_pile_fuller')
            pile.reparentTo(render)
            index = self.pileInfo.index(pos)
            random.seed(self.getDoId() * index)
            pile.setPos(*pos)
            pile.setH(random.randrange(0, 360))
            pile.setScale(2.0)

            sphere = CollisionSphere(0, 0, 0, 3)
            sphere.setTangible(0)
            node = CollisionNode('SnowPile')
            node.addSolid(sphere)
            mask = ToontownGlobals.WallBitmask | ToontownGlobals.GhostBitmask
            node.setIntoCollideMask(mask)
            pile.attachNewNode(node)
            self.snowPiles.append(pile)

    def __unloadSnowPiles(self):
        for pile in self.snowPiles:
            pile.removeNode()

    def __touchedSnow(self, entry):
        self.sendUpdate('touchedSnow', [])
        base.playSfx(self.piesRestockSfx)
