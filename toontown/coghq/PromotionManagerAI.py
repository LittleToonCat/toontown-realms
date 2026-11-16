from direct.directnotify import DirectNotifyGlobal
import random
from toontown.suit import SuitDNA
from . import CogDisguiseGlobals
from toontown.toonbase.ToontownBattleGlobals import getInvasionMultiplier
from toontown.toonbase.ToontownGlobals import ZonesNoVirtualCogCredit
from functools import reduce

from ..toonbase import ServerSettings

MeritMultiplier = 0.5


class PromotionManagerAI:
    notify = DirectNotifyGlobal.directNotify.newCategory('PromotionManagerAI')

    def __init__(self, air):
        self.air = air

    def getPercentChance(self):
        return 100.0

    def recoverMerits(self, av, cogList, zoneId, multiplier = 1, extraMerits = None):
        avId = av.getDoId()
        meritsRecovered = [0, 0, 0, 0]
        if extraMerits is None:
            extraMerits = [0, 0, 0, 0]
        if self.air.suitInvasionManager.getInvading():
            multiplier *= getInvasionMultiplier()
        multiplier *= ServerSettings.MeritMultiplier.get()
        for i in range(len(extraMerits)):
            if CogDisguiseGlobals.isSuitComplete(av.getCogParts(), i):
                meritsRecovered[i] += extraMerits[i]
                self.notify.debug('recoverMerits: extra merits = %s' % extraMerits[i])

        self.notify.debug('recoverMerits: multiplier = %s' % multiplier)
        for cogDict in cogList:
            dept = SuitDNA.suitDepts.index(cogDict['track'])
            if avId in cogDict['activeToons']:
                if CogDisguiseGlobals.isSuitComplete(av.getCogParts(), SuitDNA.suitDepts.index(cogDict['track'])):
                    self.notify.debug('recoverMerits: checking against cogDict: %s' % cogDict)
                    if cogDict['isVirtual'] and zoneId in ZonesNoVirtualCogCredit:
                        self.notify.debug('recoverMerits: virtual cog!')
                        continue
                    rand = random.random() * 100
                    if rand <= self.getPercentChance():
                        merits = cogDict['level'] * MeritMultiplier
                        merits = int(round(merits))
                        if cogDict['hasRevives']:
                            merits *= 2
                        merits = merits * multiplier
                        merits = int(round(merits))
                        meritsRecovered[dept] += merits
                        if meritsRecovered[dept] > 23300:
                            meritsRecovered[dept] = 23300
                            self.notify.debug('recoverMerits: merits = %s (tried to recover more than allowed value of 23300, defaulting to 23300' % merits)
                        else:
                            self.notify.debug('recoverMerits: merits = %s' % merits)

        if meritsRecovered != [0, 0, 0, 0]:
            actualCounted = [0, 0, 0, 0]
            merits = av.getCogMerits()
            for i in range(len(meritsRecovered)):
                maxMerits = CogDisguiseGlobals.getTotalMerits(av, i)
                if maxMerits:
                    if merits[i] + meritsRecovered[i] <= maxMerits:
                        actualCounted[i] = meritsRecovered[i]
                        merits[i] += meritsRecovered[i]
                    else:
                        actualCounted[i] = maxMerits - merits[i]
                        merits[i] = maxMerits
                    av.b_setCogMerits(merits)

            if reduce(lambda x, y: x + y, actualCounted):
                self.air.writeServerEvent('merits', avId, '%s|%s|%s|%s' % tuple(actualCounted))
                self.notify.debug('recoverMerits: av %s recovered merits %s' % (avId, actualCounted))
        return meritsRecovered
