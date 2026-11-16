from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObjectGlobal
from direct.task.Task import Task
from direct.discord_rpc.util.utils import iter_keys, iter_values

from panda3d.core import NodePath

from toontown.episodes import EpisodeConfig
from toontown.episodes.MarginManager import EpisodeMarginManager
from toontown.hood import ZoneUtil
from toontown.toon import ToonDNA
from toontown.toonbase import ToontownGlobals, TTLocalizer

import collections
from copy import deepcopy
import json


class EpisodeManager(DistributedObjectGlobal.DistributedObjectGlobal):
    notify = DirectNotifyGlobal.directNotify.newCategory('EpisodeManager')
    neverDisable = 1

    def __init__(self, cr):
        DistributedObjectGlobal.DistributedObjectGlobal.__init__(self, cr)
        cr.episodeManager = self

        self.episode = None
        self.episodeZones = None
        self.episodeZoneId = None
        self.episodeZoneStatus = {}

        self.margins = False
        # for handling local page chats and stuff
        self.marginMgr = EpisodeMarginManager()
        self.marginMgr.hideNode()
        self.__activeAvatars = {}
        self.__allowEpisodeMarginManaging = False

    def generate(self):
        DistributedObjectGlobal.DistributedObjectGlobal.generate(self)
        self.accept('requestEpisode', self.d_requestEpisode)

    def disable(self):
        self.ignoreAll()
        ZoneUtil.overrideOff()
        DistributedObjectGlobal.DistributedObjectGlobal.disable(self)

    def d_requestEpisode(self, episode):
        self.sendUpdate('requestEpisode', [episode])

    def enterEpisode(self, episodeZones):
        episodeZones = json.loads(episodeZones, object_pairs_hook=collections.OrderedDict)
        self.episodeZones = episodeZones
        zoneTypes = {}
        for zone in list(episodeZones.keys()):
            zoneId = EpisodeConfig.EPISODES.get(self.episode).get('zones').get(zone)
            zoneType = EpisodeConfig.EPISODES.get(self.episode).get('zoneTypes').get(zoneId)
            zoneTypes[episodeZones[zone]] = zoneType
            self.episodeZoneStatus[zoneId] = 0

        self.episodeZoneId = EpisodeConfig.EPISODES.get(self.episode).get('zones').get(list(episodeZones.keys())[0])
        ZoneUtil.toggleEpisodeOverride()

        base.localAvatar.setName(EpisodeConfig.EPISODES.get(self.episode).get('toon').get('name'))
        dna = ToonDNA.ToonDNA()
        dnaString = EpisodeConfig.EPISODES.get(self.episode).get('toon').get('dna')
        dna.newToonFromProperties(*dnaString)
        base.localAvatar.setDNA(dna)

        NodePath(base.marginManager).hide()

        messenger.send('startEpisode', [episodeZones.get(list(episodeZones.keys())[0])])
        self.acceptOnce('stopEpisode', self.__handleStopEpisode)
        self.acceptOnce('toonArrivedEpisode', self.d_toonArrived)

        base.cr.discordManager.setInfo(base.cr.discordManager.getState(), TTLocalizer.DiscordEpisode,
                                       self.episode, EpisodeConfig.EPISODES.get(self.episode).get('name'), None, None,
                                       ToontownGlobals.Episode)

        if __debug__:
            self.accept('p', self.advanceMovie, extraArgs=[True])
            self.accept('p-up', self.advanceMovie, extraArgs=[False])
            self.accept('m', self.toggleMargins)

    def advanceMovie(self, state):
        messenger.send('advance-movie', [state])

    def toggleMargins(self):
        self.margins = not self.margins
        if self.margins:
            base.localAvatar.book.obscureButton(0)
            base.localAvatar.book.setSafeMode(0)
            base.localAvatar.laffMeter.obscure(0)
            base.localAvatar.chatMgr.obscure(0, 0)
            base.localAvatar.chatMgr.normalButton.show()
            base.localAvatar.obscureFriendsListButton(-1)
            base.localAvatar.obscureClarabelleButton(-1)
        else:
            base.localAvatar.book.obscureButton(1)
            base.localAvatar.book.setSafeMode(1)
            base.localAvatar.laffMeter.obscure(1)
            base.localAvatar.chatMgr.obscure(1, 1)
            base.localAvatar.chatMgr.normalButton.hide()
            base.localAvatar.obscureFriendsListButton(1)
            base.localAvatar.obscureClarabelleButton(1)

    def __handleStopEpisode(self):
        # cleanup debug messages
        # Note: I know the public would never really be able to use these anyways, but just in case a dev starts
        # wondering why their game just crashed hitting one of these buttons by mistake somewhere, like the the
        # PAT screen, or other odd behavior
        if __debug__:
            self.ignore('p')
            self.ignore('p-up')
            self.ignore('m')
        tmp = deepcopy(self.__activeAvatars)
        for avatar in iter_keys(tmp):
            self.removeActiveAvatar(av=avatar)
        self.marginMgr.hideNode()
        self.b_allDone()
        ZoneUtil.toggleEpisodeOverride()
        NodePath(base.marginManager).show()
        base.cr.gameFSM.request('closeShard')

    def b_allDone(self):
        self.d_allDone()
        self.allDone()

    def d_allDone(self):
        self.sendUpdate('allDone', [])

    def allDone(self):
        self.episode = None
        self.episodeZones = None
        self.episodeZoneId = None
        self.episodeZoneStatus = {}

        self.margins = False

    def d_toonArrived(self):
        self.sendUpdate('toonArrived', [])
        self.marginMgr.showNode()

    def setEpisode(self, episode):
        self.episode = episode

    def getEpisode(self):
        return self.episode

    def setEpisodeZone(self, episodeZoneId):
        zoneName = list(self.episodeZones.keys())[list(self.episodeZones.values()).index(episodeZoneId)]
        zoneId = EpisodeConfig.EPISODES.get(self.episode).get('zones').get(zoneName)
        self.episodeZoneId = zoneId

    def getEpisodeZone(self):
        return self.episodeZoneId

    def setEpisodeStatus(self, zoneId, status):
        self.episodeZoneStatus[zoneId] = status

    def getEpisodeStatus(self, zoneId):
        return self.episodeZoneStatus.get(zoneId)

    # TODO(maybe): determine defaults for the hideNametag attrs
    def addActiveAvatar(self, av, hideNametag2d=True, hideNametag3d=True):
        if base.wantNametags:
            if av is None or not hasattr(av, 'nametag'):
                self.notify.warning("Invalid avatar passed; skipping!")
                return
            if av in self.__activeAvatars:
                self.notify.warning("Avatar already in our list of active avatars; skipping!")
                return
            try:
                nametagMsg = av.nametag.getUniqueId()
                if nametagMsg is None or nametagMsg.strip() == "" or \
                        nametagMsg in [x[0] for x in iter_values(self.__activeAvatars)]:
                    self.notify.warning("Avatar's nametag doesn't have a unique ID; skipping!")
                    return
                # this next bit is to handle being able to handle things like clicking through page dialogue
                # without having to undo the client's normal margin manager being hidden
                # we're assuming the normal margin manager is base.marginManager here
                isManaged = av.nametag.isManaged()
                if isManaged:
                    av.nametag.unmanage(base.marginManager)
                av.nametag.manage(self.marginMgr)
                av.accept(nametagMsg, av.clickedNametag)
                if hideNametag2d:
                    av.hideNametag2d()
                if hideNametag3d:
                    av.hideNametag3d()
            except Exception as e:
                print(e)
                self.notify.warning("Could not complete setup avatar to be managed by us; skipping!")
                return
            self.__activeAvatars[av] = [nametagMsg, isManaged, base.marginManager]

    def removeActiveAvatar(self, av, unhideNametag3d=False, unhideNametag2d=False):
        if base.wantNametags:
            if av is None or not hasattr(av, 'nametag'):
                self.notify.warning("Invalid avatar passed; skipping!")
                return
            if av not in self.__activeAvatars:
                self.notify.warning("Avatar not in our list of active avatars; skipping!")
                return
            try:
                av.ignore(self.__activeAvatars[av][0])
                av.nametag.unmanage(self.marginMgr)
                # restore any old managers this avatar's nametag was using
                if self.__activeAvatars[av][1]:
                    av.nametag.manage(self.__activeAvatars[av][2])
                if unhideNametag2d:
                    av.showNametag2d()
                if unhideNametag3d:
                    av.showNametag3d()
            except Exception:
                # don't return; we want to remove the avatar from our list no matter what
                self.notify.warning("Couldn't complete unmanage ops for avatar's nametag; ignoring.")
            del self.__activeAvatars[av]
