from direct.directnotify import DirectNotifyGlobal
from toontown.ai import HolidayBaseAI
from toontown.toonbase import ToontownGlobals
from toontown.suit import SuitDNA
import random

Any = 'Any'
AnyDept = 'AnyDept'

_holidayId2Cog = {
    # holiday ID: suit type, skeleton
    ToontownGlobals.HALLOWEEN: (['b'], 0),
    ToontownGlobals.SKELECOG_INVASION: ([Any], 1),
    ToontownGlobals.MR_HOLLYWOOD_INVASION: (['mh'], 0),
    # Originally it chose a random Bossbot cog specifically, but
    # since we got department invasions now, might as well use them.
    ToontownGlobals.BOSSCOG_INVASION: (['bossbot'], 0),
    ToontownGlobals.MARCH_INVASION: (['bs'], 0),
    ToontownGlobals.DECEMBER_INVASION: (['cc'], 0),
    ToontownGlobals.SELLBOT_SURPRISE_1: (['cc'], 0),
    ToontownGlobals.COLD_CALLER_INVASION: (['cc'], 0),
    ToontownGlobals.SELLBOT_SURPRISE_2: (['nd'], 0),
    ToontownGlobals.NAME_DROPPER_INVASION: (['nd'], 0),
    ToontownGlobals.SELLBOT_SURPRISE_3: (['gh'], 0),
    ToontownGlobals.SELLBOT_SURPRISE_4: (['ms'], 0),
    ToontownGlobals.MOVER_AND_SHAKER_INVASION: (['ms'], 0),
    ToontownGlobals.CASHBOT_CONUNDRUM_1: (['sc'], 0),
    ToontownGlobals.CASHBOT_CONUNDRUM_2: (['pp'], 0),
    ToontownGlobals.PENNY_PINCHER_INVASION: (['pp'], 0),
    ToontownGlobals.CASHBOT_CONUNDRUM_3: (['bc'], 0),
    ToontownGlobals.BEAN_COUNTER_INVASION: (['bc'], 0),
    ToontownGlobals.CASHBOT_CONUNDRUM_4: (['nc'], 0),
    ToontownGlobals.NUMBER_CRUNCHER_INVASION: (['nc'], 0),
    ToontownGlobals.TAX_DAY_INVASION: (['nc'], 0),
    ToontownGlobals.LAWBOT_GAMBIT_1: (['bf'], 0),
    ToontownGlobals.LAWBOT_GAMBIT_2: (['dt'], 0),
    ToontownGlobals.DOUBLE_TALKER_INVASION: (['dt'], 0),
    ToontownGlobals.LAWBOT_GAMBIT_3: (['ac'], 0),
    ToontownGlobals.AMBULANCE_CHASER_INVASION: (['ac'], 0),
    ToontownGlobals.LAWBOT_GAMBIT_4: (['bs'], 0),
    ToontownGlobals.TROUBLE_BOSSBOTS_1: (['f'], 0),
    ToontownGlobals.TROUBLE_BOSSBOTS_2: (['p'], 0),
    ToontownGlobals.TROUBLE_BOSSBOTS_3: (['mm'], 0),
    ToontownGlobals.MICROMANAGER_INVASION: (['mm'], 0),
    ToontownGlobals.TROUBLE_BOSSBOTS_4: (['ds'], 0),
    ToontownGlobals.DOWN_SIZER_INVASION: (['ds'], 0),
    ToontownGlobals.DOWNSIZER_INVASION: (['ds'], 0),
    ToontownGlobals.YES_MAN_INVASION: (['ym'], 0),
    ToontownGlobals.TIGHTWAD_INVASION: (['tw'], 0),
    ToontownGlobals.TELEMARKETER_INVASION: (['tm'], 0),
    ToontownGlobals.HEADHUNTER_INVASION: (['hh'], 0),
    ToontownGlobals.SPINDOCTOR_INVASION: (['sd'], 0),
    ToontownGlobals.MONEYBAGS_INVASION: (['mb'], 0),
    ToontownGlobals.TWOFACES_INVASION: (['tf'], 0),
    ToontownGlobals.MINGLER_INVASION: (['m'], 0),
    ToontownGlobals.LOANSHARK_INVASION: (['ls'], 0),
    ToontownGlobals.CORPORATE_RAIDER_INVASION: (['cr'], 0),
    ToontownGlobals.LEGAL_EAGLE_INVASION: (['le'], 0),
    ToontownGlobals.ROBBER_BARON_INVASION: (['rb'], 0),
    ToontownGlobals.BIGWIG_INVASION: (['bw'], 0),
    ToontownGlobals.BIG_WIG_INVASION: (['bw'], 0),
    ToontownGlobals.BIG_CHEESE_INVASION: (['tbc'], 0),

    # DISCUSS: What are we gonna do about these holidays?  They're all
    # duplicates.  Well, the first four are, except the memorial day one.
    ToontownGlobals.MEGAINVASION_HALLOWEEN: (['b'], 0),
    ToontownGlobals.MEGAINVASION_IDES_OF_MARCH: (['bs'], 0),
    ToontownGlobals.MEGAINVASION_TAX_DAY: (['nc'], 0),
    ToontownGlobals.MEGAINVASION_MEMORIAL_DAY: (['mh'], 0),
}


class HolidaySuitInvasionManagerAI(HolidayBaseAI.HolidayBaseAI):

    notify = DirectNotifyGlobal.directNotify.newCategory('HolidaySuitInvasionManagerAI')

    def __init__(self, air, holidayId):
        HolidayBaseAI.HolidayBaseAI.__init__(self, air, holidayId)

    def start(self):
        # Stop any current invasion that might be happening by chance
        if self.air.suitInvasionManager.getInvading():
            if self.air.suitInvasionManager.mega:
                # don't run if we're already running a mega-invasion
                self.notify.warning("A Mega-Invasion is already running!")
                return
            self.notify.info(f"Stopping current invasion to make room for holiday {self.holidayId}")
            self.air.suitInvasionManager.stopInvasion()

        if not simbase.config.GetBool('want-invasions', 1):
            return 1

        invasionSpec = _holidayId2Cog.get(self.holidayId)
        if not invasionSpec:
            self.notify.warning(f"Unrecognized holidayId: {self.holidayId}")
            return 0

        # Support for random suits or departments
        suitList = invasionSpec[0]
        for i in range(len(suitList)):
            if suitList[i] == Any:
                suitList[i] = random.choice(SuitDNA.suitHeadTypes)
            elif suitList[i] == AnyDept:
                suitList[i] = ToontownGlobals.Dept2Dept[random.choice(SuitDNA.suitDepts)]

        self.air.suitInvasionManager.startInvasion(suitList, 1000000000, invasionSpec[1],
                                                   0, 1)
        self.air.suitInvasionManager.waitForNextInvasion()
        return 1

    def stop(self):
        # Holiday is over, stop the invasion if it happens to still be running
        if self.air.suitInvasionManager.getInvading():
            self.notify.info(f"Prematurely stopping holiday invasion: {self.holidayId}")
            self.air.suitInvasionManager.stopInvasion()
