from panda3d.core import *
from direct.distributed import DistributedObject
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import ToontownGlobals, ClientSettings
from toontown.toonbase import ToontownBattleGlobals
from toontown.toonbase import TTLocalizer
from toontown.suit.SuitDNA import suitDeptFullnames, getDeptFullnameP
from . import HolidayDecorator
from . import HalloweenHolidayDecorator
from . import CrashedLeaderBoardDecorator
from direct.interval.IntervalGlobal import *
import calendar
from copy import deepcopy
from toontown.social.SocialGlobals import ELoginPopupTypes
from toontown.hood import ZoneUtil
from ..datapack.DataPackManager import DataPackManager
from ..toonbase.ToontownTypes import CogAppearanceIndex

decorationHolidays = [ToontownGlobals.WINTER_DECORATIONS,
 ToontownGlobals.WACKY_WINTER_DECORATIONS,
 ToontownGlobals.HALLOWEEN_PROPS,
 ToontownGlobals.SPOOKY_PROPS,
 ToontownGlobals.HALLOWEEN_COSTUMES,
 ToontownGlobals.SPOOKY_COSTUMES,
 ToontownGlobals.CRASHED_LEADERBOARD]

holidaySCMenus = {
    ToontownGlobals.WINTER_DECORATIONS: 'winter', # 4
    ToontownGlobals.WACKY_WINTER_DECORATIONS: 'winter', # 121
    ToontownGlobals.WINTER_CAROLING: 'carol', # 57
    ToontownGlobals.WACKY_WINTER_CAROLING: 'carol', # 122
    ToontownGlobals.HALLOWEEN_PROPS: 'halloween', # 26
    ToontownGlobals.SPOOKY_PROPS: 'halloween', # 119
    ToontownGlobals.APRIL_FOOLS_COSTUMES: 'aprilToons', # 29
    ToontownGlobals.SILLY_CHATTER_ONE: 'sillyMenuOne', # 67
    ToontownGlobals.SILLY_CHATTER_TWO: 'sillyMenuTwo', # 68
    ToontownGlobals.SILLY_CHATTER_THREE: 'sillyMenuThree', # 69
    ToontownGlobals.SILLY_CHATTER_FOUR: 'sillyMenuFour', # 70
    ToontownGlobals.SILLY_CHATTER_FIVE: 'sillyMenuFive', # 94
    ToontownGlobals.VICTORY_PARTY_HOLIDAY: 'victoryParties', # 95
    ToontownGlobals.SELLBOT_NERF_HOLIDAY: 'sellbotNerf', # 96
    ToontownGlobals.JELLYBEAN_TROLLEY_HOLIDAY: 'jellybeanTrolley', # 97
    ToontownGlobals.JELLYBEAN_TROLLEY_HOLIDAY_MONTH: 'jellybeanTrolley', # 113
    ToontownGlobals.JELLYBEAN_FISHING_HOLIDAY: 'jellybeanFishing', # 98
    ToontownGlobals.JELLYBEAN_FISHING_HOLIDAY_MONTH: 'jellybeanFishing', # 114
    ToontownGlobals.JELLYBEAN_PARTIES_HOLIDAY: 'jellybeanParties', # 99
    ToontownGlobals.JELLYBEAN_PARTIES_HOLIDAY_MONTH: 'jellybeanParties', # 115
    ToontownGlobals.SELLBOT_INVASION: 'sellbotInvasion', # 102
    ToontownGlobals.SELLBOT_FIELD_OFFICE: 'sellbotFieldOffice', # 103
    ToontownGlobals.IDES_OF_MARCH: 'idesOfMarch' # 105
}

MAX_COG_LIST_STR_LEN = 4
COG_ICONS = 'phase_3/models/gui/cog_icons'
HOLIDAY_MSG_DICT = TTLocalizer.HolidayNotificationMessage # type: dict
HOLIDAY_NOTI_ICONS = TTLocalizer.HolidayNotificationIcons # type: dict


