from panda3d.core import CollisionNode, CollisionSphere, NodePath
from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObjectAI
from toontown.toonbase import ToontownGlobals
from direct.fsm import FSM
import random


class DistributedLawbotChairAI(DistributedObjectAI.DistributedObjectAI, FSM.FSM):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedLawbotChairAI')

    def __init__(self, air, boss, index):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        FSM.FSM.__init__(self, 'DistributedLawbotChairAI')
        self.boss = boss
        self.index = index
        cn = CollisionNode('controls')
        cs = CollisionSphere(0, -6, 0, 6)
        cn.addSolid(cs)
        self.goonShield = NodePath(cn)
        self.goonShield.setPosHpr(*ToontownGlobals.LawbotBossChairPosHprs[self.index])
        self.avId = 0
        self.objectId = 0
        self.changeToCogTask = None
        self.startCogFlyTask = None
        self.toonJurorIndex = -1

    def delete(self):
        self.ignoreAll()
        FSM.FSM.cleanup(self)
        self.stopCogs()
        DistributedObjectAI.DistributedObjectAI.delete(self)

    def stopCogs(self):
        taskName = self.uniqueName('startCogFlyTask')
        taskMgr.remove(taskName)
        changeTaskName = self.uniqueName('changeToCogJuror')
        taskMgr.remove(changeTaskName)

    def getBossCogId(self):
        return self.boss.doId

    def getIndex(self):
        return self.index

    def getToonJurorIndex(self):
        return self.toonJurorIndex

    def setToonJurorIndex(self, newVal):
        self.toonJurorIndex = newVal

    def b_setToonJurorIndex(self, newVal):
        self.setToonJurorIndex(newVal)
        self.d_setToonJurorIndex(newVal)

    def d_setToonJurorIndex(self, newVal):
        self.sendUpdate('setToonJurorIndex', [newVal])

    def setState(self, state):
        self.request(state)

    def d_setState(self, state):
        newState = state
        if state == 'On':
            newState = 'N'
        elif state == 'ToonJuror':
            newState = 'T'
        elif state == 'SuitJuror':
            newState = 'S'
        elif state == 'EmptyJuror':
            newState = 'E'
        self.sendUpdate('setState', [newState])

    def b_setState(self, state):
        self.request(state)
        self.d_setState(state)

    def requestToonJuror(self):
        self.b_setState('ToonJuror')
        if not self.changeToCogTask:
            if not self.startCogFlyTask:
                if self.boss.hardcore:
                    lowerEnd = 5
                    higherEnd = 9
                elif self.air.nerfsMode:
                    lowerEnd = 39
                    higherEnd = 79
                else:
                    lowerEnd = 9
                    higherEnd = 19
                delayTime = random.randrange(lowerEnd, higherEnd)
                self.startCogFlyTask = taskMgr.doMethodLater(delayTime, self.cogFlyAndSit,
                                                             self.uniqueName('startCogFlyTask'))

    def requestSuitJuror(self):
        self.b_setState('SuitJuror')

    def requestEmptyJuror(self):
        self.b_setState('EmptyJuror')
        delayTime = random.randrange(1, 20)
        self.startCogFlyTask = taskMgr.doMethodLater(delayTime, self.cogFlyAndSit, self.uniqueName('startCogFlyTask'))

    def cogFlyAndSit(self, task):
        self.notify.debug('cogFlyAndSit')
        self.sendUpdate('showCogJurorFlying', [])
        self.changeToCogTask = taskMgr.doMethodLater(ToontownGlobals.LawbotBossCogJurorFlightTime, self.changeToCogJuror, self.uniqueName('changeToCogJuror'))
        if self.startCogFlyTask:
            self.startCogFlyTask = None
        return task.done

    def changeToCogJuror(self, task):
        self.notify.debug('changeToCogJuror')
        self.requestSuitJuror()
        self.changeToCogTask = None
        return task.done

    def enterOn(self):
        pass

    def exitOn(self):
        pass

    def enterOff(self):
        self.goonShield.removeNode()

    def exitOff(self):
        pass

    def enterToonJuror(self):
        pass

    def exitToonJuror(self):
        pass
