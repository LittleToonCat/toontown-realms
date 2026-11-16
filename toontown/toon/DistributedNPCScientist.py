from direct.interval.IntervalGlobal import *
from toontown.toonbase import TTLocalizer, ToontownGlobals
from . import DistributedNPCToonBase
from panda3d.toontown import CFSpeech, CFTimeout


class DistributedNPCScientist(DistributedNPCToonBase.DistributedNPCToonBase):

    def __init__(self, cr):
        DistributedNPCToonBase.DistributedNPCToonBase.__init__(self, cr)
        self.accept('SillyMeterIsRunning', self.sillyMeterIsRunning)
        self.talkIval = None

    def disable(self):
        self.leaveDialogue()
        self.ignore('SillyMeterIsRunning')
        DistributedNPCToonBase.DistributedNPCToonBase.disable(self)

    def sillyMeterIsRunning(self, isRunning):
        if isRunning:
            self.show()
        else:
            self.hide()
            self.leaveDialogue()

    def getCollSphereRadius(self):
        return 2.5

    def initPos(self):
        self.setHpr(180, 0, 0)
        self.setScale(1.0)

    def handleCollisionSphereEnter(self, collEntry):
        self.nametag3d.setDepthTest(0)
        self.nametag3d.setBin('fixed', 0)

    def announceGenerate(self):
        DistributedNPCToonBase.DistributedNPCToonBase.announceGenerate(self)
        if base.cr.newsManager.isHolidayRunning(ToontownGlobals.SILLYMETER_HOLIDAY) or base.cr.newsManager.isHolidayRunning(ToontownGlobals.SILLYMETER_EXT_HOLIDAY):
            self.show()
        else:
            self.hide()

    def generateToon(self):
        self.setLODs()
        self.generateToonLegs()
        self.generateToonHead()
        self.generateToonTorso()
        self.generateToonColor()
        self.parentToonParts()
        self.rescaleToon()
        self.resetHeight()
        self.rightHands = []
        self.leftHands = []
        self.headParts = []
        self.hipsParts = []
        self.torsoParts = []
        self.legsParts = []
        self.__bookActors = []
        self.__holeActors = []
        self.setupToonNodes()
        if self.style.getTorsoSize() == 'short' and self.style.getAnimal() == 'duck':
            sillyReader = loader.loadModel('phase_4/models/props/tt_m_prp_acs_sillyReader')
            for rHand in self.getRightHands():
                placeholder = rHand.attachNewNode('SillyReader')
                sillyReader.instanceTo(placeholder)
                placeholder.setH(180)
                placeholder.setScale(render, 1.0)
                placeholder.setPos(0, 0, 0.1)

        elif self.style.getTorsoSize() == 'long' and self.style.getAnimal() == 'monkey' or self.style.getTorsoSize() == 'medium' and self.style.getAnimal() == 'horse':
            clipBoard = loader.loadModel('phase_4/models/props/tt_m_prp_acs_clipboard')
            for rHand in self.getRightHands():
                placeholder = rHand.attachNewNode('ClipBoard')
                clipBoard.instanceTo(placeholder)
                placeholder.setH(180)
                placeholder.setScale(render, 1.0)
                placeholder.setPos(0, 0, 0.1)

    def startLookAround(self):
        pass

    def scientistPlay(self):
        if self.style.getTorsoSize() == 'short' and self.style.getAnimal() == 'duck':
            sillyReaders = self.findAllMatches('**/SillyReader')
            for sillyReader in sillyReaders:
                if not sillyReader.isEmpty():
                    sillyReader.stash()

        elif self.style.getTorsoSize() == 'long' and self.style.getAnimal() == 'monkey':
            clipBoards = self.findAllMatches('**/ClipBoard')
            for clipBoard in clipBoards:
                if not clipBoard.isEmpty():
                    clipBoard.stash()

    def showScientistProp(self):
        if self.style.getTorsoSize() == 'short' and self.style.getAnimal() == 'duck':
            sillyReaders = self.findAllMatches('**/SillyReader;+s')
            for sillyReader in sillyReaders:
                if not sillyReader.isEmpty():
                    sillyReader.unstash()

        elif self.style.getTorsoSize() == 'long' and self.style.getAnimal() == 'monkey':
            clipBoards = self.findAllMatches('**/ClipBoard;+s')
            for clipBoard in clipBoards:
                if not clipBoard.isEmpty():
                    clipBoard.unstash()

    def requestDialogue(self, topic, endPause, npcId):
        self.talkIval = Sequence()
        phrases = TTLocalizer.toontownDialogues.get(topic.decode("utf-8")).get((self.posIndex, npcId))
        if phrases:
            for phrase in phrases:
                # Gonna have to manually remove the phrases if we want to replicate TTO behavior accurately
                # This timing is taken from libotp's NametagGroup
                timeout = max(min(12.0, len(phrase) * 0.5), 4.0)
                self.talkIval.append(Sequence(Func(self.setChatAbsolute, phrase, CFSpeech),
                                              Wait(timeout), Func(self.clearChat)))

            self.talkIval.append(Wait(endPause))

            self.talkIval.loop()

    def leaveDialogue(self):
        self.clearChat()
        if self.talkIval:
            self.talkIval.clearToInitial()
