from direct.directnotify import DirectNotifyGlobal

from toontown.toonbase import ToontownGlobals

from toontown.ai.HolidayBaseAI import HolidayBaseAI
from toontown.effects.FireworkHolidayAI import FireworkHolidayAI
from toontown.fishing.BingoNightHolidayAI import BingoNightHolidayAI
from toontown.fishing.FishPokerHolidayManager import FishPokerHolidayManager
from toontown.ai.DistributedBlackCatMgrAI import BlackCatDayHolidayAI
from toontown.racing.RaceManagerAI import KartRecordDailyResetter, KartRecordWeeklyResetter, CircuitRaceHolidayMgr
from toontown.ai.ScavengerHuntHolidayAI import ScavengerHuntHolidayAI
from toontown.minigame.TrolleyHolidayMgrAI import TrolleyHolidayMgrAI
from toontown.minigame.TrolleyWeekendMgrAI import TrolleyWeekendMgrAI
from toontown.ai.CharacterSwitchHolidayAI import CharacterSwitchHolidayAI
from toontown.ai.DistributedGreenToonEffectMgrAI import GreenToonHolidayAI
from toontown.ai.SillySaturdayHolidayAI import SillySaturdayHolidayMgrAI
# from toontown.ai.MegaInvasionHolidayAI import MegaInvasionHolidayMgrAI
from toontown.suit import HolidaySuitInvasionManagerAI
from toontown.ai.DoubleJellybeanManagerAI import DoubleJellybeanFishingAI, DoubleJellybeanTrolleyAI, DoubleJellybeanPartyAI
from toontown.ai.HolidayPropsAI import HolidayPropsAI
from toontown.ai.AprilFoolsHolidayAI import AprilFoolsHolidayAI
from toontown.ai.SillyMeterHolidayAI import SillyMeterHolidayAI

holidayToMgr = {
    ToontownGlobals.JULY4_FIREWORKS: FireworkHolidayAI,
    ToontownGlobals.NEWYEARS_FIREWORKS: FireworkHolidayAI,
    ToontownGlobals.WINTER_DECORATIONS: HolidayPropsAI,
    ToontownGlobals.FISH_BINGO_NIGHT: BingoNightHolidayAI,
    ToontownGlobals.FISH_POKER: FishPokerHolidayManager,
    ToontownGlobals.BLACK_CAT_DAY: BlackCatDayHolidayAI,
    ToontownGlobals.KART_RECORD_DAILY_RESET: KartRecordDailyResetter,
    ToontownGlobals.KART_RECORD_WEEKLY_RESET: KartRecordWeeklyResetter,
    ToontownGlobals.TRICK_OR_TREAT: ScavengerHuntHolidayAI,
    ToontownGlobals.CIRCUIT_RACING: CircuitRaceHolidayMgr,
    ToontownGlobals.CIRCUIT_RACING_EVENT: CircuitRaceHolidayMgr,
    ToontownGlobals.TROLLEY_HOLIDAY: TrolleyHolidayMgrAI,
    ToontownGlobals.TROLLEY_WEEKEND: TrolleyWeekendMgrAI,
    ToontownGlobals.HALLOWEEN_PROPS: HolidayPropsAI,
    ToontownGlobals.HALLOWEEN_COSTUMES: CharacterSwitchHolidayAI,
    ToontownGlobals.APRIL_FOOLS_COSTUMES: CharacterSwitchHolidayAI,
    ToontownGlobals.APRIL_FOOLS: AprilFoolsHolidayAI,
    ToontownGlobals.WINTER_CAROLING: ScavengerHuntHolidayAI,
    ToontownGlobals.COMBO_FIREWORKS: FireworkHolidayAI,
    ToontownGlobals.IDES_OF_MARCH: GreenToonHolidayAI,
    ToontownGlobals.SPOOKY_TRICK_OR_TREAT: ScavengerHuntHolidayAI,
    ToontownGlobals.SPOOKY_COSTUMES: CharacterSwitchHolidayAI,
    ToontownGlobals.WACKY_WINTER_CAROLING: ScavengerHuntHolidayAI,
    ToontownGlobals.SILLY_SATURDAY: SillySaturdayHolidayMgrAI,
    ToontownGlobals.JELLYBEAN_TROLLEY_HOLIDAY: DoubleJellybeanTrolleyAI,
    ToontownGlobals.JELLYBEAN_FISHING_HOLIDAY: DoubleJellybeanFishingAI,
    ToontownGlobals.JELLYBEAN_PARTIES_HOLIDAY: DoubleJellybeanPartyAI,
    ToontownGlobals.JELLYBEAN_TROLLEY_HOLIDAY_MONTH: DoubleJellybeanTrolleyAI,
    ToontownGlobals.JELLYBEAN_FISHING_HOLIDAY_MONTH: DoubleJellybeanFishingAI,
    ToontownGlobals.JELLYBEAN_PARTIES_HOLIDAY_MONTH: DoubleJellybeanPartyAI,
    ToontownGlobals.SILLYMETER_HOLIDAY: SillyMeterHolidayAI
}

