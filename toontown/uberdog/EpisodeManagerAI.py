from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObjectGlobalAI
from direct.fsm.FSM import FSM
from direct.discord_rpc.util.utils import range, iter_values

from toontown.building.DoorTypes import DoorType, EXT_STANDARD, INT_STANDARD, EXT_HQ, INT_HQ
from toontown.episodes.DistributedEpisodeDoorAI import DistributedEpisodeDoorAI

from toontown.episodes import EpisodeConfig
from toontown.episodes.DistributedEpisodeZoneAI import DistributedEpisodeZoneAI

from toontown.episodes.EP02DistributedCashbotTrainYardAI import EP02DistributedCashbotTrainYardAI
from toontown.episodes.EP02DistributedShortChangeOfficeAI import EP02DistributedShortChangeOfficeAI
from toontown.episodes.EP02DistributedHighRiseHallwayAI import EP02DistributedHighRiseHallwayAI
from toontown.episodes.EP02DistributedCogBarAI import EP02DistributedCogBarAI
from toontown.episodes.EP02DistributedCogBathroomAI import EP02DistributedCogBathroomAI

from toontown.episodes.EP01DistributedDuckburgAI import EP01DistributedDuckburgAI
from toontown.episodes.EP01DistributedOakStreetAI import EP01DistributedOakStreetAI
from toontown.episodes.EP01DistributedGyrosLabAI import EP01DistributedGyrosLabAI

from toontown.episodes.EP00DistributedTestingGroundsAI import EP00DistributedTestingGroundsAI

from toontown.episodes.EP03DistributedDaisyGardensAI import EP03DistributedDaisyGardensAI
from toontown.episodes.EP03DistributedOakStreetAI import EP03DistributedOakStreetAI
from toontown.episodes.EP03DistributedSellbotHQAI import EP03DistributedSellbotHQAI
from toontown.episodes.EP03DistributedSellbotTowersAI import EP03DistributedSellbotTowersAI
from toontown.episodes.EP04DistributedScene1AI import EP04DistributedScene1AI
from toontown.episodes.EP04DistributedScene2AI import EP04DistributedScene2AI
from toontown.episodes.EP04DistributedScene3AI import EP04DistributedScene3AI

from toontown.toonbase import ToontownGlobals

import collections
import json

EPISODE_ZONES = [DistributedEpisodeZoneAI,

                 EP02DistributedCashbotTrainYardAI,
                 EP02DistributedShortChangeOfficeAI,
                 EP02DistributedHighRiseHallwayAI,
                 EP02DistributedCogBathroomAI,
                 EP02DistributedCogBarAI,

                 EP01DistributedDuckburgAI,
                 EP01DistributedOakStreetAI,
                 EP01DistributedGyrosLabAI,

                 EP00DistributedTestingGroundsAI,
                 
                 EP03DistributedDaisyGardensAI,
                 EP03DistributedOakStreetAI,
                 EP03DistributedSellbotHQAI,
                 EP03DistributedSellbotTowersAI,

                 EP04DistributedScene1AI,
                 EP04DistributedScene2AI,
                 EP04DistributedScene3AI]


