from direct.directnotify.DirectNotifyGlobal import directNotify
from .DistributedMicroGameAI import DistributedMicroGameAI
from toontown.toonbase import TTLocalizer, ToontownGlobals


class DistributedPieBlitzAI(DistributedMicroGameAI):
    notify = directNotify.newCategory('DistributedPieBlitzAI')
    messages = {'start': TTLocalizer.PieBlitzStart, 'update': TTLocalizer.PieBlitzInProgress,
                'end': TTLocalizer.PieBlitzEnd}

    def __init__(self, air):
        DistributedMicroGameAI.__init__(self, air)
        self._duration = ToontownGlobals.DefaultPieBlitzDuration
        self._damage = ToontownGlobals.DefaultPieBlitzDamage
        self._pieType = ToontownGlobals.DefaultPieBlitzPie

    def delete(self):
        del self._damage
        del self._pieType
        DistributedMicroGameAI.delete(self)

    def getName(self):
        return TTLocalizer.PieBlitzTitle

    def getDamage(self):
        return self._damage

    def setDamage(self, dmg):
        self._damage = dmg

    def getPieType(self):
        return self._pieType

    def setPieType(self, ptype):
        self._pieType = ptype

    def handleAvatarEntered(self, av):
        DistributedMicroGameAI.handleAvatarEntered(self, av)
        av.b_setPieType(self._pieType)
        finishGameTask = taskMgr.mgr.findTask(self.uniqueName('finishGame'))
        if finishGameTask:
            av.b_setNumPies(abs(int(finishGameTask.time)))
        else:
            av.b_setNumPies(self._duration)

    def handleAvatarExited(self, av):
        DistributedMicroGameAI.handleAvatarExited(self, av)
        av.b_setNumPies(0)

    def enterStart(self):
        self._callFuncsOnPlayers((('b_setPieType', self._pieType), ('b_setNumPies', self._duration)))
        DistributedMicroGameAI.enterStart(self)

    def enterOff(self):
        self._callFuncOnPlayers('b_setNumPies', 0)
        DistributedMicroGameAI.enterOff(self)
