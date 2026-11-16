import json
import os
import traceback
import uuid
from collections import OrderedDict
from datetime import datetime
from typing import Dict, Any, Optional, List

from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObjectAI
from direct.distributed.ClockDelta import globalClockDelta

from otp.otpbase import OTPGlobals
from toontown.hood import ZoneUtil
from toontown.sandbox import PropGlobals
from toontown.sandbox.BuildLotGlobals import FLPermBuild, FLPermClearLoad
from toontown.sandboxdistprops.DistributedPropAI import DistributedPropAI
from toontown.sandboxdistprops.DistributedPropDoorAI import DistributedPropDoorAI
from toontown.sandboxdistprops.DistributedPropToonBuildingAI import DistributedPropToonBuildingAI
from toontown.toonbase import TTLocalizer, ServerSettings
from toontown.toonbase import ToontownGlobals
from panda3d.core import Vec3, LVector3, LVector3f, Vec3F

# --------------------------- todo: make DistributedPropAI ---------------------------
PROP_NAME_TO_CLASS: Dict[str, type] = {
    "TestBuilding01": DistributedPropToonBuildingAI,
    "Functional Curved Door": DistributedPropDoorAI,
    "Functional Round Door": DistributedPropDoorAI,
    "Functional Windowed Door": DistributedPropDoorAI,
    "Functional Square Door (L)": DistributedPropDoorAI,
    "Functional Square Door (R)": DistributedPropDoorAI,
    "Functional Fancy Door": DistributedPropDoorAI,
    "Functional Wooden Door": DistributedPropDoorAI
}


