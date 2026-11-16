from toontown.battle.BattleObjectAI import *

class BattleToonAI(BattleObjectAI):

    def __init__(self, battle, distObj: DistributedToonAI):
        BattleObjectAI.__init__(self, battle, distObj)