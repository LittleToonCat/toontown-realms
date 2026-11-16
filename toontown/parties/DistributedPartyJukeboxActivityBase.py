from direct.actor.Actor import Actor
from direct.gui.OnscreenText import OnscreenText
from direct.task.Task import Task
from direct.distributed.ClockDelta import globalClockDelta
from direct.gui.DirectGui import DGG

from panda3d.core import *

from otp.otpbase.PythonUtil import bound
from toontown.toonbase import ToontownGlobals, ClientSettings, HotkeySettings, ControlManager
from toontown.toonbase import TTLocalizer
from toontown.parties.DistributedPartyActivity import DistributedPartyActivity
from toontown.parties.PartyGlobals import ActivityTypes, JUKEBOX_TIMEOUT
from toontown.parties.PartyGlobals import getMusicRepeatTimes, MUSIC_PATH, sanitizePhase
from toontown.parties.JukeboxGui import JukeboxGui


class DistributedPartyJukeboxActivityBase(DistributedPartyActivity):
    notify = directNotify.newCategory('DistributedPartyJukeboxActivityBase')

    def __init__(self, cr, actId, phaseToMusicData):
        DistributedPartyActivity.__init__(self, cr, actId, ActivityTypes.Continuous)
        self.phaseToMusicData = phaseToMusicData
        self.jukebox = None
        self.gui = None
        self.tunes = []
        self.music = None
        self.currentSongData = None
        self.localQueuedSongInfo = None
        self.localQueuedSongListItem = None
        self.loop = False
        self.timestamp = None

    def generateInit(self):
        self.gui = JukeboxGui(self.phaseToMusicData)

    def announceGenerate(self):
        DistributedPartyActivity.announceGenerate(self)

        def startMusic():
            if self.music:
                if self._checkPartyValidity() and hasattr(base.cr.playGame.getPlace().loader, 'music') and base.cr.playGame.getPlace().loader.music:
                    base.cr.playGame.getPlace().loader.music.stop()
                    if self.timestamp:
                        ts = globalClockDelta.localElapsedTime(self.timestamp)
                        self.music.setTime(ts)
                    self.music.play()

        # Continue music if audioManager is re-enabled
        self.accept('MusicEnabled', startMusic)
        # or if restored from minimize
        self.accept('PandaRestarted', startMusic)

    def disable(self):
        self.ignore('MusicEnabled')
        self.ignore('PandaRestarted')
        DistributedPartyActivity.disable(self)

    def load(self):
        DistributedPartyActivity.load(self)
        self.jukebox = Actor('phase_13/models/parties/jukebox_model', {'dance': 'phase_13/models/parties/jukebox_dance'})
        self.jukebox.reparentTo(self.root)
        self.jukebox.setBlend(frameBlend=ClientSettings.SmoothAnimations.get())
        self.collNode = CollisionNode(self.getCollisionName())
        self.collNode.setCollideMask(ToontownGlobals.CameraBitmask | ToontownGlobals.WallBitmask)
        collTube = CollisionTube(0, 0, 0, 0.0, 0.0, 4.25, 2.25)
        collTube.setTangible(1)
        self.collNode.addSolid(collTube)
        self.collNodePath = self.jukebox.attachNewNode(self.collNode)
        self.sign.setPos(-5.0, 0, 0)
        self.activate()

    def unload(self):
        DistributedPartyActivity.unload(self)
        self.gui.unload()
        if self.music is not None:
            self.music.stop()
            self.music = None
        self.jukebox.stop()
        self.jukebox.delete()
        self.jukebox = None
        self.ignoreAll()
        return

    def getCollisionName(self):
        return self.uniqueName('jukeboxCollision')

    def activate(self):
        self.accept('enter' + self.getCollisionName(), self.__handleEnterCollision)

    def __handleEnterCollision(self, collisionEntry):
        if base.cr.playGame.getPlace().fsm.getCurrentState().getName() == 'walk':
            if ClientSettings.ActivityInteraction.get():
                self.__createInteractHint()
            else:
                self.__interact()

    def __handleExitCollision(self, collisionEntry = None):
        self.ignore('exit' + self.getCollisionName())
        self.__destroyInteractHint()

    def __interact(self):
        base.cr.playGame.getPlace().fsm.request('activity')
        self.d_toonJoinRequest()

    def joinRequestDenied(self, reason):
        DistributedPartyActivity.joinRequestDenied(self, reason)
        self.showMessage(TTLocalizer.PartyJukeboxOccupied)

    def handleToonJoined(self, toonId):
        toon = base.cr.doId2do.get(toonId)
        if toon:
            self.jukebox.lookAt(base.cr.doId2do[toonId])
            self.jukebox.setHpr(self.jukebox.getH() + 180.0, 0, 0)
        if toonId == base.localAvatar.doId:
            self.__localUseJukebox()

    def handleToonExited(self, toonId):
        if toonId == base.localAvatar.doId and self.gui.isLoaded():
            self.__deactivateGui()

    def handleToonDisabled(self, toonId):
        self.notify.warning('handleToonDisabled no implementation yet')

    def __localUseJukebox(self):
        base.localAvatar.disableAvatarControls()
        base.localAvatar.stopPosHprBroadcast()
        self.__activateGui()
        self.accept(JukeboxGui.CLOSE_EVENT, self.__handleGuiClose)
        taskMgr.doMethodLater(0.5, self.__localToonWillExitTask, self.uniqueName('toonWillExitJukeboxOnTimeout'), extraArgs=None)
        self.accept(JukeboxGui.ADD_SONG_CLICK_EVENT, self.__handleQueueSong)
        if self.isUserHost():
            self.accept(JukeboxGui.MOVE_TO_TOP_CLICK_EVENT, self.__handleMoveSongToTop)
            self.accept(JukeboxGui.LOOP_EVENT, self.__handleRequestLoop)
        else:
            self.gui._loopButton['state'] = DGG.DISABLED
            self.gui._loopButton.setColorScale(0.5, 0.5, 0.5, 1.0)
        return

    def __localToonWillExitTask(self, task):
        self.localToonExiting()
        return Task.done

    def __activateGui(self):
        self.gui.enable(timer=JUKEBOX_TIMEOUT)
        self.gui.disableAddSongButton()
        if self.currentSongData is not None:
            self.gui.setSongCurrentlyPlaying(self.currentSongData[0], self.currentSongData[1])
        if self.loop:
            self.gui._loopButton.setText(TTLocalizer.JukeboxUnloop)
        else:
            self.gui._loopButton.setText(TTLocalizer.JukeboxLoop)
        self.d_queuedSongsRequest()
        return

    def __deactivateGui(self):
        self.ignore(JukeboxGui.CLOSE_EVENT)
        self.ignore(JukeboxGui.LOOP_EVENT)
        self.ignore(JukeboxGui.SONG_SELECT_EVENT)
        self.ignore(JukeboxGui.MOVE_TO_TOP_CLICK_EVENT)
        base.cr.playGame.getPlace().setState('walk')
        base.localAvatar.startPosHprBroadcast(period = ClientSettings.PositionSendRate.get())
        base.localAvatar.enableAvatarControls()
        self.gui.unload()
        self.__localClearQueuedSong()

    def isUserHost(self):
        return self.party.partyInfo.hostId == base.localAvatar.doId

    def d_queuedSongsRequest(self):
        self.sendUpdate('queuedSongsRequest')

    def queuedSongsResponse(self, songInfoList, index):
        if self.gui.isLoaded():
            for i in range(len(songInfoList)):
                songInfo = songInfoList[i]
                self.__addSongToQueue(songInfo, isLocalQueue=index >= 0 and i == index)

            self.gui.enableAddSongButton()

    def __handleGuiClose(self):
        self.__deactivateGui()
        self.d_toonExitDemand()

    def __handleQueueSong(self, name, values):
        self.d_setNextSong(values[0], values[1])

    def d_setNextSong(self, phase, filename):
        self.sendUpdate('setNextSong', [(phase, filename)])

    def setSongInQueue(self, songInfo):
        if self.gui.isLoaded():
            phase = sanitizePhase(songInfo[0])
            filename = songInfo[1]
            data = self.getMusicData(phase, filename)
            if data:
                if self.localQueuedSongListItem is not None:
                    self.localQueuedSongListItem['text'] = data[0]
                else:
                    self.__addSongToQueue(songInfo, isLocalQueue=True)
        return

    def __addSongToQueue(self, songInfo, isLocalQueue = False):
        isHost = isLocalQueue and self.isUserHost()
        data = self.getMusicData(sanitizePhase(songInfo[0]), songInfo[1])
        if data:
            listItem = self.gui.addSongToQueue(data[0], highlight=isLocalQueue, moveToTopButton=isHost)
            if isLocalQueue:
                self.localQueuedSongInfo = songInfo
                self.localQueuedSongListItem = listItem

    def __localClearQueuedSong(self):
        self.localQueuedSongInfo = None
        self.localQueuedSongListItem = None
        return

    def __handleRequestLoop(self):
        self.d_requestLoop()

    def d_requestLoop(self):
        self.sendUpdate('requestLoop', [])

    def setLoop(self, state):
        self.loop = state

        if hasattr(self, 'gui') and self.gui and hasattr(self.gui, '_loopButton') and self.gui._loopButton:
            if self.loop:
                self.gui._loopButton.setText(TTLocalizer.JukeboxUnloop)
            else:
                self.gui._loopButton.setText(TTLocalizer.JukeboxLoop)

    def _play(self, phase, filename, length, timestamp):
        self.music = base.loader.loadMusic((MUSIC_PATH + '%s') % (phase, filename))
        self.timestamp = timestamp
        if self.music:
            if self._checkPartyValidity() and hasattr(base.cr.playGame.getPlace().loader, 'music') and base.cr.playGame.getPlace().loader.music:
                base.cr.playGame.getPlace().loader.music.stop()
            ts = globalClockDelta.localElapsedTime(timestamp)
            self.music.setTime(ts)
            self.music.setLoopCount(getMusicRepeatTimes(length))
            self.music.play()
            jukeboxAnimControl = self.jukebox.getAnimControl('dance')
            if not jukeboxAnimControl.isPlaying():
                self.jukebox.loop('dance', fromFrame=0, toFrame=48)
            self.currentSongData = (phase, filename)

    def __stop(self):
        self.jukebox.stop()
        self.currentSongData = None
        if self.music:
            self.music.stop()
            self.music = None
        if self.gui.isLoaded():
            self.gui.clearSongCurrentlyPlaying()
        return

    def setSongPlaying(self, songInfo, toonId, timestamp, forceRemoval=False):
        phase = sanitizePhase(songInfo[0])
        filename = songInfo[1]
        if not filename:
            self.__stop()
            return
        data = self.getMusicData(phase, filename)
        if data:
            self._play(phase, filename, data[1], timestamp)
            self.setSignNote(data[0])
            if self.gui.isLoaded() and (not self.loop or forceRemoval):
                item = self.gui.popSongFromQueue()
                self.gui.setSongCurrentlyPlaying(phase, filename)
                if item == self.localQueuedSongListItem:
                    self.__localClearQueuedSong()
        if toonId == localAvatar.doId:
            localAvatar.setSystemMessage(0, TTLocalizer.PartyJukeboxNowPlaying)

    def __handleMoveSongToTop(self):
        if self.isUserHost() and self.localQueuedSongListItem is not None:
            self.d_moveHostSongToTopRequest()
        return

    def d_moveHostSongToTopRequest(self):
        self.notify.debug('d_moveHostSongToTopRequest')
        self.sendUpdate('moveHostSongToTopRequest')

    def moveHostSongToTop(self):
        self.notify.debug('moveHostSongToTop')
        if self.gui.isLoaded():
            self.gui.pushQueuedItemToTop(self.localQueuedSongListItem)

    def getMusicData(self, phase, filename):
        data = []
        phase = sanitizePhase(phase)
        phase = self.phaseToMusicData.get(phase)
        if phase:
            data = phase.get(filename, [])
        return data

    def _checkPartyValidity(self):
        return hasattr(base.cr.playGame, 'getPlace') and base.cr.playGame.getPlace() and hasattr(base.cr.playGame.getPlace(), 'loader') and base.cr.playGame.getPlace().loader

    def __createInteractHint(self):
        if not hasattr(self, "interactHint"):
            self.accept(HotkeySettings.Interact.getPressed(),
                        self.__interact)
            self.accept('exit' + self.getCollisionName(), self.__handleExitCollision)
            self.accept('toonExitWalk', self.__handleExitCollision)

            text: str = ControlManager.ControlManager.parseHotkeyString(TTLocalizer.ActivityInteractJukebox, useGlyphs=True)
            self.interactHint = OnscreenText(
                    text,
                    style = 3, scale = .065,
                    parent = base.a2dBottomCenter,
                    font = ToontownGlobals.getFancyFont(),
                    fg = (0.74, 0.47, 1.0, 1.0),
                    pos = (0.0, 0.0))

            taskMgr.add(self.__alignInteractHint, self.alignInteractHintTaskName)

    def __destroyInteractHint(self):
        self.ignore(HotkeySettings.Interact.getPressed())
        self.ignore('toonExitWalk')
        # Remove interact hint
        if hasattr(self, "interactHint"):
            taskMgr.remove(self.alignInteractHintTaskName)
            self.interactHint.removeNode()
            del self.interactHint

    def __alignInteractHint(self, task):
        """
        Aligns the interact hint on the screen
        The hint should be positioned on the npc, then the position is projected to the aspect2d
        """
        if hasattr(self, 'interactHint'):
            center = base.cam.getRelativePoint(self.jukebox, Point3(0, 0, 2))

            if base.camNode.isInView(center):
                center2d = Point2()
                base.camLens.project(center, center2d)

                center2d.x = bound(center2d.x, -0.7, 0.7)
                center2d.y = bound(center2d.y, -0.9, 0.95)
            else:
                # If the point isnt in the view, we set it to the 'default' position
                center2d = Point2(0.0, -0.45)

            self.interactHint.set_pos(render2d, Point3(center2d.x, 0, center2d.y))

        return task.cont

    @property
    def alignInteractHintTaskName(self):
        return f'alignInteractHint-{self.getDoId()}'
