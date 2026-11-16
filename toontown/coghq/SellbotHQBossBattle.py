from panda3d.core import *
from toontown.suit import DistributedSellbotBoss, DistributedSellbotArena
from direct.directnotify import DirectNotifyGlobal
from toontown.coghq import CogHQBossBattle


class SellbotHQBossBattle(CogHQBossBattle.CogHQBossBattle):
    notify = DirectNotifyGlobal.directNotify.newCategory('SellbotHQBossBattle')

    def __init__(self, loader, parentFSM, doneEvent):
        CogHQBossBattle.CogHQBossBattle.__init__(self, loader, parentFSM, doneEvent)
        self.teleportInPosHpr = (0, 95, 18, 180, 0, 0)

    def enter(self, requestStatus):
        bossCogs = (DistributedSellbotBoss.OneBossCog, DistributedSellbotArena.OneBossCog)
        bossCog = None

        for bc in bossCogs:
            if bc:
                bossCog = bc
                break

        CogHQBossBattle.CogHQBossBattle.enter(self, requestStatus, bossCog)
