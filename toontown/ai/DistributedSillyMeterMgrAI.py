from direct.directnotify import DirectNotifyGlobal
from toontown.ai.DistributedPhaseEventMgrAI import DistributedPhaseEventMgrAI
from otp.ai.AIBase import *


class DistributedSillyMeterMgrAI(DistributedPhaseEventMgrAI):
    notify = DirectNotifyGlobal.directNotify.newCategory("DistributedSillyMeterMgrAI")

    def __init__(self, air, isRunning, numPhases, curPhase, holidayDates):
        DistributedPhaseEventMgrAI.__init__(self, air, isRunning, numPhases, curPhase, holidayDates)
        air.SillyMeterMgr = self

    def setCurPhase(self, curPhrase):
        DistributedPhaseEventMgrAI.setCurPhase(self, curPhrase)
        messenger.send('SillyMeterPhase', [curPhrase])
