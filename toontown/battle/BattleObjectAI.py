from typing import Union
from direct.showbase.DirectObject import DirectObject
from toontown.toon.DistributedToonAI import DistributedToonAI
from toontown.suit.DistributedSuitAI import DistributedSuitAI

class BattleObjectAI(DirectObject):

    def __init__(self, battle, distObj: Union[DistributedToonAI, DistributedSuitAI]):
        DirectObject.__init__(self)
        self.battle = battle
        self.battleCalc = battle.battleCalc
        self.distObj = distObj
        self.listenForEvents()

    def listenForEvents(self):
        pass

    def destroy(self):
        self.ignoreAll()