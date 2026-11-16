from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.interval.IntervalGlobal import *
from .DistributedNPCToon import DistributedNPCToon
from . import NPCToons
from toontown.toonbase import TTLocalizer, ToontownGlobals, ClientSettings


class DistributedNPCMuseumToon(DistributedNPCToon):
    notify = directNotify.newCategory('DistributedNPCMuseumToon')

    def announceGenerate(self):
        DistributedNPCToon.announceGenerate(self)

        # Put on the special Big Cheese transformation if our position index matches
        if self.posIndex == ToontownGlobals.MuseumToonBigCheese:
            self.setMiscIndex(ToontownGlobals.TransformationMiscCheese + 1)

        # Put on the Chip transformation if our position index matches
        elif self.posIndex == ToontownGlobals.MuseumToonChip:
            self.setCharIndex(14 + 1)

        # Put on a Short Change discuise if we're Lord Lowden Clear
        elif self.posIndex == ToontownGlobals.MuseumToonLowdenClear:
            self.setCogIndex('sc', 5, 0)

        #self.setCustomIcon(text='2003', z=3)

    def getCollSphereRadius(self):
        return 4

    def handleInteraction(self, collisionEntry):
        if ClientSettings.NPCInteraction.get():
            self._DistributedNPCToonBase__createInteractHint(collisionEntry)
        else:
            self.handleCollisionSphereEnter(collisionEntry)

    def handleCollisionSphereEnter(self, collEntry):
        self.sendUpdate('avatarEnter', [])

    def handleInteract(self, avId):
        isLocalToon = avId == base.localAvatar.doId

        av = base.cr.doId2do.get(avId)
        if av is None:
            self.notify.warning('Avatar %d not found in doId' % avId)
            return

        if isLocalToon:
            self.getLockLocalToon().start()
            self.setupCamera(NPCToons.QUEST_MOVIE_INCOMPLETE)
        self.setupAvatars(av)

        fullString = TTLocalizer.MuseumToonTalk[self.posIndex]

        self.acceptOnce(self.uniqueName('doneChatPage'), self.finishMovie, extraArgs=[av, isLocalToon])
        self.clearChat()
        self.setPageChat(avId, 0, fullString, 1)
        return

    def finishMovie(self, av, isLocalToon, elapsedTime):
        self.cleanupMovie()
        av.startLookAround()
        self.startLookAround()
        self.detectAvatars()
        self.initPos()
        if isLocalToon:
            self.sendUpdate('setMovieDone', [])
            self.getFreeLocalToon().start()

    def setMovie(self, mode, npcId, avId, quests, timestamp):
        isLocalToon = avId == base.localAvatar.doId
        if mode == NPCToons.QUEST_MOVIE_CLEAR:
            self.cleanupMovie()
        if mode == NPCToons.QUEST_MOVIE_TIMEOUT:
            self.cleanupMovie()
            if isLocalToon:
                self.getFreeLocalToon().start()

    def getLockLocalToon(self):
        return Sequence(Func(base.localAvatar.detachCamera), Func(base.localAvatar.setLocked, True),
                        Func(base.localAvatar.stopTrackAnimToSpeed), Func(base.localAvatar.deactivateCamera))

    def getFreeLocalToon(self):
        return Sequence(Func(base.localAvatar.attachCamera), Func(base.localAvatar.startTrackAnimToSpeed),
                        Func(base.localAvatar.setLocked, False), Func(base.localAvatar.activateCamera))

    def setupAvatars(self, av):
        av.setZ(0)
        av.loop('neutral')
        DistributedNPCToon.setupAvatars(self, av)