class DistributedPropGeneratorAI(DistributedObjectAI.DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedPropGeneratorAI')

    def __init__(self, air, zoneId: int, specialZone: int = 0):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)

        # If we don't yet have a backups/props directory, make one
        if not os.path.exists('backups/props/'):
            os.mkdir('backups/props/')

        # The zoneId our Prop Generator is loaded in
        self.zoneId = zoneId

        # We store all the info related to the individual props here
        self.propInfo = OrderedDict()

        # Store all distributed props here
        # ------------------------------ todo: make DistributedPropAI ------------------------------
        self.distributedProps: Dict[str, DistributedPropAI] = {}

        # How many props are loaded in the zone
        self.context = 0

        # Is this Prop Generator locked?
        self.locked = False

        # Keep track of players who have been spawning props to prevent spam
        self.recentAvatars = {}

        # == Build lot specific features ==
        self.isBuildLot: bool = specialZone == 1
        self.buildLotPrivileges: Dict[int, int] = {}

        if self.isBuildLot:
            self.maxPropCount = PropGlobals.MaxPropCountHard
        else:
            self.maxPropCount = PropGlobals.MaxPropCount

        # == Estate Specific Features ==
        self.isEstate: bool = specialZone == 2
        self.estateDoId: Optional[int] = None

    def announceGenerate(self):
        DistributedObjectAI.DistributedObjectAI.announceGenerate(self)
        self.loadBackup()
        taskMgr.doMethodLater(0.5, self.propCooldown, self.uniqueName('propCooldown'))

    def getMaxPropCount(self):
        return self.maxPropCount

    def getIsBuildLotOrEstate(self) -> bool:
        return self.isBuildLot or self.isEstate

    def requestProps(self):
        if not self.propInfo:
            # Don't bother sending any info if we don't got any.
            return
        avId = self.air.getAvatarIdFromSender()
        for prop in self.propInfo:
            propName, pos, hpr, scale, data = self.propInfo[prop]
            data = json.dumps(data)
            self.sendUpdate('spawnPropNew', [prop, propName, pos, hpr, scale, data])

    def getBuilder(self, toon):
        if toon.getAccessLevel() < OTPGlobals.AccessLevelName2Int.get('BUILDER'):
            return False
        return True

    def confirmUpdateProp(self, propData):
        propId = propData[0]
        if propId not in self.propInfo:
            self.notify.warning('Received update for non-existant prop %s!' % propId)
            return

        propDataList = list(propData)
        propDataList[15] = globalClockDelta.getRealNetworkTime(bits = 32)
        propData = tuple(propDataList)

        self.propInfo[propId] = propData
        self.d_updateProp(propData)

        self.backupProps()

    def d_updateProp(self, propData):
        self.sendUpdate('updateProp', [propData])

    def confirmDeleteProp(self, propId):
        avId = self.air.getAvatarIdFromSender()
        if propId not in self.propInfo:
            self.notify.warning('Received update for non-existant prop %s!' % propId)
            return

        toon = self.air.doId2do.get(avId)
        if not toon:
            self.notify.warning(
                'Non-existant toon with avId of %s tried to delete all props' % avId)
            return

        # If prop spawning is locked and the Toon isn't a builder, we can't generate it
        if self.locked and not self.getBuilder(toon):
            self.sendUpdateToAvatarId(avId, 'propMessage', [ToontownGlobals.PROPS_SPAWNING_LOCKED])
            return

        if self.propInfo[propId][4].get('locked', False):
            self.sendUpdateToAvatarId(avId, 'propMessage', [ToontownGlobals.PROP_LOCKED])
            return

        # for otherProp in list(self.propInfo.values()):
        #    if otherProp[21] == propId and otherProp[22]:
        #        # Because this prop is parented to the requested prop we're deleting, it's gotta go too.
        #        self.confirmDeleteProp(otherProp[0])

        distprop: Optional[DistributedPropAI] = self.distributedProps.get(propId,None)
        if distprop:
            distprop.requestDelete()
            del self.distributedProps[propId]

        del self.propInfo[propId]
        self.sendUpdate('deleteProp', [propId])
        self.backupProps()

    def confirmDeleteAllProps(self, state, zoneId):
        avId = self.air.getAvatarIdFromSender()

        toon = self.air.doId2do.get(avId)
        if not toon:
            self.notify.warning(
                'Non-existant toon with avId of %s tried to delete all props with state %d' % (avId, state))
            return

        if not state and self.isBuildLot:
            if not self.getLotPrivilegesForAvatar(avId) & FLPermClearLoad:
                self.sendUpdateToAvatarId(avId, 'propMessage', [ToontownGlobals.PROPS_NO_PERMISSION])
                return
        elif not self.getBuilder(toon):
            self.notify.warning(
                'Non-builder Toon with avId of %s tried to delete all props with state %d!' % (avId, state))
            return

        if not avId:
            self.notify.warning('Non-existant avId tried to delete all props with state %s!' % state)
            return

        if not state:
            if self.zoneId == zoneId:
                # Save some time if this is the same zone
                self.deleteProps()
            else:
                propGenerator = self.air.propGenerators.get(zoneId)
                if not propGenerator:
                    self.sendUpdateToAvatarId(avId, 'propMessage',
                                              [ToontownGlobals.PROPS_DELETED_ZONE_ERROR_NO_PROPGEN])
                    return
                propGenerator.deleteProps()
            self.sendUpdateToAvatarId(avId, 'propMessage', [ToontownGlobals.PROPS_DELETED_ZONE])
            self.notify.info(
                'Toon with name of {} and avId of {} deleting ALL props in zoneId {}!'.format(toon.getName(), avId,
                                                                                              zoneId))
        elif state:
            for propGeneratorId in list(self.air.propGenerators.keys()):
                propGenerator = self.air.propGenerators[propGeneratorId]
                propGenerator.deleteProps()
            self.sendUpdateToAvatarId(avId, 'propMessage', [ToontownGlobals.PROPS_DELETED])
            self.notify.info(
                'Toon with name of {} and avId of {} deleting ALL props in ALL zones!'.format(toon.getName(), avId))

    def requestDelete(self):
        for prop in self.distributedProps.values():
            prop.requestDelete()
            del prop
        DistributedObjectAI.DistributedObjectAI.requestDelete(self)

    def deleteProps(self):
        self.propInfo = OrderedDict()
        for prop in self.distributedProps.values():
            prop.requestDelete()
            del prop

        self.distributedProps: Dict[str, DistributedPropAI] = {}

        self.context = 0

        self.sendUpdate('deleteAllProps', [])
        self.backupProps()

    def confirmLockProps(self, state, zoneId):
        avId = self.air.getAvatarIdFromSender()
        if not state:
            if self.zoneId == zoneId:
                # Save some time if this is the same zone
                self.lockProps(state)
                self.sendLockMessage(avId, self.locked)
            else:
                propGenerator = self.air.propGenerators.get(zoneId)
                if not propGenerator:
                    self.sendUpdateToAvatarId(avId, 'propMessage', [ToontownGlobals.PROPS_LOCKED_ZONE_ERROR_NO_PROPGEN])
                    return
                propGenerator.lockProps(state)
                self.sendLockMessage(avId, propGenerator.locked)
        elif state:
            if not self.air.propGeneratorsLocked:
                self.air.propGeneratorsLocked = True
                self.sendUpdateToAvatarId(avId, 'propMessage', [ToontownGlobals.PROPS_LOCKED])
            elif self.air.propGeneratorsLocked:
                self.air.propGeneratorsLocked = False
                self.sendUpdateToAvatarId(avId, 'propMessage', [ToontownGlobals.PROPS_UNLOCKED])
            for propGeneratorId in list(self.air.propGenerators.keys()):
                propGenerator = self.air.propGenerators[propGeneratorId]
                propGenerator.lockProps(state)

    def lockProps(self, state = None):
        if state:
            if not self.air:
                self.notify.warning('Tried to lock prop generation but self.air does not exist! Trying simbase...')
                if simbase.air:
                    self.locked = simbase.air.propGeneratorsLocked
                else:
                    self.notify.warning('simbase does not exist either! Aborting prop generator locking.')
                    return
            else:
                self.locked = self.air.propGeneratorsLocked
            return
        self.locked = not self.locked

    def sendLockMessage(self, avId, locked):
        if locked:
            msgType = ToontownGlobals.PROPS_LOCKED_ZONE
        else:
            msgType = ToontownGlobals.PROPS_UNLOCKED_ZONE
        self.sendUpdateToAvatarId(avId, 'propMessage', [msgType])

    def propCooldown(self, task):
        for avId in list(self.recentAvatars.keys()):
            self.recentAvatars[avId] -= 1
            if self.recentAvatars.get(avId) <= 0:
                del self.recentAvatars[avId]

        return task.again

    def loadPropsFromFile(self, propUUID, propName, pos, hpr, scale, data):
        avId = self.air.getAvatarIdFromSender()

        if not avId:
            self.notify.warning('Non-existant avId tried to load props from file!')
            return

        toon = self.air.doId2do.get(avId)
        if not toon:
            self.notify.warning('Non-existant toon with avId of %s tried to load props from file!' % avId)
            return

        if self.isBuildLot:
            if not self.getLotPrivilegesForAvatar(avId) & FLPermClearLoad:
                self.sendUpdateToAvatarId(avId, 'propMessage', [ToontownGlobals.PROPS_NO_PERMISSION])
                return
        elif not self.getBuilder(toon):
            self.notify.warning('Non-builder Toon with avId of %s tried to load props from file!' % avId)
            return

        if propName not in PropGlobals.PropList:
            if propName.lower() in PropGlobals.Conversions:
                propName = PropGlobals.Conversions[propName.lower()]
            else:
                self.notify.warning(f'{avId} tried to spawn an unknown prop {propName}')
                return
        self.spawnPropFromFile(propUUID, propName, pos, hpr, scale, json.loads(data))

    def spawnPropFromFile(self, propUUID, propName, pos, hpr, scale, data):
        if propUUID == 'CONVERTED':
            propUUID = str(uuid.uuid4())

        self.updatePropInfo(propUUID, propName, pos, hpr, scale, data)

        if propName in PROP_NAME_TO_CLASS:
            if not ServerSettings.ExperimentalFeatures.get():
                self.notify.warning(f"Attempted to place a {propName}, but experimental features are disabled.")
                return
            newPropType = PROP_NAME_TO_CLASS.get(propName)
            if newPropType is None:
                self.notify.error("what")
            newProp: DistributedPropAI = newPropType(self.air, self, propName, propUUID, data)
            newProp.generateWithRequired(self.zoneId)
            newProp.b_setPosHpr(*pos, *hpr)
            if propUUID in self.distributedProps:
                self.notify.warning(f'A prop with UUID {propUUID} already exists?')
            self.distributedProps[propUUID] = newProp

        self.sendUpdate('spawnPropNew', [propUUID, propName, pos, hpr, scale, json.dumps(data)])

    def requestPropSave(self):
        avId = self.air.getAvatarIdFromSender()
        if not avId:
            self.notify.warning('Non-existant avId tried to request prop save!')
            return

        toon = self.air.doId2do.get(avId)
        if not toon:
            self.notify.warning('Non-existant toon with avId of %s tried to request prop save!' % avId)
            return

        if not self.getBuilder(toon):
            self.notify.warning('Non-builder Toon with avId of %s tried to request prop save!' % avId)
            return

        self.backupProps()

    def backupProps(self):
        if not self.zoneId:
            return

        # We don't want to backup any props that are in dynamic zones- that'd be plain weird
        if ZoneUtil.isDynamicZone(self.zoneId) and not self.isEstate:
            return

        propData = OrderedDict({'propgen_version': PropGlobals.PropGenVersion})
        for propID in self.propInfo:
            prop = self.propInfo[propID]
            propInfo = OrderedDict()
            propInfo['PropType'] = prop[0]
            propInfo['Position'] = prop[1]
            propInfo['Rotation'] = prop[2]
            propInfo['Scale'] = prop[3]
            propInfo['Data'] = prop[4]
            propData[propID] = propInfo

        if self.isEstate:
            zoneId = f'estate_{self.estateDoId}'
        else:
            zoneId = self.zoneId
        fileName = f'props_{zoneId}'
        with open('backups/props/' + fileName + '.json', 'w') as data:
            json.dump(propData, data, indent = 4)

    def loadBackup(self):
        # We don't want to load backups of props that are in dynamic zones - that'd be plain weird
        if ZoneUtil.isDynamicZone(self.zoneId) and not self.isEstate:
            return

        if self.isEstate:
            zoneId = f'estate_{self.estateDoId}'
        else:
            zoneId = self.zoneId

        filePath = 'backups/props/props_%s.json' % zoneId
        if os.path.exists(filePath):
            try:
                with open(filePath) as fileData:
                    props = json.load(fileData)
                    if 'propgen_version' not in props:
                        self.notify.warning(f'Backup for zone {zoneId} uses pre 1.1 prop gen save. Not loading.')
                        return
                    fileVersion = None
                    for propId in props:
                        # this will still get recognized
                        if propId == 'propgen_version':
                            fileVersion = props[propId]
                            continue
                        prop = props[propId]

                        if fileVersion != PropGlobals.PropGenVersion:
                            # Convert props that have had their names changed
                            if prop['PropType'].lower() in PropGlobals.Conversions:
                                prop['PropType'] = PropGlobals.Conversions[prop['PropType'].lower()]

                        if prop['PropType'] not in PropGlobals.PropList:
                            self.notify.warning(f'Tried to spawn an unknown prop {prop["PropType"]}')
                            continue
                        self.spawnPropFromFile(propId,
                                               prop['PropType'],
                                               prop['Position'],
                                               prop['Rotation'],
                                               prop['Scale'],
                                               prop['Data'])
            except:
                traceback.print_exc()

    def loadFromLotFile(self, lotFile: str):
        if os.path.exists(lotFile):
            try:
                with open(lotFile) as fileData:
                    props = json.load(fileData)['propgen_save']
                    if 'propgen_version' not in props:
                        self.notify.warning(f'Backup for zone {self.zoneId} uses pre 1.1 prop gen save. Not loading.')
                        return
                    fileVersion = None
                    for propId in props:
                        # this will still get recognized
                        if propId == 'propgen_version':
                            fileVersion = props[propId]
                            continue
                        prop = props[propId]

                        if fileVersion != PropGlobals.PropGenVersion:
                            # Convert props that have had their names changed
                            if prop['PropType'].lower() in PropGlobals.Conversions:
                                prop['PropType'] = PropGlobals.Conversions[prop['PropType'].lower()]

                        if prop['PropType'] not in PropGlobals.PropList:
                            self.notify.warning(f'Tried to spawn an unknown prop {prop["PropType"]}')
                            return
                        self.spawnPropFromFile(propId,
                                               prop['PropType'],
                                               prop['Position'],
                                               prop['Rotation'],
                                               prop['Scale'],
                                               prop['Data'])
            except:
                traceback.print_exc()

    def requestSpawnProp(self, propName: str, pos: Vec3F, hpr: Vec3F, scale: Vec3F):
        """
        === Sent from client ===
        Client told the server to spawn a prop
        """

        # Timestamp for when our prop was generated
        spawnTime = datetime.now().timestamp()

        # AvId of the Toon that generated it
        creatorAvId = self.air.getAvatarIdFromSender()

        if self.isBuildLot:
            if not self.getLotPrivilegesForAvatar(creatorAvId) & FLPermBuild:
                self.sendUpdateToAvatarId(creatorAvId, 'propMessage', [ToontownGlobals.PROPS_NO_PERMISSION])
                return

        # Attempt at getting the Toon's name
        creatorName = TTLocalizer.WordPageNA
        av = self.air.doId2do.get(creatorAvId)
        if av:
            creatorName = av.getName()

        if propName not in PropGlobals.PropList:
            self.sendUpdateToAvatarId(creatorAvId, 'propMessage', [ToontownGlobals.PROPS_ERROR])
            return

        # Don't generate this prop if the limit has been reached and the Toon isn't a builder
        propCount = len(list(self.propInfo.keys()))
        if propCount >= self.getMaxPropCount() and not self.getBuilder(av):
            self.sendUpdateToAvatarId(creatorAvId, 'propMessage', [ToontownGlobals.MAX_PROPS])
            return

        # Even if the Toon is a builder, don't generate passed our hard limit unless we're on dev
        if propCount >= PropGlobals.MaxPropCountHard and not __debug__:
            self.sendUpdateToAvatarId(creatorAvId, 'propMessage', [ToontownGlobals.MAX_PROPS_HARD])
            return

        # If prop spawning is locked and the Toon isn't a builder, we can't generate it
        if self.locked and not self.getBuilder(av):
            self.sendUpdateToAvatarId(creatorAvId, 'propMessage', [ToontownGlobals.PROPS_SPAWNING_LOCKED])
            return

        if creatorAvId in self.recentAvatars and not self.getBuilder(av):
            if self.recentAvatars.get(creatorAvId) >= 5:
                self.sendUpdateToAvatarId(creatorAvId, 'propMessage', [ToontownGlobals.PROPS_SPAMMING])
                return
            self.recentAvatars[creatorAvId] += 1

        if creatorAvId not in self.recentAvatars:
            self.recentAvatars[creatorAvId] = 1

        propUUID = str(uuid.uuid4())

        data = {
            'spawned_by_name': f'{creatorName}',
            'spawned_by_avid': creatorAvId,
            'spawned_on': spawnTime
        }

        self.updatePropInfo(propUUID, propName, pos, hpr, scale, data)

        if propName in PROP_NAME_TO_CLASS:
            if not ServerSettings.ExperimentalFeatures.get():
                self.sendUpdateToAvatarId(creatorAvId, 'propMessage', [ToontownGlobals.PROPS_EXPERIMENTAL])
                return
            newPropType = PROP_NAME_TO_CLASS.get(propName)
            if newPropType is None:
                self.notify.error("what")
            newProp: DistributedPropAI = newPropType(self.air, self, propName, propUUID, data)
            newProp.generateWithRequired(self.zoneId)
            newProp.b_setPosHpr(*pos, *hpr)
            if propUUID in self.distributedProps:
                self.notify.warning(f'A prop with UUID {propUUID} already exists?')
            self.distributedProps[propUUID] = newProp

        data = json.dumps(data)

        self.sendUpdate('spawnPropNew', [propUUID, propName, pos, hpr, scale, data])

        self.backupProps()

        self.sendUpdateToAvatarId(creatorAvId, 'finishedSpawnProp', [propUUID])

    def requestDuplicateProp(self, originalUUID, newPos, newHpr, newScale, newColorScale):
        # Timestamp for when our prop was generated
        spawnTime = datetime.now().timestamp()

        # AvId of the Toon that generated it
        creatorAvId = self.air.getAvatarIdFromSender()

        if self.isBuildLot:
            if not self.getLotPrivilegesForAvatar(creatorAvId) & FLPermBuild:
                self.sendUpdateToAvatarId(creatorAvId, 'propMessage', [ToontownGlobals.PROPS_NO_PERMISSION])
                return

        # Attempt at getting the Toon's name
        creatorName = TTLocalizer.WordPageNA
        av = self.air.doId2do.get(creatorAvId)
        if av:
            creatorName = av.getName()

        if originalUUID not in self.propInfo:
            self.sendUpdateToAvatarId(creatorAvId, 'propMessage', [ToontownGlobals.PROPS_ERROR])
            return

        originalProp = self.propInfo[originalUUID]
        propName, pos, hpr, scale, data = self.propInfo[originalUUID]

        if propName not in PropGlobals.PropList:
            self.sendUpdateToAvatarId(creatorAvId, 'propMessage', [ToontownGlobals.PROPS_ERROR])
            return

        # Don't generate this prop if the limit has been reached and the Toon isn't a builder
        propCount = len(list(self.propInfo.keys()))
        if propCount >= self.getMaxPropCount() and not self.getBuilder(av):
            self.sendUpdateToAvatarId(creatorAvId, 'propMessage', [ToontownGlobals.MAX_PROPS])
            return

        # Even if the Toon is a builder, don't generate passed our hard limit unless we're on dev
        if propCount >= PropGlobals.MaxPropCountHard and not __debug__:
            self.sendUpdateToAvatarId(creatorAvId, 'propMessage', [ToontownGlobals.MAX_PROPS_HARD])
            return

        # If prop spawning is locked and the Toon isn't a builder, we can't generate it
        if self.locked and not self.getBuilder(av):
            self.sendUpdateToAvatarId(creatorAvId, 'propMessage', [ToontownGlobals.PROPS_SPAWNING_LOCKED])
            return

        if creatorAvId in self.recentAvatars and not self.getBuilder(av):
            if self.recentAvatars.get(creatorAvId) >= 5:
                self.sendUpdateToAvatarId(creatorAvId, 'propMessage', [ToontownGlobals.PROPS_SPAMMING])
                return
            self.recentAvatars[creatorAvId] += 1

        if creatorAvId not in self.recentAvatars:
            self.recentAvatars[creatorAvId] = 1

        propUUID = str(uuid.uuid4())

        data['spawned_by_name'] = creatorName
        data['spawned_by_avid'] = creatorAvId
        data['spawned_on'] = spawnTime
        if newColorScale != (1.0, 1.0, 1.0, 1.0):
            data['color_scale'] = newColorScale
        self.updatePropInfo(propUUID, propName, newPos, newHpr, newScale, data)

        data = json.dumps(data)
        self.sendUpdate('spawnPropNew', [propUUID, propName, newPos, newHpr, newScale, data])

        self.backupProps()

    def updatePropInfo(self, propUUID: str, propName: str, pos: Vec3F, hpr: Vec3F, scale: Vec3F, data: Dict[str, Any]):
        self.propInfo[propUUID] = (propName, pos, hpr, scale, data)
        distProp = self.distributedProps.get(propUUID, None)
        if distProp:
            distProp.data.update(data)
            distProp.b_setPosHpr(*pos, *hpr)

    def requestUpdateProp(self, propUUID: str, pos: Vec3F, hpr: Vec3F, scale: Vec3F, data: bytes):
        """
        == Sent from a client ==
        Client told the server to update a prop, lets update it
        :param propUUID: UUID of the prop
        :param pos: Position to set the prop to
        :param hpr: Rotation to set the prop to
        :param scale: Scale to set the prop to
        :param data: dict (sent as a bytes json stream bc we cant send dicts over astron unless im braindead)
        """
        sender = self.air.getAvatarIdFromSender()
        if self.isBuildLot:
            if not self.getLotPrivilegesForAvatar(sender) & FLPermBuild:
                self.sendUpdateToAvatarId(sender, 'propMessage', [ToontownGlobals.PROPS_NO_PERMISSION])
                return

        # Timestamp for when our prop was edited
        dataDict = json.loads(data)
        if self.propInfo[propUUID][4].get('locked', False) and dataDict.get('locked', False):
            self.sendUpdateToAvatarId(sender, 'propMessage', [ToontownGlobals.PROP_LOCKED])
            return
        self.updatePropInfo(propUUID, self.propInfo[propUUID][0], pos, hpr, scale, dataDict)
        self.sendUpdate('updatePropNew', [propUUID, pos, hpr, scale, data])

        self.backupProps()

    def setLotPrivilegesForAvatar(self, avId: int, permFlags: int):
        self.buildLotPrivileges[avId] = permFlags

    def getLotPrivilegesForAvatar(self, avId: int) -> int:
        return self.buildLotPrivileges.get(avId, 0)

    def setEstateDoId(self, doId: int):
        if not self.isEstate:
            self.notify.error(f"Tried to set an estate doId on a PropGenAI that isn't in an estate. Zone id {self.zoneId}")
        self.estateDoId = doId