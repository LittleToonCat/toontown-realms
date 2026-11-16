from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObject import DistributedObject

from otp.util import random
from toontown.building import ToonInteriorColors
from toontown.hood import ZoneUtil
from direct.distributed.DistributedObject import DistributedObject

from toontown.toonbase.ToonBase import *


class DistributedArcadeInterior(DistributedObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedArcadeInterior')

    def __init__(self, cr):
        DistributedObject.__init__(self, cr)
        self.dnaStore = cr.playGame.dnaStore

    def generate(self):
        DistributedObject.generate(self)

    def announceGenerate(self):
        DistributedObject.announceGenerate(self)
        self.setup()

    def disable(self):
        self.interior.removeNode()
        del self.interior
        DistributedObject.disable(self)
        #super().disable()

    def setZoneIdAndBlock(self, zoneId, block):
        self.zoneId = zoneId
        self.block = block

    def chooseDoor(self):
        doorModelName = 'door_double_round_ul'
        if doorModelName[-1:] == 'r':
            doorModelName = doorModelName[:-1] + 'l'
        else:
            doorModelName = doorModelName[:-1] + 'r'
        door = self.dnaStore.findNode(doorModelName)
        return door

    def setup(self):
        self.dnaStore = base.cr.playGame.dnaStore
        self.randomGenerator = random.Random()
        self.randomGenerator.seed(self.zoneId)

        self.interior = loader.loadModel('phase_14.5/models/modules/ttrm_m_ara_int_tsk_arcade')
        self.interior.reparentTo(render)

        hoodId = ZoneUtil.getCanonicalHoodId(self.zoneId)
        self.colors = ToonInteriorColors.colors[hoodId]
        door = self.chooseDoor()

        doorOrigin = render.find('**/door_origin;+s')
        doorNP = door.copyTo(doorOrigin)
        doorOrigin.setScale(0.8, 0.8, 0.8)
        doorOrigin.setPos(doorOrigin, 0, -0.025, 0)

        # TEMP UNTIL I EXPORT UPDATED MODEL
        doorOrigin.setH(180)
        render.find('**/npc_origin_0').setH(180)

        doorColor = self.randomGenerator.choice(self.colors['TI_door'])
        DNADoor.setupDoor(doorNP, self.interior, doorOrigin, self.dnaStore, str(self.block), doorColor)
        doorFrame = doorNP.find('door_*_flat')
        doorFrame.wrtReparentTo(self.interior)
        doorFrame.setColor(doorColor)

        del self.colors
        del self.dnaStore
        del self.randomGenerator