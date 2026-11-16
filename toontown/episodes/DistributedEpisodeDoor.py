from toontown.building.DistributedDoor import DistributedDoor
from toontown.building import DoorTypes
from toontown.episodes.DistributedEpisodeZone import DistributedEpisodeZone
from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.discord_rpc.util.utils import iter_values
from panda3d.core import NodePath


class DistributedEpisodeDoor(DistributedDoor):
    # NOTE: add any additional required data if needed
    notify = directNotify.newCategory('DistributedEpisodeDoor')

    def __init__(self, cr):
        DistributedDoor.__init__(self, cr)
        self.__ourZone = None
        self.__zoneLookupFailed = False

    def announceGenerate(self):
        DistributedDoor.announceGenerate(self)
        self.notify.debug('announceGenerate() - DO ID={}, Zone ID={}'.format(self.doId, self.zoneId))
        messenger.send('episodeDoorReady-{doId}'.format(doId=self.doId), [])

    def getBuilding(self):
        if 'building' not in self.__dict__:
            if self.doorType == DoorTypes.INT_STANDARD:
                door = render.find('**/leftDoor;+s')
                self.building = door.getParent()
            elif self.doorType == DoorTypes.INT_HQ:
                door = render.find('**/door_0')
                self.building = door.getParent()
            elif self.doorType == DoorTypes.INT_KS:
                self.building = render.find('**/KartShop_Interior*')
            elif self.doorType in (DoorTypes.EXT_STANDARD, DoorTypes.EXT_HQ, DoorTypes.EXT_KS):
                self.building = self.geom.find('**/??{block}:*_landmark_*_DNARoot;+s'.format(block=self.block))
                if self.building.isEmpty():
                    self.building = self.geom.find('**/??{block}:animated_building_*_DNARoot;+s'.format(block=self.block))
            elif self.doorType == DoorTypes.EXT_COGHQ or self.doorType == DoorTypes.INT_COGHQ:
                self.building = self.geom
            else:
                self.notify.error('No such door type as {}'.format(self.doorType))
        return self.building

    def getRequestStatus(self):
        zoneId = self.otherZoneId
        doId = self.otherDoId
        if zoneId == 0 or doId == 0:
            self.notify.error('Other door data corrupted! Zone ID={}, DO ID={}.'.format(zoneId, doId))
        self.notify.debug('Zone ID={}, DO ID={}.'.format(zoneId, doId))
        self.cr.episodeManager.setEpisodeZone(zoneId)
        hoodId = self.cr.playGame.hood.hoodId
        request = {'loader': 'episodeLoader',
                   'where': 'episodeZone',
                   'how': 'doorIn',
                   'hoodId': hoodId,
                   'zoneId': zoneId,
                   'avId': -1,
                   'allowRedirect': 0,
                   'doorDoId': doId}
        return request

    def findDoorNode(self, string, allowEmpty=False):
        building = self.getBuilding()
        foundNode = NodePath() if allowEmpty else None
        if not building:
            self.notify.warning('getBuilding() returned None, avoiding crash, remark 896029')
        else:
            if building.isEmpty():
                self.notify.warning('Building node is empty!')
            else:
                self.notify.debug('Building node children: {}'.format(building.getChildren()))
            if building.getNumChildren() > 0:
                foundNode = building.find('**/door_{doorIdx}/**/{locator}*;+s+i'.format(doorIdx=self.doorIndex,
                                                                                        locator=string))
                if foundNode.isEmpty():
                    foundNode = building.find('**/{locator}*;+s+i'.format(locator=string))
            else:
                self.notify.warning('Building has no children!')
        if allowEmpty:
            return foundNode
        else:
            # make use of allowEmpty being False
            if foundNode is None or foundNode.isEmpty():
                self.notify.error('Failed to lookup door node with node {} and door index {}!'.format(string,
                                                                                                      self.doorIndex))
        return foundNode

    def exitCompleted(self):
        DistributedDoor.exitCompleted(self)
        messenger.send('enterEpisodeZone')

    def __doZoneLookup(self):
        # only attempt a lookup once; if it fails, we're probably never going to get it
        if self.__ourZone is None and not self.__zoneLookupFailed:
            self.__zoneLookupFailed = True
            for do in iter_values(self.cr.doId2do):
                if isinstance(do, DistributedEpisodeZone) and do.zoneId == self.zoneId:
                    self.__zoneLookupFailed = False
                    self.__ourZone = do
                    self.notify.debug('Class {} found with our zone ID; using that.'.format(do.__class__.__name__))
            if self.__zoneLookupFailed:
                self.notify.warning('Failed to lookup our episode zone!')

    @property
    def geom(self):
        self.__doZoneLookup()
        if self.__ourZone is not None:
            return self.__ourZone.geom
        else:
            self.notify.warning('Could not get episode geom!')
            return NodePath()
