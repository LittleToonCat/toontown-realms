from panda3d.core import *
from direct.fsm.FSM import FSM
from direct.showbase import PythonUtil
from direct.interval.MetaInterval import Sequence
from toontown.parties.PartyGlobals import DanceReverseLoopAnims, ToonDancingStates

class PartyDanceActivityToonFSM(FSM):
    notify = directNotify.newCategory('PartyDanceActivityToonFSM')

    def __init__(self, avId, activity, h):
        FSM.__init__(self, self.__class__.__name__)
        self.notify.debug('init : avId = %s, activity = %s ' % (avId, activity))
        self.avId = avId
        self.activity = activity
        self.isLocal = avId == base.localAvatar.doId
        self.toon = self.activity.getAvatar(self.avId)
        self.danceMoveSequence = None
        self.lastAnim = None
        self.defaultTransitions = {'DanceMove': ['Run', 'DanceMove'],
         'Run': ['Run', 'DanceMove']}
        return

    def destroy(self):
        self.toon = None
        self.activity = None
        self.avId = None
        return

    def enterDanceMove(self, anim = ''):
        if not self.lastAnim and anim == '':
            self.toon.loop('victory', fromFrame=98, toFrame=122)
        else:
            if anim == '':
                anim = self.lastAnim
            if anim in DanceReverseLoopAnims:
                self.danceMoveSequence = Sequence(self.toon.actorInterval(anim, loop=0), self.toon.actorInterval(anim, loop=0, playRate=-1.0))
                self.danceMoveSequence.loop()
            else:
                self.toon.loop(anim)
            self.lastAnim = anim
        return

    def exitDanceMove(self):
        if self.danceMoveSequence and self.danceMoveSequence.isPlaying():
            self.danceMoveSequence.finish()
            self.danceMoveSequence = None
        return

    def enterRun(self, *args):
        if self.toon.getCurrentAnim() != 'run':
            self.toon.loop('run')

    def exitRun(self):
        pass
