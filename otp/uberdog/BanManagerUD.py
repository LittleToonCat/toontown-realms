from direct.distributed.DistributedObjectGlobalUD import DistributedObjectGlobalUD
from direct.directnotify import DirectNotifyGlobal
from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.MsgTypes import CLIENTAGENT_EJECT

import os
import json
import hashlib
from datetime import datetime, timedelta


class BanManagerUD(DistributedObjectGlobalUD):
    notify = DirectNotifyGlobal.directNotify.newCategory('BanManagerUD')

    def __init__(self, air):
        DistributedObjectGlobalUD.__init__(self, air)

        self.banFilename = 'bans.json'
        self.muteFilename = 'mutes.json'
        self.hwIdBySender = {}
        self.uuidBySender = {}
        self.ipBySender = {}

        self.banJsonData = {}
        self.muteJsonData = {}

        for filename in (self.banFilename, self.muteFilename):
            if not os.path.isfile(filename):
                self.notify.info("Creating %s" % filename)
                with open(filename, 'w+') as file:
                    json.dump({}, file, indent=4)
                    file.close()

    def addClient(self, sender, hwId, uuid, ip):
        if sender not in self.hwIdBySender:
            self.hwIdBySender[sender] = hwId
            self.uuidBySender[sender] = uuid
            self.ipBySender[sender] = ip

    def removeClient(self, sender):
        if sender in self.hwIdBySender:
            self.hwIdBySender[sender] = None
            del self.hwIdBySender[sender]

        if sender in self.uuidBySender:
            self.uuidBySender[sender] = None
            del self.uuidBySender[sender]

        if sender in self.ipBySender:
            self.ipBySender[sender] = None
            del self.ipBySender[sender]

    def handleBan(self, accId, avId, name, modAvId, modName, minutes, reason):
        # First off, let's kick someone when we ban them
        self.handleKick(avId, reason, 2)

        # Now let's get the banned user's hwid
        hwId = self.hwIdBySender.get(int(accId))
        if not hwId:
            self.notify.warning("Tried to ban player with accId of {} but hwId is invalid!".format(accId))
            return

        # Let's decode the hwid now
        hwId = hwId.decode('utf-8')

        # Here is their UUID
        uuid = self.uuidBySender.get(int(accId))
        if not uuid:
            self.notify.warning("Tried to ban with accId of {} player but uuid is invalid!".format(accId))
            return
        uuid = uuid.decode('utf-8')

        # And their IP Address
        ip = self.ipBySender.get(int(accId))
        if not ip:
            self.notify.warning("Tried to ban with accId of {} player but ip is invalid!".format(accId))
            return

        # Time to do some sanity checks now
        accountIds = list(self.banJsonData.keys())
        hardwareIds = []
        universalIds = []
        ipAddresses = []
        for accountId in accountIds:
            banInfo = self.banJsonData.get(accountId)

            # The the ban time has expired, ignore this entry
            now = datetime.now()
            expire = banInfo.get('expire', 0)
            # If their expire time is 0, that means they are perma-banned
            if not isinstance(expire, int) and not expire == 0:
                if not isinstance(expire, datetime):
                    expire = datetime.strptime(expire, "%Y-%m-%d %H:%M:%S.%f")
                if expire < now:
                    accountIds.remove(accountId)
                    continue

            hardwareId = banInfo.get('hwId')
            hardwareIds.append(hardwareId)
            universalId = banInfo.get('uuid')
            universalIds.append(universalId)
            ipAddress = banInfo.get('ip')
            ipAddresses.append(ipAddress)

        accIdBanned = False
        hwIdBanned = False
        uuidBanned = False
        ipBanned = False

        if accId in accountIds:
            accIdBanned = True
        if hwId in hardwareIds:
            hwIdBanned = True
        if uuid in universalIds:
            uuidBanned = True
        if ip in ipAddresses:
            ipBanned = True

        if accIdBanned or hwIdBanned or uuidBanned or ipBanned:
            warningMessage = "Attempted to ban Toon with avId of {0} and accId of {1} but they're already banned!" \
                             " accIdBanned = {2} - {3}, hwIdBanned = {4} - {5}, uuidBanned = {6} - {7}, " \
                             "ipBanned = {8} - {9}".format(avId, accId, accIdBanned, accId, hwIdBanned, hwId,
                                                           uuidBanned, uuid, ipBanned, ip)
            self.notify.warning(warningMessage)
            return

        hwId = hwId.encode('utf-8')
        uuid = hashlib.sha512(uuid.encode('utf-8')).hexdigest()

        if minutes:
            expire = datetime.now() + timedelta(minutes=minutes)
        else:
            expire = minutes

        # We need to create our banning information
        ban = {"hwId": hwId,                                                     # A person's hardware ID
               "uuid": uuid,                                                     # A person's UUID, a unique identifier generated by Windows (and now Linux!)
               "ip": ip,                                                         # A person's IP Address
               "avId": avId,
               "name": name,
               "modAvId": modAvId,
               "modName": modName,
               "timestamp": datetime.now().strftime("%d-%b-%Y (%H:%M:%S.%f)"),   # Timestamp of when the person was banned
               "reason": reason,                                                 # The reason a person was banned
               "expire": expire}                                                 # How long a person's ban is for

        # Add our ban to the bans dict
        if str(accId) in list(self.banJsonData.keys()):
            del self.banJsonData[str(accId)]
        self.banJsonData[accId] = ban

        # Save our new ban dict to file
        with open(self.banFilename, "w") as file:
            data = json.dumps(self.banJsonData, indent=4, default=str)
            file.write(data)
            file.close()

    def handleKick(self, avId, reason, silent):
        puppet = self.GetPuppetConnectionChannel(avId)
        if not puppet:
            self.notify.warning("Got an invalid connection for avatar %d" % avId)
            return

        silent2code = {0: 1,
                       2: 152,
                       3: 155}

        self.dropConnection(puppet, silent2code.get(silent, 1), reason)

    def handleKickAccount(self, accId, reason, silent):
        puppet = self.GetAccountConnectionChannel(accId)
        if not puppet:
            self.notify.warning("Got an invalid connection for account %d" % accId)
            return

        silent2code = {0: 1,
                       2: 152,
                       3: 155}

        self.dropConnection(puppet, silent2code.get(silent, 1), reason)

    def handleMute(self, accId, avId, name, modAvId, modName, minutes, reason):
        if minutes:
            expire = datetime.now() + timedelta(minutes=minutes)
        else:
            expire = minutes

        # We need to create our banning information
        ban = {"avId": avId,
               "name": name,
               "modAvId": modAvId,
               "modName": modName,
               "timestamp": datetime.now().strftime("%d-%b-%Y (%H:%M:%S.%f)"),   # Timestamp of when the person was muted
               "reason": reason,                                                 # The reason a person was muted
               "expire": expire}                                                 # How long a person is muted for

        # Add our mute to the mute dict
        if str(accId) in list(self.muteJsonData.keys()):
            del self.muteJsonData[str(accId)]
        self.muteJsonData[accId] = ban

        # Save our new mute dict to file
        with open(self.muteFilename, "w") as file:
            data = json.dumps(self.muteJsonData, indent=4, default=str)
            file.write(data)
            file.close()

    def handleUnmute(self, accId):
        if str(accId) in list(self.muteJsonData.keys()):
            del self.muteJsonData[str(accId)]

        # Save our new ban dict to file
        with open(self.muteFilename, "w") as file:
            data = json.dumps(self.muteJsonData, indent=4, default=str)
            file.write(data)
            file.close()

    def dropConnection(self, connId, code, reason):
        self.notify.debug("Dropping connection %d code %d for %s" % (connId, code, reason))
        dg = PyDatagram()
        dg.addServerHeader(connId, self.air.ourChannel, CLIENTAGENT_EJECT)
        dg.addUint16(code)
        dg.addString(str(reason))
        self.air.send(dg)

    def openBanFile(self):
        with open(self.banFilename, "r") as file:
            self.banJsonData = json.load(file)
            file.close()
        return self.banJsonData

    def openMuteFile(self):
        with open(self.muteFilename, "r") as file:
            self.muteJsonData = json.load(file)
            file.close()
        return self.muteJsonData