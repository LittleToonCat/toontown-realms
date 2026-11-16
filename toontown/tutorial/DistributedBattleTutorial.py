from toontown.battle import DistributedBattle
from direct.directnotify import DirectNotifyGlobal

class DistributedBattleTutorial(DistributedBattle.DistributedBattle):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedBattleTutorial')

    def startTimer(self, ts = 0):
        self.townBattle.timer.hide()

    def playReward(self, ts):
        self.movie.playTutorialReward(ts, self.getTutorialNPC(), self.uniqueName('reward'), self.handleRewardDone)

    def setTutorialNPC(self, tutorialNPC):
        self.tutorialNPC = tutorialNPC

    def getTutorialNPC(self):
        return self.tutorialNPC