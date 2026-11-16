"""
DistributedArcadeMachine AI Side • Created by Drew @ 10/6/2022
Authorized for use ONLY in Toontown Realms
"""
from typing import Optional

from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI

from toontown.arcade.ArcadeMachineGlobals import RequestPlayResponses


class DistributedArcadeMachineAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistArcadeMachineAI')

    def __init__(self, air):
        DistributedObjectAI.__init__(self, air)
        self.activeToon: Optional[int] = None

    def requestPlay(self):
        """
        Client asked us to play, see if we can, then respond
        """
        avId = self.air.getAvatarIdFromSender()
        if not avId:
            self.notify.warning('requestPlay somehow got no avid from sender. discarding...')
            return

        if self.activeToon:
            self.sendUpdateToAvatarId(avId, 'requestPlayResponse', [RequestPlayResponses.SOMEONE_ELSE_PLAYING.value])
            return

        self.sendUpdateToAvatarId(avId, 'requestPlayResponse', [RequestPlayResponses.START_PLAYING.value])
        self.activeToon = avId
        self.acceptOnce(self.air.getAvatarExitEvent(avId), self.unexpectedExit)

    def requestLeave(self):
        """
        Client asked us to leave
        """
        if not self.activeToon:
            self.notify.warning('requestLeave but no one is playing')
            return
        avId = self.air.getAvatarIdFromSender()
        if not avId:
            self.notify.warning('requestPlay somehow got no avid from sender. discarding...')
            return

        self.sendUpdateToAvatarId(avId, 'requestPlayResponse', [RequestPlayResponses.STOP_PLAYING.value])
        self.activeToon = None

    def unexpectedExit(self):
        """
        Player unexpectedly left the machine (e.g. disconnected)
        """
        self.activeToon = None