class EpisodeFSM(FSM):
    notify = DirectNotifyGlobal.directNotify.newCategory('EpisodeFSM')

    def __init__(self, air, episodeInfo, episodeZones, avId):
        FSM.__init__(self, 'EpisodeFSM')
        self.air = air
        self.episodeInfo = episodeInfo
        self.episodeZones = episodeZones
        self.avId = avId
        self.zoneClasses = {}

        self.forceTransition('Introduction')

    def enterIntroduction(self):
        for key, value in self.episodeInfo.get('zones').items():
            zoneId = value
            zoneClass = EPISODE_ZONES[zoneId]
            zoneConnections = self.episodeInfo.get('zoneConnections').get(zoneId)
            allocatedZoneId = self.episodeZones.get(key)

            allocatedZones = []
            for connectionZoneId in zoneConnections:
                zoneName = self.episodeInfo.get('zoneId2String').get(connectionZoneId)
                connectionAllocatedId = self.episodeZones.get(zoneName)
                allocatedZones.append(connectionAllocatedId)

            zone = zoneClass(self.air, allocatedZoneId, allocatedZones, self.avId)
            zone.generateWithRequired(allocatedZoneId)
            self.zoneClasses[zoneId] = zone

        if 'zoneDoors' in self.episodeInfo:
            # TODO: hoodZone and blockNum should have more dynamic default values
            # doorData defaults:
            # doorType: DoorType.STANDARD
            # hoodZone: ToontownGlobals.Episode
            # blockVal: False
            # bldgZone: None
            # blockNum: 0
            # intZone: No default/REQUIRED

            # What each value means:
            # doorType - Type of doors to use
            # hoodZone - playground/street that normally has the building doors
            # Note: Street zone is only acceptable for blockNum lookups where blockNum or bldgZone is defined
            # blockVal - whether or not we can use a block value
            # bldgZone - the zone the building is normally found in
            # blockNum - the block number of the building
            # intZone - the episode zone of the interior door

            for ourZoneId, doorData in self.episodeInfo['zoneDoors'].items():
                if not self.episodeInfo['zoneConnections'].get(ourZoneId):
                    self.notify.error('Zone ID {} not in zoneConnections!'.format(ourZoneId))
                for idx in range(len(doorData)):
                    dnaStoreVals = doorData[idx]
                    otherZoneId = dnaStoreVals.get('intZone')
                    if not otherZoneId:
                        self.notify.error('Other zone ID {} not defined!'.format(otherZoneId))
                    elif not self.episodeInfo['zoneConnections'].get(otherZoneId):
                        self.notify.error('Other zone ID {} not in zoneConnections!'.format(otherZoneId))
                    hoodZone = dnaStoreVals.get('hoodZone', ToontownGlobals.Episode)
                    blockNum = dnaStoreVals.get('blockNum', 0)
                    if dnaStoreVals.get('blockVal', False):
                        def zoneCheck(mainZone, blockNum, bldgZone=None):
                            if blockNum > 99:
                                return False
                            intZone = mainZone - (mainZone % 100) + 500 + blockNum
                            if bldgZone is not None and intZone != bldgZone:
                                return False
                            return True

                        bldgZone = dnaStoreVals.get('bldgZone')
                        if bldgZone is not None:
                            blockNum = bldgZone % 100
                        if not zoneCheck(hoodZone, blockNum, bldgZone):
                            self.notify.error('Zone mismatch! Building zone {} not part of hood/street {}!'.
                                              format(bldgZone, hoodZone))

                    if ourZoneId not in self.zoneClasses:
                        self.notify.warning('Zone ID {} was not found in allocated zones; continuing'.format(ourZoneId))
                        continue
                    elif otherZoneId not in self.zoneClasses:
                        self.notify.warning('Other zone ID {} was not found in allocated zones; continuing'.format(otherZoneId))
                        continue
                    ourZoneLoc = self.episodeInfo['zoneTypes'][ourZoneId]
                    if ourZoneLoc == self.episodeInfo['zoneTypes'][otherZoneId]:
                        if ourZoneLoc == EpisodeConfig.EXTERIOR:
                            self.notify.warning('There is no such thing as an Exterior to Exterior door anywhere!')
                        else:
                            self.notify.warning('Interior to Interior door unimplemented.')
                        continue
                    doorType = dnaStoreVals.get('doorType', DoorType.STANDARD)
                    if doorType == DoorType.STANDARD:
                        if ourZoneLoc == EpisodeConfig.EXTERIOR:
                            ourDoorType = EXT_STANDARD
                            nextDoorType = INT_STANDARD
                        else:
                            ourDoorType = INT_STANDARD
                            nextDoorType = EXT_STANDARD
                    elif doorType == DoorType.HQ:
                        if ourZoneLoc == EpisodeConfig.EXTERIOR:
                            ourDoorType = EXT_HQ
                            nextDoorType = INT_HQ
                        else:
                            ourDoorType = INT_HQ
                            nextDoorType = EXT_HQ
                    else:
                        self.notify.warning('Invalid door type; continuing')
                        continue
                    ourZone = self.episodeZones.get(self.episodeInfo['zoneId2String'][ourZoneId])
                    nextZone = self.episodeZones.get(self.episodeInfo['zoneId2String'][otherZoneId])
                    if ourZone is None or nextZone is None:
                        self.notify.warning('Missing a zone ID for our doors; continuing')
                        continue
                    ourDoor = DistributedEpisodeDoorAI(self.air, blockNum, ourDoorType, ourZone)
                    nextDoor = DistributedEpisodeDoorAI(self.air, blockNum, nextDoorType, nextZone)
                    ourDoor.setOtherDoor(nextDoor)
                    nextDoor.setOtherDoor(ourDoor)
                    ourDoor.generateWithRequired(ourZone)
                    nextDoor.generateWithRequired(nextZone)
                    self.zoneClasses[ourZoneId].appendDoor(ourDoor)
                    self.zoneClasses[otherZoneId].appendDoor(nextDoor)
                    self.notify.debug('Our door DO ID={}, Zone ID={}, Other door DO ID={}, Zone ID={}'.format(
                        ourDoor.doId, ourDoor.zoneId,
                        nextDoor.doId, nextDoor.zoneId
                    ))

    def enterCleanup(self):
        self.episodeInfo = None
        self.episodeZones = None
        self.avId = -1

        for zone in iter_values(self.zoneClasses):
            zone.requestDelete()

        self.zoneClasses = {}


