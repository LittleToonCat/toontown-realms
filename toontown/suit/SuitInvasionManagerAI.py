from direct.directnotify import DirectNotifyGlobal
from direct.showbase.DirectObject import DirectObject
from toontown.toonbase import ToontownGlobals
from toontown.suit import SuitDNA
import random, copy
from direct.task import Task

class SuitInvasionManagerAI(DirectObject):
    """
    Manages invasions of Suits
    """

    notify = DirectNotifyGlobal.directNotify.newCategory('SuitInvasionManagerAI')

    def __init__(self, air):
        self.air = air
        self.invading = 0

        # We store the summoner name in-case the toon decides to logoff
        self.summonerName = ''
        self.summonerId = 0

        self.cogList = []
        self.special = 0
        self.virtual = 0
        self.mega = False
        self.totalNumCogs = 0
        self.numCogsRemaining = 0

        # Set of cog types to choose from
        self.invadingCogTypes = (
            # Corporate
            'f', # Flunky
            'hh', # Head Hunter
            'cr', # Corporate Raider
            # Sales
            'tf', # Two-faced
            'm', # Mingler
            # Money
            'mb', # Money Bags
            'ls', # Loan shark
            # Legal
            'sd', # Spin Doctor
            'le', # Legal Eagle
            )

        # Picked from randomly how many cogs will invade
        # This might need to be adjusted based on population(?)
        self.invadingNumList = (1000, 2000, 3000, 4000)

        # Minimum time between invasions on this shard (in seconds)
        # No more than 1 per 2 days
        self.invasionMinDelay = 2 * 24 * 60 * 60
        # Maximum time between invasions on this shard (in seconds)
        # At least once every 7 days
        self.invasionMaxDelay = 7 * 24 * 60 * 60

        self.accept('toon-name-update', self.handleToonNameUpdate)

        # Kick off the first invasion
        self.waitForNextInvasion()

    def delete(self):
        self.ignoreAll()
        taskMgr.remove(self.taskName("cogInvasionMgr"))

    def computeInvasionDelay(self):
        # Compute the delay until the next invasion
        return ((self.invasionMaxDelay - self.invasionMinDelay) * random.random()
                + self.invasionMinDelay)

    def tryInvasionAndWaitForNext(self, task):
        # Start the invasion if there is not one already
        if self.getInvading():
            self.notify.warning("invasionTask: tried to start random invasion, but one is in progress")
        else:
            self.notify.debug("invasionTask: starting random invasion")
            cogList = [random.choice(self.invadingCogTypes)]
            totalNumCogs = random.choice(self.invadingNumList)
            self.startInvasion(cogList, totalNumCogs, False, False)
        # In either case, fire off the next invasion
        self.waitForNextInvasion()
        return Task.done

    def waitForNextInvasion(self):
        taskMgr.remove(self.taskName("cogInvasionMgr"))
        delay = self.computeInvasionDelay()
        self.notify.debug(f"invasionTask: waiting {delay} seconds until next invasion")
        taskMgr.doMethodLater(delay, self.tryInvasionAndWaitForNext,
                              self.taskName("cogInvasionMgr"))

    def getInvading(self):
        return self.invading

    def getSummonerName(self):
        return self.summonerName

    def getSummonerId(self):
        return self.summonerId

    def getCogType(self):
        return self.cogList, self.special, self.virtual, self.mega

    def getNumCogsRemaining(self):
        return self.numCogsRemaining

    def getTotalNumCogs(self):
        return self.totalNumCogs

    def startInvasion(self, cogList, totalNumCogs, special, virtual, mega = False, summonerId = 0):
        if self.invading:
            self.notify.warning("startInvasion: already invading cogType: %s numCogsRemaining: %s" %
                                (cogType, self.numCogsRemaining))
            return 0

        # This value will only be useful to check if we're trying to summon an entire cog department
        for cogType in cogList:
            department = cogType.capitalize()

            if cogType not in SuitDNA.suitHeadTypes and department not in ToontownGlobals.Dept2Dept.values():
                self.notify.warning("startInvasion: unknown cogType: %s" % cogType)
                return 0

        self.notify.debug("startInvasion: cogList: %s totalNumCogs: %s special: %s virtual: %s mega: %s" %
                          (cogList, totalNumCogs, special, virtual, mega))
        self.invading = 1
        self.cogList = cogList
        self.special = special
        self.virtual = virtual
        self.mega = mega
        self.totalNumCogs = totalNumCogs
        self.numCogsRemaining = self.totalNumCogs

        self.summonerId = summonerId
        if summonerId:
            toon = simbase.air.doId2do.get(summonerId)
            if toon:
                self.summonerName = toon.getName()

        # Tell the news manager that an invasion is beginning
        self.air.newsManager.invasionBegin(self.cogList, self.totalNumCogs, self.special, self.virtual, self.mega)

        # Get rid of all the current cogs on the streets
        # (except those already in battle, they can stay)
        for suitPlanner in self.air.suitPlanners.values():
            if suitPlanner.respectInvasions:
                suitPlanner.flySuits(ignoreTopBrasses=True)
        # Success!
        return 1

    def getInvadingCogList(self):
        if self.invading:
            self.notify.debug("getInvadingCogList: returned cog list: %s, num remaining: %s" %
                              (self.cogList, self.numCogsRemaining))
            return self.cogList, self.special, self.virtual
        else:
            # self.notify.debug("getInvadingCogList: not currently invading")
            return None, None, None

    def getInvadingCog(self):
        if self.invading:
            invadingCog = random.choice(self.cogList)
            special = copy.deepcopy(self.special)
            virtual = copy.deepcopy(self.virtual)

            if not self.mega:
                self.numCogsRemaining -= 1
                if self.numCogsRemaining <= 0:
                    self.stopInvasion()

            self.notify.debug("getInvadingCog: returned cog: %s, num remaining: %s" %
                              (invadingCog, self.numCogsRemaining))
            return invadingCog, special, virtual
        else:
            # self.notify.debug("getInvadingCog: not currently invading")
            return None, None, None

    def stopInvasion(self):
        self.notify.debug("stopInvasion: invasion is over now")
        # Tell the news manager that an invasion is ending
        self.air.newsManager.invasionEnd(self.cogList, 0, self.special, self.virtual, self.mega)
        self.invading = 0
        self.summonerId = 0
        self.summonerName = ''
        self.cogList = []
        self.special = 0
        self.virtual = 0
        self.mega = False
        self.totalNumCogs = 0
        self.numCogsRemaining = 0
        # Get rid of all the current invasion cogs on the streets
        # (except those already in battle, they can stay)
        for suitPlanner in self.air.suitPlanners.values():
            if suitPlanner.respectInvasions:
                suitPlanner.flySuits()

    # Need this here since this is not a distributed object
    def taskName(self, taskString):
        return (taskString + "-" + str(hash(self)))

    def handleToonNameUpdate(self, doId, name):
        if doId == self.summonerId:
            self.summonerName = name
