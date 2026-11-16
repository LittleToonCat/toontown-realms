from copy import deepcopy
import datetime
import json
from math import floor
import os
import shutil
from threading import Lock
from direct.directnotify.DirectNotifyGlobal import directNotify
from toontown.parties.PartyGlobals import MaxSetHostedParties, MaxSetPartiesInvitedTo
from direct.discord_rpc.util.utils import iter_items
from otp.otpbase.PythonUtil import cmp_to_key



class CalendarBackup(object):
    # Don't load this or any class that inherits from this from the client
    notify = directNotify.newCategory('CalendarBackup')
    __serverDataFolder = simbase.config.GetString('server-data-folder', '')

    def __init__(self, backupName):
        if not isinstance(backupName, (type(''), type(b''))):
            raise TypeError('backup name must be a unicode/bytes string!')
        self.__ourDataFolder = os.path.join(self.__serverDataFolder, 'calendar')
        self.__backupName = backupName
        self.__filename = os.path.join(self.__ourDataFolder, self.__backupName + '.json')
        self._dataLock = Lock()
        self.__loadData()

    def __loadData(self):
        self._data = {}
        if not os.path.exists(self.__ourDataFolder):
            # calendar events to save; so far, it's just parties
            os.mkdir(self.__ourDataFolder)
        else:
            if os.path.exists(self.filename):
                if os.path.isfile(self.filename):
                    with open(self.filename, 'r') as f:
                        tmp = json.load(f)
                    self._parseLoadData(tmp)
                elif os.path.isdir(self.filename):
                    # it'd be a *shame* if you stored important data in this oddly named directory...
                    shutil.rmtree(self.filename)

    def _parseLoadData(self, filedata):
        # default for reading in data; overwrite if needed
        i = 0
        with self._dataLock:
            for _, data in iter_items(filedata):
                # in case some moron changes 'IDs' manually in the files
                self._data[i] = data
                i += 1

    def _validateData(self, data):
        # overwrite this if you need to validate data, but use the default addData()
        return True

    def getData(self):
        tmp = []
        for _, data in iter_items(self._data):
            tmp.append(data)
        return deepcopy(tmp)

    def addData(self, data):
        if self._validateData(data):
            with self._dataLock:
                nextId = len(self._data)
                self._data[nextId] = deepcopy(data)
                with open(self.filename, 'w') as f:
                    json.dump(self._data, f)
        else:
            self.notify.warning('Failed to add data!')

    def reloadData(self):
        # only call this if needed (example: reload data on AI if change in UD)
        self.__loadData()

    @property
    def filename(self):
        return self.__filename


class PartyBackup(CalendarBackup):
    notify = directNotify.newCategory('PartyBackup')

    def __init__(self):
        # append to calendar party data in form of following:
        # [hostId, [startTime data], [endTime data], [inviteeIDs], isPrivate, theme, status]
        # TODO(maybe): prune archived parties older than certain time (example: 3 months)
        CalendarBackup.__init__(self, 'party')

    @staticmethod
    def __getEpochSeconds(year, month, day, hour, minute):
        # might as well make this do the things, since i'm gonna fix up other party things
        return simbase.air.time.timestamp(year=year,
                                          month=month,
                                          day=day,
                                          hour=hour,
                                          minute=minute)

    def __generateDataId(self, data):
        # basically generates a unique ID for each archived party
        sTime = self.__getEpochSeconds(data[1][0], data[1][1], data[1][2], data[1][3], data[1][4])
        # shouldn't need to floor, but just in case
        return "{stsec}{hid}".format(stsec=int(floor(sTime)), hid=data[0])

    def _parseLoadData(self, filedata):
        with self._dataLock:
            for _, data in iter_items(filedata):
                self._data[self.__generateDataId(data)] = data

    def getData(self, hostId=None, inviteeId=None):
        if hostId is not None and inviteeId is not None:
            self.notify.error('Only use one or the other, not both!')
        elif hostId is not None or inviteeId is not None:
            def timeCmp(cmp1, cmp2):
                if cmp1[0] < cmp2[0]:
                    return -1
                elif cmp1[0] == cmp2[0]:
                    return 0
                else:
                    return 1

            cmpTmp = []
            for _, data in iter_items(self._data):
                if hostId is not None and hostId == data[0]:
                    cmpTmp.append([datetime.datetime(*data[1], tzinfo=self.tzinfo), data])
                elif inviteeId is not None and inviteeId in data[3]:
                    cmpTmp.append([datetime.datetime(*data[1], tzinfo=self.tzinfo), data])
            cmpTmp.sort(key=cmp_to_key(timeCmp))
            if hostId is not None:
                if len(cmpTmp) > MaxSetHostedParties:
                    cmpTmp = cmpTmp[-MaxSetHostedParties:]
            elif inviteeId is not None:
                if len(cmpTmp) > MaxSetPartiesInvitedTo:
                    cmpTmp = cmpTmp[-MaxSetPartiesInvitedTo:]
            tmp = []
            for _, data in cmpTmp:
                tmp.append(data)
            return deepcopy(tmp)
        else:
            return CalendarBackup.getData(self)

    def _validateData(self, data, asError=False):
        # I guess some basic checks to make sure party data is more or less correct...
        eStr = None
        if not isinstance(data, (tuple, list)):
            eStr = 'Party data must be of type tuple/list!'
        if len(data) != 7:
            eStr = 'Party data is malformed (incorrect size)!'
        if len(data[1]) != 5 or len(data[2]) != 5:
            eStr = 'Party start/end parameters are malformed (incorrect size)!'
        if eStr is not None:
            if asError:
                self.notify.error(eStr)
            else:
                self.notify.warning(eStr)
                return False
        return True

    def addData(self, data):
        data = deepcopy(data)
        if self._validateData(data):
            # everything more or less checks out; actually append data
            with self._dataLock:
                self._data[self.__generateDataId(data)] = data
                with open(self.filename, 'w') as f:
                    json.dump(self._data, f)
        else:
            self.notify.warning('Failed to add party to archive!')

    def deleteData(self, data):
        # I plan to use this to basically remove parties that are going on in the AI but were added here by the
        # restarted UD, who will end up getting the party info later
        if self._validateData(data):
            did = self.__generateDataId(data)
            if did in self._data:
                with self._dataLock:
                    del self._data[did]
                    if len(self._data) > 0:
                        with open(self.filename, 'w') as f:
                            json.dump(self._data, f)
                    else:
                        # No more data? no need for a file with no content!
                        os.remove(self.filename)
            else:
                self.notify.debug("Data doesn't exist in party archive; ignoring.")
        else:
            self.notify.warning('Failed to remove party from archive!')

    @property
    def tzinfo(self):
        return simbase.air.toontownTimeManager.serverTimeZone