class EpisodeManagerAI(DistributedObjectGlobalAI.DistributedObjectGlobalAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('EpisodeManagerAI')

    def __init__(self, air):
        DistributedObjectGlobalAI.DistributedObjectGlobalAI.__init__(self, air)
        self.air = air
        self.avId2fsm = {}
        self.avId2Episode = {}

    def requestEpisode(self, episode):
        avId = self.air.getAvatarIdFromSender()
        if not avId:
            return

        episodeInfo = EpisodeConfig.EPISODES.get(episode)
        if not episodeInfo:
            return

        zoneInfo = episodeInfo.get('zones')
        if not zoneInfo:
            return

        self.avId2Episode[avId] = episode

        episodeZones = collections.OrderedDict()
        for zone in zoneInfo:
            episodeZones[zone] = self.air.allocateZone()

        self.avId2fsm[avId] = EpisodeFSM(self.air, episodeInfo, episodeZones, avId)

        event = self.air.getAvatarExitEvent(avId)
        self.acceptOnce(event, self.__unexpectedExit, extraArgs=[avId])

        episodeZones = json.dumps(episodeZones)

        self.d_enterEpisode(avId, episodeZones)

    def __unexpectedExit(self, avId):
        fsm = self.avId2fsm.get(avId)
        if fsm:
            fsm.demand('Cleanup')

    def d_enterEpisode(self, avId, episodeZones):
        self.sendUpdateToAvatarId(avId, 'enterEpisode', [episodeZones])

    def toonArrived(self):
        avId = self.air.getAvatarIdFromSender()
        av = self.air.doId2do.get(avId)
        if not av:
            return

        episode = self.avId2Episode[avId]
        if not episode:
            return

        av.b_setNametagStyle(100)
        av.b_setRun(False)

        if episode == 'short_work':
            av.b_setName('Short Change')

    def allDone(self):
        accId = self.air.getAccountIdFromSender()
        avId = self.air.getAvatarIdFromSender()

        event = self.air.getAvatarExitEvent(avId)
        self.ignore(event)

        if avId not in self.avId2Episode:
            self.air.writeServerEvent('suspicious', accId=accId, avId=avId,
                                      issue="Avatar tried to end an episode they aren't apart of!")
            return
        episodeName = self.avId2Episode[avId]
        del self.avId2Episode[avId]

        fsm = self.avId2fsm.get(avId)
        if fsm:
            fsm.demand('Cleanup')
            # since this is normally called only when a player does indeed finish an episode, go ahead and set
            # the episode as completed
            self.air.netMessenger.send('SetEpisodeCompleted', [accId, episodeName])
        else:
            self.air.writeServerEvent('suspicious', avId, 'Attempted to exit a non-existent episode.')
