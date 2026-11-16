from panda3d.core import *
from .DistributedNPCToon import *


class DistributedNPCFlippyInToonHall(DistributedNPCToon):

    def __init__(self, cr):
        DistributedNPCToon.__init__(self, cr)

    def getCollSphereRadius(self):
        return 4

    def initPos(self):
        self.clearMat()
        self.setScale(1.25)

    if HALLOWEEN:
        def announceGenerate(self):
            self.initToonState()
            DistributedToon.DistributedToon.announceGenerate(self)
            # halloween only
            random.seed(self.getDoId())
            costume = ToontownGlobals.NPCHalloweenCostumes[1]
            dna = self.style
            dna.topTex = costume[0][0]
            dna.topTexColor = costume[0][1]
            dna.sleeveTex = costume[1][0]
            dna.sleeveTexColor = costume[1][1]
            dna.botTex = costume[2][0]
            dna.botTexColor = costume[2][1]
            self.setDNA(dna)
            self.setHat(*costume[3], 0)
            self.setGlasses(*costume[4], 0)
            self.setBackpack(*costume[5], 0)
            self.setShoes(*costume[6], 0)

    def handleCollisionSphereEnter(self, collEntry):
        base.cr.playGame.getPlace().fsm.request('quest', [self])
        self.sendUpdate('avatarEnter', [])
        self.nametag3d.setDepthTest(0)
        self.nametag3d.setBin('fixed', 0)
        self.lookAt(base.localAvatar)
