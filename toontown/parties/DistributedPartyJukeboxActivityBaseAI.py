from direct.directnotify import DirectNotifyGlobal
from direct.distributed.ClockDelta import globalClockDelta

from toontown.parties import PartyGlobals
from toontown.parties.DistributedPartyActivityAI import DistributedPartyActivityAI
import random


class DistributedPartyJukeboxActivityBaseAI(DistributedPartyActivityAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedPartyJukeboxActivityBaseAI')

    def __init__(self, air, parent, activity):
        DistributedPartyActivityAI.__init__(self, air, parent, activity)
        self.music = PartyGlobals.PhaseToMusicData
        self.currentToon = 0
        self.owners = []
        self.queue = []
        self.paused = False
        self.playing = False
        self.loop = False

    def announceGenerate(self):
        DistributedPartyActivityAI.announceGenerate(self)
        self.accept('fireworks-started-%s' % self.getPartyDoId(), self.handleFireworksStarted)
        self.accept('fireworks-finished-%s' % self.getPartyDoId(), self.handleFireworksFinished)
        # Wait 1 second so we don't start before holidays do
        taskMgr.doMethodLater(1, self.playSong, self.uniqueName('wait-for-holidays'), extraArgs=[[0, '']])

    def delete(self):
        taskMgr.remove(self.uniqueName('play-song'))
        taskMgr.remove(self.uniqueName('remove-toon'))
        self.ignoreAll()
        DistributedPartyActivityAI.delete(self)

    def setNextSong(self, song):
        avId = self.air.getAvatarIdFromSender()
        if not avId:
            return

        phase = self.music.get(song[0])
        if avId != self.currentToon:
            self.air.writeServerEvent('suspicious', avId=avId,
                                      issue='Toon tried to set song without using the jukebox!')
            return

        if not phase:
            self.air.writeServerEvent('suspicious', avId=avId, issue='Toon supplied invalid phase for song!')
            return

        if song[1] not in phase:
            self.air.writeServerEvent('suspicious', avId=avId, issue='Toon supplied invalid song name!')
            return

        if avId in self.owners:
            self.queue[self.owners.index(avId)] = song
        else:
            self.queue.append(song)
            self.owners.append(avId)

        for avId in self.toonsPlaying:
            self.sendUpdateToAvatarId(avId, 'setSongInQueue', [song])

        if self.paused:
            return

        if not self.playing:
            self.d_setSongPlaying([0, ''], 0)
            taskMgr.remove(self.uniqueName('play-song'))
            self.playSong([0, ''])

    def d_setSongPlaying(self, details, owner, forceRemoval=False):
        timestamp = globalClockDelta.getRealNetworkTime()
        self.sendUpdate('setSongPlaying', [details, owner, timestamp, forceRemoval])

    def queuedSongsRequest(self):
        avId = self.air.getAvatarIdFromSender()
        if avId in self.owners:
            index = self.owners.index(avId)
        else:
            index = -1

        self.sendUpdateToAvatarId(avId, 'queuedSongsResponse', [self.queue, index])

    def requestLoop(self):
        avId = self.air.getAvatarIdFromSender()
        if not avId:
            return

        av = self.air.doId2do.get(avId)
        if not av:
            return

        if avId != self.currentToon:
            self.air.writeServerEvent('suspicious', avId=avId, issue='Toon tried to loop song without using the jukebox!')
            return

        party = self.air.doId2do.get(self.parent)
        if not party:
            return

        hostId = party.hostId
        if avId != hostId:
            self.air.writeServerEvent('suspicious', avId=avId, issue='Toon tried to loop song to the top but is not the party host!')
            return

        self.loop = not self.loop

        self.d_setLoop(self.loop)

    def d_setLoop(self, state):
        self.sendUpdate('setLoop', [state])

    def moveHostSongToTopRequest(self):
        avId = self.air.getAvatarIdFromSender()
        if not avId:
            return

        if avId != self.currentToon:
            self.air.writeServerEvent('suspicious', avId=avId,
                                      issue='Toon tried to set song without using the jukebox!')
            return

        party = self.air.doId2do.get(self.parent)
        if not party:
            return

        hostId = party.hostId
        if avId != hostId:
            self.air.writeServerEvent('suspicious', avId=avId, issue='Toon tried to move the host\'s song to the top!')
            return

        if hostId not in self.owners:
            self.air.writeServerEvent('suspicious', avId=avId,
                                      issue='Host tried to move non-existent song to the top of the queue!')
            return

        index = self.owners.index(hostId)
        self.owners.remove(hostId)
        song = self.queue.pop(index)
        self.owners.insert(0, hostId)
        self.queue.insert(0, song)
        for avId in self.toonsPlaying:
            self.sendUpdateToAvatarId(avId, 'moveHostSongToTop', [])

    def getRandomMusicInfo(self, phase=-1):
        if phase == -1:
            # Get random phase
            keys = list(self.music.keys())
            phase = random.choice(keys)

        # From that phase, get random filename
        values = list(self.music[phase].keys())
        filename = values[random.randint(0, len(values) - 1)]

        return phase, filename

    def __getSongInfo(self, details):
        return self.music[details[0]][details[1]]

    def __getNormalWaitTime(self, songInfo):
        return songInfo[1] * PartyGlobals.getMusicRepeatTimes(songInfo[1])

    def __getPauseGap(self):
        if not self.loop:
            gap = PartyGlobals.MUSIC_GAP
        else:
            gap = PartyGlobals.LOOP_GAP
        return gap

    def playSong(self, details, task=None):
        if not self.paused:
            forceRemoval = False
            owner = 0
            gap = self.__getPauseGap()
            if self.loop:
                # Normal loop w/ queue
                if self.queue:
                    if details == [0, '']:
                        details = self.queue.pop(0)
                    # A Toon chooses a new song while a randomized song is being looped
                    if not self.playing:
                        # If we don't do this, there will be issues queueing up future songs
                        owner = self.owners.pop(0)
                        # Since we're looping, we need a way to force remove the new song from the queue on the client
                        forceRemoval = True
                    self.playing = True
                    songInfo = self.__getSongInfo(details)
                    waitTime = self.__getNormalWaitTime(songInfo)
                else:
                    if not self.playing:
                        # Handle loop while playing a random song
                        # This actually makes it look like there's no loop because we don't want to loop a random song
                        details = self.getRandomMusicInfo()
                        waitTime = self.__getSongInfo(details)[1]
                        # Force normal, non-loop gap
                        gap = PartyGlobals.MUSIC_GAP
                    else:
                        # Normal loop w/o queue
                        songInfo = self.__getSongInfo(details)
                        waitTime = self.__getNormalWaitTime(songInfo)
            else:
                if self.queue:
                    # Play a song from the queue
                    self.playing = True
                    details = self.queue.pop(0)
                    owner = self.owners.pop(0)
                    songInfo = self.__getSongInfo(details)
                    waitTime = self.__getNormalWaitTime(songInfo)
                else:
                    # Play a random song because there's no queue
                    self.playing = False
                    details = self.getRandomMusicInfo()
                    waitTime = self.__getSongInfo(details)[1]

            self.d_setSongPlaying(details, owner, forceRemoval)
            taskMgr.doMethodLater(waitTime, self.pauseSong, self.uniqueName('play-song'), extraArgs=[details, gap],
                                  appendTask=True)

        if task:
            return task.done

    def pauseSong(self, details, gap, task):
        # Create a gap in between 2 songs
        self.d_setSongPlaying([0, ''], 0)
        taskMgr.doMethodLater(gap, self.playSong, self.uniqueName('play-song'), extraArgs=[details], appendTask=True)
        return task.done

    def toonJoinRequest(self):
        avId = self.air.getAvatarIdFromSender()
        if not avId:
            return

        if self.currentToon:
            self.sendUpdateToAvatarId(avId, 'joinRequestDenied', [PartyGlobals.DenialReasons.Default])
            return

        if avId in self.toonsPlaying:
            return

        self.currentToon = avId
        taskMgr.doMethodLater(PartyGlobals.JUKEBOX_TIMEOUT, self.removeToon, self.uniqueName('remove-toon'))
        self.toonsPlaying.append(avId)
        self.b_setToonsPlaying(self.toonsPlaying)

    def toonExitRequest(self):
        avId = self.air.getAvatarIdFromSender()
        if not avId:
            return

        if avId != self.currentToon:
            return

        if avId not in self.toonsPlaying:
            return

        taskMgr.remove(self.uniqueName('remove-toon'))
        self.currentToon = 0
        self.toonsPlaying.remove(avId)
        self.b_setToonsPlaying(self.toonsPlaying)

    def toonExitDemand(self):
        avId = self.air.getAvatarIdFromSender()
        if not avId:
            return

        if avId != self.currentToon:
            return

        if avId not in self.toonsPlaying:
            return

        taskMgr.remove(self.uniqueName('remove-toon'))
        self.currentToon = 0
        self.toonsPlaying.remove(avId)
        self.b_setToonsPlaying(self.toonsPlaying)

    def removeToon(self, task):
        if not self.currentToon:
            return

        if self.currentToon not in self.toonsPlaying:
            return

        self.toonsPlaying.remove(self.currentToon)
        self.b_setToonsPlaying(self.toonsPlaying)
        self.currentToon = 0
        return task.done

    def handleFireworksStarted(self):
        taskMgr.remove(self.uniqueName('play-song'))
        self.paused = True
        self.playing = False
        self.d_setSongPlaying([0, ''], 0)

    def handleFireworksFinished(self):
        self.paused = False
        self.playSong([0, ''])
