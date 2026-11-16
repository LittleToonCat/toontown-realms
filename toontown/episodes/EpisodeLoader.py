from direct.directnotify import DirectNotifyGlobal
from direct.fsm import StateData
from direct.fsm import ClassicFSM, State

from otp.otpbase.PythonUtil import uniqueName

from toontown.hood import QuietZoneState
from toontown.town import TownBattle
from toontown.suit import Suit
from panda3d.core import *
from toontown.episodes import EpisodeConfig
from toontown.episodes import EpisodeZone


class EpisodeLoader(StateData.StateData):
    notify = DirectNotifyGlobal.directNotify.newCategory('EpisodeLoader')

    def __init__(self, hood, parentFSMState, doneEvent):
        StateData.StateData.__init__(self, doneEvent)
        self.hood = hood
        self.parentFSMState = parentFSMState
        self.placeDoneEvent = 'episodeLoaderPlaceDone'
        self.townBattleDoneEvent = 'town-battle-done'
        self.fsm = ClassicFSM.ClassicFSM('EpisodeLoader', [State.State('start', None, None, ['quietZone', 'episodeZone']),
         State.State('episodeZone', self.enterEpisodeZone, self.exitEpisodeZone, ['quietZone']),
         State.State('quietZone', self.enterQuietZone, self.exitQuietZone, ['episodeZone']),
         State.State('final', None, None, ['start'])], 'start', 'final')
        return

    def load(self, zoneId):
        self.parentFSMState.addChild(self.fsm)
        self.musicFile = EpisodeConfig.EPISODES.get(base.cr.episodeManager.episode).get('zone2Music').get(base.cr.episodeManager.episodeZoneId)
        if self.musicFile != '':
            self.music = base.loader.loadMusic(self.musicFile)
        else:
            self.music = None
        self.battleMusic = base.loader.loadMusic('phase_9/audio/bgm/encntr_suit_winning.ogg')
        self.townBattle = TownBattle.TownBattle(self.townBattleDoneEvent)
        self.townBattle.load()
        Suit.loadSuits()

    def unload(self):
        self.parentFSMState.removeChild(self.fsm)
        del self.parentFSMState
        del self.fsm
        self.townBattle.unload()
        self.townBattle.cleanup()
        del self.townBattle
        del self.battleMusic
        if self.music is not None:
            self.music.stop()
            del self.music
        Suit.unloadSuits()
        Suit.unloadSkelDialog()
        del self.hood
        ModelPool.garbageCollect()
        TexturePool.garbageCollect()

    def enter(self, requestStatus):
        self.fsm.enterInitialState()
        self.fsm.request(requestStatus['where'], [requestStatus])

    def exit(self):
        self.ignoreAll()

    def enterQuietZone(self, requestStatus):
        self.quietZoneDoneEvent = uniqueName('quietZoneDone')
        self.acceptOnce(self.quietZoneDoneEvent, self.handleQuietZoneDone)
        self.quietZoneStateData = QuietZoneState.QuietZoneState(self.quietZoneDoneEvent)
        self.quietZoneStateData.load()
        self.quietZoneStateData.enter(requestStatus)

    def exitQuietZone(self):
        self.ignore(self.quietZoneDoneEvent)
        del self.quietZoneDoneEvent
        self.quietZoneStateData.exit()
        self.quietZoneStateData.unload()
        self.quietZoneStateData = None

    def handleQuietZoneDone(self):
        status = self.quietZoneStateData.getRequestStatus()
        self.fsm.request(status['where'], [status])

    def enterPlace(self, requestStatus):
        self.acceptOnce(self.placeDoneEvent, self.placeDone)
        self.place = self.placeClass(self, self.fsm, self.placeDoneEvent)
        base.cr.playGame.setPlace(self.place)
        self.place.load()
        self.place.enter(requestStatus)

    def exitPlace(self):
        self.ignore(self.placeDoneEvent)
        self.place.exit()
        self.place.unload()
        self.place = None
        base.cr.playGame.setPlace(self.place)

    def placeDone(self, task=None):
        doneStatus = self.place.doneStatus
        if doneStatus:
            self.requestStatus = doneStatus
            self.doneStatus = doneStatus
            messenger.send(self.doneEvent)
            if task:
                return task.done
        else:
            # For some reason, after doing one episode and then
            # playing the prologue and entering Gyro's Lab
            # will have this edge case. This is an easy fix
            # that took me hours to think of for some reason lol.
            self.notify.debug('No place doneStatus! Trying again.')
            taskMgr.doMethodLater(0.5, self.placeDone, uniqueName('tryAgainTask'))

    def enterEpisodeZone(self, requestStatus):
        self.placeClass = self.getExteriorPlaceClass()
        self.enterPlace(requestStatus)
        self.hood.spawnTitleText(requestStatus['zoneId'])
        if requestStatus['how'] != 'doorIn':
            # door handles sending the message
            messenger.send('enterEpisodeZone')

    def getExteriorPlaceClass(self):
        self.notify.debug('getExteriorPlaceClass')
        return EpisodeZone.EpisodeZone

    def exitEpisodeZone(self):
        taskMgr.remove('titleText')
        self.hood.hideTitleText()
        self.exitPlace()
        self.placeClass = None
        return
