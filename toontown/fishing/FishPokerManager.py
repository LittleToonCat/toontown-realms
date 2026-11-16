from direct.distributed.DistributedObject import DistributedObject
from direct.directnotify.DirectNotifyGlobal import directNotify
from .FishPokerGui import FishPokerGui


class FishPokerManager(DistributedObject):
    neverDisable = 1
    notify = directNotify.newCategory('DistributedFishPokerManager')

    def __init__(self, cr):
        DistributedObject.__init__(self, cr)
        self.gui = None

    def disable(self):
        self.exitFishing()
        DistributedObject.disable(self)

    def __lockCallback(self, index, lockStatus):
        self.notify.debug('lockStatus %d %d' % (index, lockStatus))

    def __cashInCallback(self, value):
        if self.gui:
            self.notify.debug('cashed in %d' % value)
            self.sendUpdate('cashIn', [value])

    def enterFishing(self):
        place = base.cr.playGame.getPlace()
        if place and place.getState() == 'fishing':
            self.gui = FishPokerGui(self.__lockCallback, self.__cashInCallback)

    def caughtSomething(self, genus, species, weight):
        if self.gui:
            self.gui.drawCard(genus, species, weight)

    def exitFishing(self):
        if self.gui:
            self.gui.destroy()
