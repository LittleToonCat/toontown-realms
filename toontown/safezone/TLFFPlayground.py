import random

from panda3d.core import *
from toontown.toonbase import ToontownGlobals
from . import Playground
from toontown.launcher import DownloadForceAcknowledge
from toontown.building import Elevator
from toontown.toontowngui import TTDialog
from toontown.toonbase import TTLocalizer
from toontown.racing import RaceGlobals
from direct.fsm import State
from toontown.safezone import PicnicBasket
from toontown.safezone import GolfKart
from direct.task.Task import Task

class TLFFPlayground(Playground.Playground):
    def __init__(self, loader, parentFSM, doneEvent):
        super().__init__(loader, parentFSM, doneEvent)
        self.parentFSM = parentFSM
        self.picnicBasketBlockDoneEvent = 'picnicBasketBlockDone'
        self.fsm.addState(State.State('picnicBasketBlock', self.enterPicnicBasketBlock, self.exitPicnicBasketBlock, ['walk']))
        state = self.fsm.getStateNamed('walk')
        state.addTransition('picnicBasketBlock')
        self.picnicBasketDoneEvent = 'picnicBasketDone'

    def load(self):
        super().load()

    def unload(self):
        super().unload()

    def enter(self, requestStatus):
        super().enter(requestStatus)
        #self.doMethodLater(1, self.__birds, 'tlffbirds')

    def exit(self):
        #self.removeTask('tlffbirds')
        super().exit()

    def enterDFA(self, requestStatus):
        doneEvent = 'dfaDoneEvent'
        self.accept(doneEvent, self.enterDFACallback, [requestStatus])
        self.dfa = DownloadForceAcknowledge.DownloadForceAcknowledge(doneEvent)
        if requestStatus['hoodId'] == ToontownGlobals.MyEstate:
            self.dfa.enter(base.cr.hoodMgr.getPhaseFromHood(ToontownGlobals.MyEstate))
        else:
            self.dfa.enter(5)

    def __cleanupDialog(self, value):
        if self.dialog:
            self.dialog.cleanup()
            self.dialog = None
        if hasattr(self, 'fsm'):
            self.fsm.request('walk', [1])
        return

    def createPicnic(self, picnicBasket):
        self.accept(self.picnicBasketDoneEvent, self.handlePicnicBasketDone)
        place = base.cr.playGame.getPlace()

        if not hasattr(place, 'picnic') or not place.picnic:
            place.picnic = PicnicBasket.PicnicBasket(place, place.fsm, self.picnicBasketDoneEvent,
                                                     picnicBasket.getDoId(), picnicBasket.seatNumber)
            place.picnic.load()
            place.picnic.enter()

    def enterPicnicBasketBlock(self, picnicBasket):
        base.localAvatar.laffMeter.start()
        base.localAvatar.b_setAnimState('off', 1)
        self.createPicnic(picnicBasket)

    def exitPicnicBasketBlock(self):
        base.localAvatar.laffMeter.stop()
        self.ignore(self.picnicBasketDoneEvent)
        place = base.cr.playGame.getPlace()
        if hasattr(place, 'picnic') and place.picnic:
            place.picnic.unload()
            place.picnic.exit()

        place.picnic = None

    def detectedPicnicTableSphereCollision(self, picnicBasket):
        if self.fsm.getCurrentState().getName() != 'picnicBasketBlock':
            self.fsm.request('picnicBasketBlock', [picnicBasket])

    def handlePicnicBasketDone(self, doneStatus):
        self.notify.debug('handling picnic basket done event')
        mode = doneStatus['mode']
        if mode == 'reject':
            self.fsm.request('walk')
        elif mode == 'exit':
            self.fsm.request('walk')
        else:
            self.notify.error('Unknown mode: ' + mode + ' in handlePicnicBasketDone')

    def showPaths(self):
        from toontown.classicchars import CCharPaths
        from toontown.toonbase import TTLocalizer
        self.showPathPoints(CCharPaths.getPaths(TTLocalizer.Chip))

    def __birds(self, task):
        if hasattr(self.loader, 'birdSound'):
            base.playSfx(random.choice(self.loader.birdSound))
            t = ((random.random() * 20.0) + 1)
            self.doMethodLater(t, self.__birds, 'tlffbird')
        return task.done