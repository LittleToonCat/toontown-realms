import random

from direct.distributed.DistributedNodeAI import DistributedNodeAI

from toontown.toon.DistributedToonAI import DistributedToonAI
from toontown.toon.NPCToons import NPCToonDict
from toontown.toon.ToonDNA import ToonDNA

POSES = (
    ('victory', 116),
    ('bored', 96),
    ('think', 59),
    ('wave', 18),
    ('left', 15),
    ('up', 15),
    ('push', 10),
    ('sprinkle-dust', 40)
)

USE_COOLDOWN = 0.25


class DistributedTTStatueActivityAI(DistributedNodeAI):

    def __init__(self, air, npcId = 0):
        DistributedNodeAI.__init__(self, air)
        if npcId == 0:
            npcId = random.choice(list(NPCToonDict.keys()))
        toonData = NPCToonDict[npcId]
        startDNA = ToonDNA()
        if toonData[2] == 'r':
            self.notify.debug(f'generating random toon with seed {npcId} and gender {toonData[3]}')
            startDNA.newToonRandom(npcId, toonData[3], 1)
        else:
            self.notify.debug(f'generating with dna: {toonData[2]}')
            startDNA.newToonFromProperties(*toonData[2])
        self.dna = startDNA.makeNetString()
        self.info = (toonData[1], *random.choice(POSES), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0))
        self.onCoolDown = False

    def generate(self):
        DistributedNodeAI.generate(self)
        self.setDNA(self.dna)
        self.setInfo(*self.info)

    def delete(self):
        DistributedNodeAI.delete(self)

    def destroy(self):
        DistributedNodeAI.destroy(self)

    def touchedStatue(self):
        """
        A client has told the AI that they have touched the statue sphere

        Stores & sends the dna and info
        """
        if self.onCoolDown:
            self.notify.debug('Toon Statue touched, but is on cooldown. Ignoring!')
            return
        self.notify.debug('Toon Statue Touched')
        avId = self.air.getAvatarIdFromSender()
        if not avId:
            return

        av = self.air.doId2do.get(avId)  # type: DistributedToonAI
        if not av:
            return

        if av.dclass == self.air.dclassesByName['DistributedToonAI']:
            self.setDNA(av.getDNAString())
            self.setInfo(av.getName(), *random.choice(POSES), av.getHat(),
                         av.getBackpack(), av.getGlasses(), av.getShoes())
        self.onCoolDown = True

        def endCooldown(task):
            self.onCoolDown = False
        taskMgr.doMethodLater(USE_COOLDOWN, endCooldown, f'{self.getDoId()}-statue-cooldown')

    def setDNA(self, dna):
        """
        Sets the DNA from a net string
        Then sends it to clients

        :param dna: DNA Net String
        :type dna: bytes
        """
        self.dna = dna
        self.sendUpdate('setDNA', [dna])

    def getDNA(self):
        """
        :returns: DNA Net string
        """
        return self.dna

    def setInfo(self, name, pose, poseFrame, hat, backpack, glasses, shoes):
        """
        Sets and sends other info to clients

        :param name: The Toon's Name
        :param pose: Animation
        :param poseFrame: Frame of animation to pose
        :param backpack: Toon's Backpack
        :type name: str
        :type pose: str
        :type poseFrame: int
        :type hat: tuple[int, int, int]
        :type backpack: tuple[int, int, int]
        :type glasses: tuple[int, int, int]
        :type shoes: tuple[int, int, int]
        """
        self.info = (name, pose, poseFrame, hat, backpack, glasses, shoes)
        self.sendUpdate('setInfo', (*self.info,))

    def getInfo(self):
        """
        :return: Tuple of the name, animation, and frame to pose
        """
        return self.info
