from direct.directnotify import DirectNotifyGlobal

from toontown.battle import DistributedBattleAI

from toontown.toon import ToonDNA, NPCToons
from toontown.toonbase import TTLocalizer

class DistributedBattleTutorialAI(DistributedBattleAI.DistributedBattleAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedBattleTutorialAI')

    def __init__(self, air, battleMgr, pos, suit, toonId, zoneId, finishCallback=None, maxSuits=4, interactivePropTrackBonus=-1):
        """__init__(air, battleMgr, pos, suit, toonId, zoneId,
                 finishCallback, maxSuits)
        """
        DistributedBattleAI.DistributedBattleAI.__init__(self, air, battleMgr, pos, suit, toonId, zoneId, finishCallback, maxSuits, tutorialFlag=1, interactivePropTrackBonus=interactivePropTrackBonus)

    # There is no timer in the tutorial... The reward movie is random length.
    def startRewardTimer(self):
        pass

    def getTutorialNPC(self):
        npcId = 20000
        npcDesc = NPCToons.NPCToonDict.get(npcId)
        npcName = npcDesc[1]
        npcDNA = npcDesc[2]
        if npcDNA == 'r':
            npcDNA = NPCToons.getRandomDNA(npcId, npcDesc[3])
        dna = ToonDNA.ToonDNA()
        dna.newToonFromProperties(*npcDNA)
        dnaString = dna.makeNetString()

        if len(npcDesc) == 10:
            npcHat = npcDesc[6]
            npcBackpack = npcDesc[7]
            npcGlasses = npcDesc[8]
            npcShoes = npcDesc[9]
        else:
            npcHat = (0, 0, 0)
            npcBackpack = (0, 0, 0)
            npcGlasses = (0, 0, 0)
            npcShoes = (0, 0, 0)

        return [npcName, dnaString, npcHat, npcBackpack, npcGlasses, npcShoes]