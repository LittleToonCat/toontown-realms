from direct.fsm import ClassicFSM
from direct.fsm.State import State

from toontown.classicchars.DistributedCCharBase import DistributedCCharBase
from toontown.classicchars.DistributedDonald import DistributedDonald
from toontown.toonbase import TTLocalizer, ToontownGlobals


class DistributedDonaldDreamDay(DistributedDonald):

    def __init__(self, cr):
        super(DistributedDonald, self).__init__(cr, TTLocalizer.DonaldDreamDay, 'ddl')
        self.fsm = ClassicFSM.ClassicFSM(
                self.getName(),
                [
                    State('Off', self.enterOff, self.exitOff, ['Neutral']),
                    State('Neutral', self.enterNeutral, self.exitNeutral, ['Walk']),
                    State('Walk', self.enterWalk, self.exitWalk, ['Neutral'])
                ],
                'Off', 'Off')
        self.fsm.enterInitialState()
        self.nametag.setName(TTLocalizer.Donald)

    def generate(self):
        super().generate()

    def walkSpeed(self):
        return ToontownGlobals.BetaDonaldSpeed