# Get holidays added on HolidaySuitInvasionManagerAI and add it here.
# If you need to add invasion related holidays, go to
# toontown/suit/HolidaySuitInvasionManagerAI.py
for holiday in HolidaySuitInvasionManagerAI._holidayId2Cog.keys():
    holidayToMgr[holiday] = HolidaySuitInvasionManagerAI.HolidaySuitInvasionManagerAI


class HolidayManagerAI:
    notify = DirectNotifyGlobal.directNotify.newCategory('HolidayManagerAI')

    def __init__(self, air):
        self.air = air
        self.currentHolidays = {}

    def isHolidayRunning(self, holidayId):
        return holidayId in self.currentHolidays

    def isMoreXpHolidayRunning(self):
        if ToontownGlobals.MORE_XP_HOLIDAY in self.currentHolidays:
            return True

        return False

    def getCurPhase(self, holidayId):
        # TODO: Implement this... maybe; it was used for phased holidays,
        #  mostly relating to the silly meter
        return 1

    def isValidHoliday(self, holidayId):
        # This is kinda hacky but there's no good way to determine what's a real holiday and what's not
        # unless we gave every real holiday a manager
        return ToontownGlobals.JULY4_FIREWORKS <= holidayId <= ToontownGlobals.FISH_POKER

    def startHoliday(self, holidayId, task=None):
        if not self.isValidHoliday(holidayId):
            self.notify.warning(f'Tried to start invalid holiday {holidayId}!')
            if task:
                return task.done
            return
        if holidayId not in self.currentHolidays:
            if holidayId in holidayToMgr:
                holidayMgr = holidayToMgr[holidayId]
                for holiday in list(self.currentHolidays.values()):
                    if isinstance(holiday, holidayMgr) and holidayMgr.__name__ != 'HolidayPropsAI':
                        self.notify.warning(f'Unable to start holiday {holidayId} because the same manager for {holiday.holidayId} is already running!')
                        return
                if holidayMgr.__name__ == 'ScavengerHuntHolidayAI':
                    holidayMgr = holidayMgr(self.air, holidayId, holidayYear=self.air.toontownTimeManager.
                                            getCurServerDateTime().now(tz=self.air.toontownTimeManager.serverTimeZone).
                                            year)
                elif holidayMgr.__name__ == 'SillyMeterHolidayAI':
                    for holidayData in self.air.newsManager.getYearlyCalendarHolidays():
                        if holidayData[0] == ToontownGlobals.SILLYMETER_HOLIDAY:
                            sillyMeterHolidayData = holidayData
                            holidayMgr = holidayMgr(self.air, holidayId, sillyMeterHolidayData[1], sillyMeterHolidayData[2])
                            break
                else:
                    holidayMgr = holidayMgr(self.air, holidayId)
            else:
                holidayMgr = HolidayBaseAI(self.air, holidayId)
            holidayMgr.start()
            self.currentHolidays[holidayId] = holidayMgr
            self.air.newsManager.d_setHolidayIdList(list(self.currentHolidays.keys()))

        if task:
            return task.done

    def endHoliday(self, holidayId):
        if not self.isValidHoliday(holidayId):
            self.notify.warning(f'Tried to end invalid holiday {holidayId}!')
            return

        if holidayId in self.currentHolidays:
            self.currentHolidays[holidayId].stop()
            del self.currentHolidays[holidayId]
            self.air.newsManager.d_setHolidayIdList(list(self.currentHolidays.keys()))