class NewsManager(DistributedObject.DistributedObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('NewsManager')
    neverDisable = 1
    YearlyHolidayType = 1
    OncelyHolidayType = 2
    RelativelyHolidayType = 3
    OncelyMultipleStartHolidayType = 4

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)
        self.invading = 0
        self.decorationHolidayIds = []
        self.holidayDecorator = None
        self.holidayIdList = []
        base.cr.newsManager = self
        base.localAvatar.inventory.setInvasionCreditMultiplier(1)
        self.weeklyCalendarHolidays = []
        self.initialized = False

    def delete(self):
        self.cr.newsManager = None
        if self.holidayDecorator:
            self.holidayDecorator.exit()
        DistributedObject.DistributedObject.delete(self)

    def sendSystemMessage(self, message, style):
        base.localAvatar.setSystemMessage(style, message)

    def buildCogInvasionName(self, cogList, msgType):
        if len(cogList) >= MAX_COG_LIST_STR_LEN:
            if msgType == ToontownGlobals.SuitInvasionEnd:
                return TTLocalizer.MultipleInvasionPrefix, TTLocalizer.Cog, ''
            return TTLocalizer.MultipleInvasionPrefix, '', TTLocalizer.Cogs

        singularNames = []
        pluralNames = []

        for cog in cogList:
            if cog.capitalize() in suitDeptFullnames.values():
                singularNames.append(
                    cog.capitalize()
                )
                pluralNames.append(
                    getDeptFullnameP(ToontownGlobals.Dept2NameDept.get(cog.capitalize()))
                )
            else:
                singularNames.append(
                    DataPackManager.getLocalizedText(base.cr.dataPackMgr.getCogAppearance(cog)[CogAppearanceIndex.NAME])
                )
                pluralNames.append(
                    DataPackManager.getLocalizedText(base.cr.dataPackMgr.getCogAppearance(cog)[CogAppearanceIndex.NAME_PLURAL])
                )

        if len(cogList) == 2:
            cogName = f" {TTLocalizer.And} ".join(singularNames)
            cogNameP = f" {TTLocalizer.And} ".join(pluralNames)
        else:
            cogName = ''
            cogNameP = ''
            for i in range(len(cogList)):
                if i == len(cogList) - 1:
                    cogName += '{0} {1}'.format(TTLocalizer.And, singularNames[i])
                    cogNameP += '{0} {1}'.format(TTLocalizer.And, pluralNames[i])
                else:
                    cogName += '{0}, '.format(singularNames[i])
                    cogNameP += '{0}, '.format(pluralNames[i])                

        return '', cogName, cogNameP

    def getInvadingCogMessage(self, cogList, special, virtual, msgType):
        firstCog = cogList[0]
        invPrefix = ''
        if len(cogList) > 1:
            invPrefix, cogName, cogNameP = self.buildCogInvasionName(cogList, msgType)
        elif firstCog.capitalize() in suitDeptFullnames.values():
            cogName = cogList[0].capitalize()
            cogNameP = getDeptFullnameP(ToontownGlobals.Dept2NameDept.get(firstCog.capitalize()))
        else:
            cogName = DataPackManager.getLocalizedText(base.cr.dataPackMgr.getCogAppearance(firstCog)[CogAppearanceIndex.NAME])
            cogNameP = DataPackManager.getLocalizedText(base.cr.dataPackMgr.getCogAppearance(firstCog)[CogAppearanceIndex.NAME_PLURAL])
        if special == 1:
            cogName = TTLocalizer.Skeleton
            cogNameP = TTLocalizer.SkeletonP
        elif special == 2 and not virtual:
            cogName = TTLocalizer.SkeleRevive + cogName
            cogNameP = TTLocalizer.SkeleRevive + cogNameP
        if virtual and special == 2:
            cogName = TTLocalizer.Virtual + TTLocalizer.SkeleRevive + cogName
            cogNameP = TTLocalizer.Virtual + TTLocalizer.SkeleRevive + cogNameP
        elif virtual:
            cogName = TTLocalizer.Virtual + cogName
            cogNameP = TTLocalizer.Virtual + cogNameP
        if msgType in [ToontownGlobals.SuitInvasionBegin, ToontownGlobals.SuitInvasionUpdate, ToontownGlobals.SuitInvasionBulletin]:
            body = TTLocalizer.SuitInvasionBegin.format(invPrefix + cogNameP)
            self.invading = 1
        elif msgType == ToontownGlobals.SuitInvasionEnd:
            body = TTLocalizer.SuitInvasionEnd.format(invPrefix + cogName)
            self.invading = 0
        else:
            self.notify.warning(f'getInvadingCogMessage() invalid msgType: {msgType}')
        return body

    def setInvasionStatus(self, msgType, cogList, numRemaining, special, virtual, mega):
        self.notify.info(f'setInvasionStatus(msgType: {msgType}, cogList: {cogList}, numRemaining: {numRemaining}, skeleton: {special}, virtual: {virtual})')
        if self.invading:
            mult = ToontownBattleGlobals.getInvasionMultiplier()
        else:
            mult = 1
        base.localAvatar.inventory.setInvasionCreditMultiplier(mult)

        specialDict = {
            0: 'Cog',
            1: 'Skelecog',
            2: 'V2.0 Cog'
        }
        virtualDict = {
            0: '',
            1: 'Virtual'
        }
        depts = {'sellbot': 'SalesIcon', 
                 'cashbot': 'MoneyIcon', 
                 'lawbot': 'LegalIcon', 
                 'bossbot': 'CorpIcon'}
        title = f'{virtualDict[virtual]} {specialDict[special]} Invasion'.strip()
        icon = loader.loadModel(COG_ICONS).find('**/cog')
        base.localAvatar.sendNotification(
                title = title,
                body = self.getInvadingCogMessage(cogList, special, virtual, msgType),
                icon = icon,
                id = "cog_inv",
        )

    def setOnlineStatus(self, online, doId, name):
        loginPopupSetting = ClientSettings.LoginMessages.get()
        if doId == base.localAvatar.doId or loginPopupSetting == ELoginPopupTypes.FRIENDS and not base.cr.isFriend(doId) or \
                loginPopupSetting == ELoginPopupTypes.NO_ONE:
            return

        # If this avatar is going offline and it isn't a friend, make the message unclickable.
        if not online and doId not in base.cr.offlineFriends:
            doId = 0

        if not base.localAvatar.tutorialAck:
            return

        if base.cr.getChatFilterMode() == ToontownGlobals.CHAT_FILTER_CENSOR:
            name = base.profanityFilter.censor(name)

        if online:
            msg = TTLocalizer.WhisperAvatarComingOnline
        else:
            msg = TTLocalizer.WhisperAvatarLoggedOut
        base.localAvatar.setSystemMessage(doId, msg % name)

    def getInvading(self):
        return self.invading

    def startHoliday(self, holidayId):
        if holidayId not in self.holidayIdList:
            self.holidayIdList.append(holidayId)

            # Decorate the playgrounds
            if holidayId in decorationHolidays:
                self.decorationHolidayIds.append(holidayId)
                if hasattr(base.cr.playGame, 'dnaStore') and hasattr(base.cr.playGame, 'hood') and hasattr(base.cr.playGame.hood, 'loader'):
                    if holidayId == ToontownGlobals.HALLOWEEN_COSTUMES or holidayId == ToontownGlobals.SPOOKY_COSTUMES: # 27, 120
                        if hasattr(base, 'localAvatar') and base.localAvatar and not ZoneUtil.isBetaPlaygroundZone(base.localAvatar.zoneId):
                            self.holidayDecorator = HalloweenHolidayDecorator.HalloweenHolidayDecorator()
                    elif holidayId == ToontownGlobals.CRASHED_LEADERBOARD: # 30
                        if hasattr(base, 'localAvatar') and base.localAvatar and not ZoneUtil.isBetaPlaygroundZone(base.localAvatar.zoneId):
                            self.holidayDecorator = CrashedLeaderBoardDecorator.CrashedLeaderBoardDecorator()
                    else:
                        if hasattr(base, 'localAvatar') and base.localAvatar and not ZoneUtil.isBetaPlaygroundZone(base.localAvatar.zoneId):
                            self.holidayDecorator = HolidayDecorator.HolidayDecorator()
                    if hasattr(self, 'holidayDecorator') and self.holidayDecorator:
                        self.holidayDecorator.decorate()
                    messenger.send(f'decorator-holiday-{holidayId}-starting')

            # Add Speedchat Menu's
            if holidayId in holidaySCMenus:
                if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                    base.localAvatar.chatMgr.chatInputSpeedChat.addHolidayMenu(holidaySCMenus[holidayId])
            elif holidayId == ToontownGlobals.ELECTION_PROMOTION: # 8
                if hasattr(base, 'TTSCPromotionalMenu'):
                    base.TTSCPromotionalMenu.startHoliday(holidayId)

            # Other holiday events
            if holidayId == ToontownGlobals.HYDRANT_ZERO_HOLIDAY: # 58
                messenger.send('HydrantZeroIsRunning', [True])
            elif holidayId == ToontownGlobals.VALENTINES_DAY: # 59
                messenger.send('ValentinesDayStart')
            elif holidayId == ToontownGlobals.SPOOKY_BLACK_CAT: # 117
                if hasattr(base, 'cr') and base.cr and hasattr(base.cr, 'toons') and base.cr.toons:
                    for currToon in list(base.cr.toons.values()):
                        currToon.setDNA(currToon.style.clone())

            # Tell the Toon HQ's!
            if holidayId in HOLIDAY_MSG_DICT:
                messenger.send('notifyHolidayStart', [HOLIDAY_MSG_DICT[holidayId][1]])

            # Send the notification
            self.sendHolidayNotification(holidayId)
            self.notify.info(f'Starting Holiday {holidayId}')

    def endHoliday(self, holidayId):
        if holidayId in self.holidayIdList:
            self.holidayIdList.remove(holidayId)

            # Remove the decorations
            if holidayId in self.decorationHolidayIds:
                self.decorationHolidayIds.remove(holidayId)
                if hasattr(base.cr.playGame, 'dnaStore') and hasattr(base.cr.playGame, 'hood') and hasattr(base.cr.playGame.hood, 'loader'):
                    if holidayId == ToontownGlobals.HALLOWEEN_COSTUMES or holidayId == ToontownGlobals.SPOOKY_COSTUMES:
                        self.holidayDecorator = HalloweenHolidayDecorator.HalloweenHolidayDecorator()
                    elif holidayId == ToontownGlobals.CRASHED_LEADERBOARD:
                        self.holidayDecorator = CrashedLeaderBoardDecorator.CrashedLeaderBoardDecorator()
                    else:
                        self.holidayDecorator = HolidayDecorator.HolidayDecorator()
                    self.holidayDecorator.undecorate()
                    messenger.send(f'decorator-holiday-{holidayId}-ending')

            # Remove Speedchat Menu's
            if holidayId in holidaySCMenus:
                if hasattr(base, 'localAvatar') and base.localAvatar and hasattr(base.localAvatar, 'chatMgr') and base.localAvatar.chatMgr:
                    base.localAvatar.chatMgr.chatInputSpeedChat.removeHolidayMenu(holidaySCMenus[holidayId])
            elif holidayId == ToontownGlobals.ELECTION_PROMOTION: # 8
                if hasattr(base, 'TTSCPromotionalMenu'):
                    base.TTSCPromotionalMenu.endHoliday(holidayId)

            # Other holiday events
            if holidayId == ToontownGlobals.HYDRANT_ZERO_HOLIDAY:
                messenger.send('HydrantZeroIsRunning', [False])
            elif holidayId == ToontownGlobals.VALENTINES_DAY:
                messenger.send('ValentinesDayStop')
            elif holidayId == ToontownGlobals.SPOOKY_BLACK_CAT:
                if hasattr(base, 'cr') and base.cr and hasattr(base.cr, 'toons') and base.cr.toons:
                    for currToon in list(base.cr.toons.values()):
                        currToon.setDNA(currToon.style.clone())

            # Tell the ToonHQ's!
            if holidayId in HOLIDAY_MSG_DICT:
                messenger.send('notifyHolidayEnd', [f'{HOLIDAY_MSG_DICT[holidayId][0]} has ended.'])

            # Send the notification
            self.sendHolidayNotification(holidayId, end=True)
            self.notify.info(f'Ending Holiday {holidayId}')


    def setHolidayIdList(self, holidayIdList):

        def isEnding(id):
            return id not in holidayIdList

        def isStarting(id):
            return id not in self.holidayIdList

        toEnd = list(filter(isEnding, self.holidayIdList))
        for endingHolidayId in toEnd:
            self.endHoliday(endingHolidayId)

        toStart = list(filter(isStarting, holidayIdList))
        for startingHolidayId in toStart:
            self.startHoliday(startingHolidayId)

        messenger.send('setHolidayIdList', [holidayIdList])

    def getDecorationHolidayId(self):
        return self.decorationHolidayIds

    def getHolidayIdList(self):
        return self.holidayIdList

    def notifyHardcoreBossWon(self, numToons, dept):
        base.localAvatar.setSystemMessage(0, TTLocalizer.HardcoreBossNotifyText[dept].format(numToons, TTLocalizer.ToonS if numToons == 1 else TTLocalizer.ToonP))

    def setBingoWin(self, zoneId):
        placeNameData = TTLocalizer.GlobalStreetNames.get(zoneId)
        if placeNameData:
            # the place's name
            placeName = placeNameData[-1]
            # string like "in" or "on"
            placeNameIn = placeNameData[1]
            # ex would be in Toontown Central or on Seaweed Street
            if placeName == TTLocalizer.GlobalStreetNames[1000][-1]:
                placeName = base.cr.hoodMgr.getFullnameFromId(ZoneUtil.getCanonicalHoodId(zoneId))
            self.notifyOfHoliday(TTLocalizer.BlockoutWin % (placeNameIn, placeName), name='End')

    def setBingoStart(self):
        self.sendHolidayNotification(ToontownGlobals.FISH_BINGO_NIGHT)

    def setBingoEnd(self):
        self.sendHolidayNotification(ToontownGlobals.FISH_BINGO_NIGHT, end = True)

    def setPokerStart(self):
        self.sendHolidayNotification(ToontownGlobals.FISH_POKER)

    def setPokerEnd(self):
        self.sendHolidayNotification(ToontownGlobals.FISH_POKER, end = True)

    def setCircuitRaceStart(self):
        self.sendHolidayNotification(ToontownGlobals.CIRCUIT_RACING)

    def setCircuitRaceEnd(self):
        self.sendHolidayNotification(ToontownGlobals.CIRCUIT_RACING, end = True)

    def setTrolleyHolidayStart(self):
        self.sendHolidayNotification(ToontownGlobals.TROLLEY_HOLIDAY)

    def setTrolleyHolidayEnd(self):
        self.sendHolidayNotification(ToontownGlobals.TROLLEY_HOLIDAY, end = True)

    def setTrolleyWeekendStart(self):
        self.notifyOfHoliday(TTLocalizer.TrolleyWeekendStart)

    def setTrolleyWeekendEnd(self):
        self.notifyOfHoliday(TTLocalizer.TrolleyWeekendEnd, name='End')

    def setRoamingTrialerWeekendStart(self):
        self.notifyOfHoliday(TTLocalizer.RoamingTrialerWeekendStart)
        base.roamingTrialers = True

    def setRoamingTrialerWeekendOngoing(self):
        self.notifyOfHoliday(TTLocalizer.RoamingTrialerWeekendOngoing, name='Ongoing')
        base.roamingTrialers = True

    def setRoamingTrialerWeekendEnd(self):
        self.notifyOfHoliday(TTLocalizer.RoamingTrialerWeekendEnd, name='End')
        base.roamingTrialers = False

    def holidayNotify(self):
        for id in self.holidayIdList:
            if id == ToontownGlobals.SILLY_SATURDAY_BINGO:
                self.setBingoStart()
            elif id == ToontownGlobals.SILLY_SATURDAY_CIRCUIT:
                self.setCircuitRaceStart()
            elif id == ToontownGlobals.SILLY_SATURDAY_TROLLEY:
                self.setTrolleyHolidayStart()
            elif id == ToontownGlobals.ROAMING_TRIALER_WEEKEND:
                self.setRoamingTrialerWeekendOngoing()

    def notifyOfHoliday(self, msg, name='Start'):
        messenger.send(f'notifyHoliday{name}', [msg])
        base.localAvatar.setSystemMessage(0, msg)

    def sendHolidayNotification(self, holidayId, end = 0):
        if holidayId not in HOLIDAY_MSG_DICT:
            return

        title = HOLIDAY_MSG_DICT[holidayId][0]
        if end:
            body = f'{HOLIDAY_MSG_DICT[holidayId][0]} has ended.'
        else:
            body = HOLIDAY_MSG_DICT[holidayId][1]

        # TODO: Get rid of the conditional statement once all icons are finished
        # TODO: Remove mega invasions from the holiday system. Spawn mega invasions with new command
        if holidayId in HOLIDAY_NOTI_ICONS:
            iconModel = loader.loadModel(HOLIDAY_NOTI_ICONS[holidayId][0])
            icon = iconModel.find(f'**/{HOLIDAY_NOTI_ICONS[holidayId][1]}')
            iconModel.removeNode()
            icon.clearBillboard()
        else:
            icon = loader.loadModel('phase_3/models/gui/ttrm_m_gui_chat_emojis').find('**/realms')
        base.localAvatar.sendNotification(
                title = title,
                body = body,
                icon = icon,
                id = f"holiday_{holidayId}",
                allowDuplicateIds = False
        )

    def setWeeklyCalendarHolidays(self, weeklyCalendarHolidays):
        self.weeklyCalendarHolidays = weeklyCalendarHolidays

    def getHolidaysForWeekday(self, day):
        result = []
        for item in self.weeklyCalendarHolidays:
            if item[1] == day:
                result.append(item[0])

        return result

    def setYearlyCalendarHolidays(self, yearlyCalendarHolidays):
        self.yearlyCalendarHolidays = yearlyCalendarHolidays

    def getYearlyHolidaysForDate(self, theDate):
        result = []
        for item in self.yearlyCalendarHolidays:
            if item[1][0] == theDate.month and item[1][1] == theDate.day:
                newItem = [self.YearlyHolidayType] + list(item)
                result.append(tuple(newItem))
                continue
            if item[2][0] == theDate.month and item[2][1] == theDate.day:
                newItem = [self.YearlyHolidayType] + list(item)
                result.append(tuple(newItem))

        return result

    def setMultipleStartHolidays(self, multipleStartHolidays):
        self.multipleStartHolidays = multipleStartHolidays

    def getMultipleStartHolidaysForDate(self, theDate):
        result = []
        for theHoliday in self.multipleStartHolidays:
            times = theHoliday[1:]
            tempTimes = times[0]
            for startAndStopTimes in tempTimes:
                startTime = startAndStopTimes[0]
                endTime = startAndStopTimes[1]
                if startTime[0] == theDate.year and startTime[1] == theDate.month and startTime[2] == theDate.day:
                    fakeOncelyHoliday = [theHoliday[0], startTime, endTime]
                    newItem = [self.OncelyMultipleStartHolidayType] + fakeOncelyHoliday
                    result.append(tuple(newItem))
                    continue
                if endTime[0] == theDate.year and endTime[1] == theDate.month and endTime[2] == theDate.day:
                    fakeOncelyHoliday = [theHoliday[0], startTime, endTime]
                    newItem = [self.OncelyMultipleStartHolidayType] + fakeOncelyHoliday
                    result.append(tuple(newItem))

        return result

    def setOncelyCalendarHolidays(self, oncelyCalendarHolidays):
        self.oncelyCalendarHolidays = oncelyCalendarHolidays

    def getOncelyHolidaysForDate(self, theDate):
        result = []
        for item in self.oncelyCalendarHolidays:
            if item[1][0] == theDate.year and item[1][1] == theDate.month and item[1][2] == theDate.day:
                newItem = [self.OncelyHolidayType] + list(item)
                result.append(tuple(newItem))
                continue
            if item[2][0] == theDate.year and item[2][1] == theDate.month and item[2][2] == theDate.day:
                newItem = [self.OncelyHolidayType] + list(item)
                result.append(tuple(newItem))

        return result

    def setRelativelyCalendarHolidays(self, relativelyCalendarHolidays):
        self.relativelyCalendarHolidays = relativelyCalendarHolidays

    def getRelativelyHolidaysForDate(self, theDate):
        result = []
        self.weekDaysInMonth = []
        self.numDaysCorMatrix = [(28, 0), (29, 1), (30, 2), (31, 3)]

        for i in range(7):
            self.weekDaysInMonth.append((i, 4))

        for holidayItem in self.relativelyCalendarHolidays:
            item = deepcopy(holidayItem)

            newItem = []
            newItem.append(item[0])

            i = 1
            while i < len(item):
                sRepNum = item[i][1]
                sWeekday = item[i][2]
                eWeekday = item[i+1][2]

                while 1:
                    eRepNum = item[i+1][1]

                    self.initRepMatrix(theDate.year, item[i][0])
                    while self.weekDaysInMonth[sWeekday][1] < sRepNum:
                        sRepNum -= 1

                    sDay = self.dayForWeekday(theDate.year, item[i][0], sWeekday, sRepNum)

                    self.initRepMatrix(theDate.year, item[i+1][0])
                    while self.weekDaysInMonth[eWeekday][1] < eRepNum:
                        eRepNum -= 1

                    nDay = self.dayForWeekday(theDate.year, item[i+1][0], eWeekday, eRepNum)

                    if ((nDay > sDay and
                        item[i+1][0] == item[i][0] and
                        (item[i+1][1] - item[i][1]) <= (nDay - sDay + abs(eWeekday - sWeekday))/7) or
                        item[i+1][0] != item[i][0]):
                        break

                    if self.weekDaysInMonth[eWeekday][1] > eRepNum:
                        eRepNum += 1
                    else:
                        item[i+1][0] += 1
                        item[i+1][1] = 1

                newItem.append([item[i][0], sDay, item[i][3], item[i][4], item[i][5]])

                newItem.append([item[i+1][0], nDay, item[i+1][3], item[i+1][4], item[i+1][5]])

                i += 2

            if item[1][0] == theDate.month and newItem[1][1] == theDate.day:
                nItem = [self.RelativelyHolidayType] + list(newItem)
                result.append(tuple(nItem))
                continue

            if item[2][0] == theDate.month and newItem[2][1] == theDate.day:
                nItem = [self.RelativelyHolidayType] + list(newItem)
                result.append(tuple(nItem))

        return result

    def dayForWeekday(self, year, month, weekday, repNum):
        monthDays = calendar.monthcalendar(year, month)
        if monthDays[0][weekday] == 0:
            repNum += 1
        return monthDays[repNum - 1][weekday]

    def initRepMatrix(self, year, month):
        for i in range(7):
            self.weekDaysInMonth[i] = (i, 4)

        startingWeekDay, numDays = calendar.monthrange(year, month)
        if startingWeekDay > 6:
            import pdb
            pdb.set_trace()
        for i in range(4):
            if numDays == self.numDaysCorMatrix[i][0]:
                break

        for j in range(self.numDaysCorMatrix[i][1]):
            self.weekDaysInMonth[startingWeekDay] = (self.weekDaysInMonth[startingWeekDay][0], self.weekDaysInMonth[startingWeekDay][1] + 1)
            startingWeekDay = (startingWeekDay + 1) % 7

    def isHolidayRunning(self, holidayId):
        result = holidayId in self.holidayIdList
        return result

    def setExpSettings(self, mult, cap):
        if hasattr(base, 'localAvatar'):
            base.localAvatar.inventory.setServerCreditMultiplier(mult)
        base.cr.expCap = cap

    def newsManagerDone(self):
        self.initialized = True
        messenger.send('generateNewsManager')
