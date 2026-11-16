from panda3d.core import *
from direct.interval.IntervalGlobal import *
from toontown.suit import DistributedBossbotBoss
from direct.directnotify import DirectNotifyGlobal
from toontown.coghq import CogHQBossBattle

class BossbotHQBossBattle(CogHQBossBattle.CogHQBossBattle):
    notify = DirectNotifyGlobal.directNotify.newCategory('BossbotHQBossBattle')

    def __init__(self, loader, parentFSM, doneEvent):
        CogHQBossBattle.CogHQBossBattle.__init__(self, loader, parentFSM, doneEvent)
        self.teleportInPosHpr = (88, -214, 0, 210, 0, 0)
        for stateName in ['movie']:
            state = self.fsm.getStateNamed(stateName)
            state.addTransition('crane')

        state = self.fsm.getStateNamed('finalBattle')
        state.addTransition('finalBattle')

    def load(self):
        CogHQBossBattle.CogHQBossBattle.load(self)

    def unload(self):
        CogHQBossBattle.CogHQBossBattle.unload(self)

    def enter(self, requestStatus):
        bossCog = DistributedBossbotBoss.OneBossCog
        CogHQBossBattle.CogHQBossBattle.enter(self, requestStatus, bossCog)

        if not bossCog:
            def checkForBossCogTask(task):
                # This check doesn't work properly unless you redefine this everytime the task runs
                bossCog = DistributedBossbotBoss.OneBossCog
                self.notify.debug('Checking bossCog result: %s' % str(bossCog is not None))

                if not hasattr(task, 'counter'):
                    task.counter = 0
                taskCounterThreshold = task.counter >= 10

                if taskCounterThreshold:
                    self.notify.error('Check for bossCog failed!')
                elif bossCog:
                    self.setBossCog(bossCog)
                    return task.done
                else:
                    task.counter += 1
                    task.delayTime = 0.5
                    return task.again

            taskMgr.add(checkForBossCogTask, 'checkForBossCogTask')

    def exit(self):
        CogHQBossBattle.CogHQBossBattle.exit(self)

    def exitCrane(self):
        CogHQBossBattle.CogHQBossBattle.exitCrane(self)
        messenger.send('exitCrane')
