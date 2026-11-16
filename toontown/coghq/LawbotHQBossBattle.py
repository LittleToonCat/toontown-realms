from toontown.suit import DistributedLawbotBoss, DistributedLawbotArena
from direct.directnotify import DirectNotifyGlobal
from toontown.coghq import CogHQBossBattle


class LawbotHQBossBattle(CogHQBossBattle.CogHQBossBattle):
    notify = DirectNotifyGlobal.directNotify.newCategory('LawbotHQBossBattle')

    def __init__(self, loader, parentFSM, doneEvent):
        CogHQBossBattle.CogHQBossBattle.__init__(self, loader, parentFSM, doneEvent)
        self.teleportInPosHpr = (88, -214, 0, 210, 0, 0)

    def load(self):
        CogHQBossBattle.CogHQBossBattle.load(self)

    def unload(self):
        CogHQBossBattle.CogHQBossBattle.unload(self)

    def enter(self, requestStatus):
        bossCogs = (DistributedLawbotBoss.OneBossCog, DistributedLawbotArena.OneBossCog)
        bossCog = None

        for bc in bossCogs:
            if bc:
                bossCog = bc
                break

        CogHQBossBattle.CogHQBossBattle.enter(self, requestStatus, bossCog)

        if not bossCog:
            def checkForBossCogTask(task):
                # This check doesn't work properly unless you redefine this everytime the task runs
                bossCogs = (DistributedLawbotBoss.OneBossCog, DistributedLawbotArena.OneBossCog)

                if not hasattr(task, 'counter'):
                    task.counter = 0
                taskCounterThreshold = task.counter >= 10

                for bc in bossCogs:
                    self.notify.debug('Checking bossCog result: %s' % str(bc is not None))
                    if bc:
                        nonlocal bossCog
                        bossCog = bc
                        self.setBossCog(bossCog)
                        return task.done
                if taskCounterThreshold:
                    self.notify.error('Check for bossCog failed!')
                else:
                    task.counter += 1
                    task.delayTime = 0.5
                    return task.again

            taskMgr.add(checkForBossCogTask, 'checkForBossCogTask')

    def exit(self):
        CogHQBossBattle.CogHQBossBattle.exit(self)
