from direct.directnotify import DirectNotifyGlobal
from direct.distributed.AstronInternalRepository import AstronInternalRepository
from direct.distributed.PyDatagram import PyDatagram
from otp.distributed import DCReader
from panda3d.direct import DCPacker

from otp.distributed.OtpDoGlobals import *


class FakeMessenger(object):
    """
    A fake NetMessenger class, so that extra logic isn't needed to check for netMessenger existence
    """

    def __init__(self, air, baseChannel=20000, baseMsgType=20000):
        return

    def clear(self):
        return

    def register(self, code, message):
        return

    def prepare(self, message, sentArgs=[]):
        return None

    def accept(self, message, *args):
        return

    def send(self, message, sentArgs=[]):
        return

    def handle(self, msgType, di):
        return


class ToontownInternalRepository(AstronInternalRepository):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToontownInternalRepository')
    GameGlobalsId = OTP_DO_ID_TOONTOWN
    dbId = 4003

    def __init__(self, baseChannel, serverId=None, dcFileNames=None, dcSuffix='AI', connectMethod=None,
                 threadedNet=None):
        AstronInternalRepository.__init__(self, baseChannel, serverId, dcFileNames, dcSuffix, connectMethod,
                                          threadedNet)
        self.__callbacks = {}

    def handleConnected(self):
        # Ehhh... screw it. Don't want to come up with super hacky logic just to tell the AI the UD restarted...
        if hasattr(self, 'netMessenger'):
            self.netMessenger.register(0, 'UdOnline')
            self.netMessenger.register(1, 'SetGamemode')    # 0 might have worked fine, but just in case it actually causes internal issues...
            self.netMessenger.register(2, 'SetEpisodeCompleted')
        else:
            self.netMessenger = FakeMessenger(self)
            self.notify.warning('Could not find a netMessenger to use; required messages for certain logic *will* fail!')

    def handleDatagram(self, di):
        msgType = self.getMsgType()

        if msgType in (STATESERVER_OBJECT_GET_FIELD_RESP,
                       STATESERVER_OBJECT_GET_FIELDS_RESP):
            self.handleGetFieldsResp(di)
        else:
            AstronInternalRepository.handleDatagram(self, di)

    def readDCFile(self, dcFileNames=None):
        return DCReader.readDCFile(self, dcFileNames)

    def getAvatarIdFromSender(self):
        return self.getMsgSender() & 0xFFFFFFFF

    def getAccountIdFromSender(self):
        return (self.getMsgSender() >> 32) & 0xFFFFFFFF

    def getSenderReturnChannel(self):
        return self.getMsgSender()

    def _isValidPlayerLocation(self, parentId, zoneId):
        if zoneId < 1000 and zoneId != 1:
            return False

        return True

    def sendUpdateToDoId(self, dclassName, fieldName, doId, args,
                         channelId=None):
        dclass=self.dclassesByName.get(dclassName + self.dcSuffix)
        assert dclass is not None
        if channelId is None:
            channelId=doId
        if dclass is not None:
            dg = dclass.aiFormatUpdate(
                    fieldName, doId, channelId, self.ourChannel, args)
            self.send(dg)

    def setAllowClientSend(self, avId, distObj, fieldNameList=[]):
        dg = PyDatagram()
        dg.addServerHeader(distObj.GetPuppetConnectionChannel(avId), self.ourChannel, CLIENTAGENT_SET_FIELDS_SENDABLE)
        fieldIds = []
        for fieldName in fieldNameList:
            field = distObj.dclass.getFieldByName(fieldName)
            if field:
                fieldIds.append(field.getNumber())

        dg.addUint32(distObj.getDoId())
        dg.addUint16(len(fieldIds))
        for fieldId in fieldIds:
            dg.addUint16(fieldId)

        self.send(dg)

    def getFieldsFromActiveObject(self, doId, dclass, fieldNameList, callback):
        ctx = self.getContext()
        self.__callbacks[ctx] = (doId, callback)

        fieldIds = []
        for fieldName in fieldNameList:
            field = dclass.getFieldByName(fieldName)
            if field:
                fieldIds.append(field.getNumber())

        dg = PyDatagram()
        dg.addServerHeader(doId, self.ourChannel, STATESERVER_OBJECT_GET_FIELDS)
        dg.addUint32(ctx)
        dg.addUint32(doId)
        dg.addUint16(len(fieldIds))
        for fieldId in fieldIds:
            dg.addUint16(fieldId)

        self.send(dg)

    def handleGetFieldsResp(self, di):
        ctx = di.getUint32()
        callback = self.__callbacks.get(ctx)
        if not callback:
            self.notify.warning('No context for GET_FIELDS!')
            return
        doId = callback[0]
        success = di.getUint8()

        fieldCount = di.getUint16()

        unpacker = DCPacker()
        unpacker.setUnpackData(di.getRemainingBytes())
        fields = {}
        for x in range(fieldCount):
            fieldId = unpacker.rawUnpackUint16()
            field = self.getDcFile().getFieldByIndex(fieldId)

            if not field:
                self.notify.error('Received bad field %d in query for'
                                  ' %s object' % (fieldId, dclass.getName()))

            unpacker.beginUnpack(field)
            fields[field.getName()] = list(field.unpackArgs(unpacker))
            unpacker.endUnpack()

        callback[1](doId, success, fields)

        del self.__callbacks[ctx]

    def packDclassValueDict(self, dclass, fieldDict):
        '''
        Converts {fieldName: fieldValue} dictionaries to
        {fieldName: packedFieldValue} dictionary.

        Useful for converting values returned from from Astron's Database
        interface to something more OTP compatible (for dObj.directUpdate or
        dObj.initFromServerResponse calls).
        '''

        valueDict = {}
        packer = DCPacker()

        for fieldName in fieldDict:
            field = dclass.getFieldByName(fieldName)

            packer.beginPack(field)
            field.packArgs(packer, fieldDict[fieldName])
            packer.endPack()

            valueDict[fieldName] = packer.getBytes()
            packer.clearData()

        return valueDict

    def generateObjectFromDatabase(self, doId, callback, fieldNames=()):
        '''
        Fetches the specified object's fields from the database
        and generates a class with them.

        Calls the callback with an distributed object instance
        if doId exists in database, None otherwise.
        '''

        def __getQuery(dclass, fields):
            if (dclass, fields) == (None, None):
                self.notify.warning(f'generateObjectFromDatabase returned None for doId {doId}!')
                callback(None)
                return

            self.notify.info(f'generateObjectFromDatabase: Generating {dclass.getName()} with doId {doId}.')

            valueDict = self.packDclassValueDict(dclass, fields)

            classDef = dclass.getClassDef()
            dObj = classDef(self)
            dObj.doId = doId
            dObj.dclass = dclass
            dObj.doNotDeallocateChannel = 1

            dObj.generate()
            dObj.initFromServerResponse(valueDict)
            dObj.announceGenerate()

            callback(dObj)

        # Query the object fields from the database.
        self.dbInterface.queryObject(self.dbId, doId, __getQuery, fieldNames)

    def generateTemporaryAvatar(self, avId, parentId, zoneId, required, other={}):
        dclass = self.dclassesByName['DistributedTemporaryToon' + self.dcSuffix]
        dcPacker = DCPacker()

        dg = PyDatagram()
        dg.addServerHeader(self.serverId, self.ourChannel, STATESERVER_CREATE_OBJECT_WITH_REQUIRED if not other else STATESERVER_CREATE_OBJECT_WITH_REQUIRED_OTHER)
        dg.addUint32(avId)
        dg.addUint32(parentId)
        dg.addUint32(zoneId)
        dg.addUint16(dclass.getNumber())

        for curField in range(dclass.getNumInheritedFields()):
            field = dclass.getInheritedField(curField)
            if field.isRequired() and not field.asMolecularField():
                dcPacker.beginPack(field)
                if field.getName() in required:
                    dcPacker.packObject(required[field.getName()])
                else:
                    dcPacker.packDefaultValue()
                if not dcPacker.endPack():
                    self.notify.error('Error has occurred while trying to pack field %s%r' % (field.getName(), required.get(field.getName())))
                    return

        if other:
            dcPacker.rawPackUint16(len(other))
            for name in other:
                field = dclass.getFieldByName(name)
                if not field:
                    self.notify.error('Field %s doesn\'t exist!')
                    return

                dcPacker.rawPackUint16(field.getNumber())
                dcPacker.beginPack(field)
                dcPacker.packObject(other[name])
                if not dcPacker.endPack():
                    self.notify.error('Error has occurred while trying to pack field %s%r' % (field.getName(), other.get(field.getName())))
                    return

        dg.appendData(dcPacker.getBytes())
        self.send(dg)

    def isGameLive(self):
        """
        Returns True if the game is a live build, else False for a local environment (source)
        """
        try:
            # reuse this if we can
            return simbase.isGameLive()
        except (AttributeError, NameError):
            # if we can't, use this copypasta from AIBase (which exists there to setup logging in there)
            if __debug__:
                return False
            return True
