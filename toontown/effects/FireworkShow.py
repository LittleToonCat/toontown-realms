from panda3d.core import *
from direct.interval.IntervalGlobal import *
from toontown.effects.FireworkGlobals import *
from toontown.effects.Firework import Firework
from toontown.toonbase import ToontownGlobals, TTLocalizer
from toontown.parties import PartyGlobals
import random, json

from toontown.toonbase.ControlManager import ControlManager

colors = [(1, 1, 1, 1),
 (1, 0.1, 0.1, 1),
 (0.1, 1, 0.1, 1),
 (0.3, 1, 0.3, 1),
 (0.2, 0.2, 1, 1),
 (1, 1, 0.1, 1),
 (1, 0.5, 0.1, 1),
 (1, 0.1, 1, 1),
 (0.1, 1, 1, 1),
 (0.1, 0.5, 1, 1)]
fireworkShowTypes = [ToontownGlobals.JULY4_FIREWORKS,
                     PartyGlobals.FireworkShows.Summer,
                     ToontownGlobals.NEWYEARS_FIREWORKS,
                     ToontownGlobals.COMBO_FIREWORKS]

normalInstructions = TTLocalizer.FireworksInstructions
try:
    normalInstructions = ControlManager.parseHotkeyString(normalInstructions)
except:
    pass
summerInstructions = TTLocalizer.FireworksActivityInstructions
try:
    summerInstructions = ControlManager.parseHotkeyString(summerInstructions)
except:
    pass
fireworkShowMessages = {ToontownGlobals.JULY4_FIREWORKS: {'instructions': normalInstructions, 'start': TTLocalizer.FireworksJuly4Beginning, 'end': TTLocalizer.FireworksJuly4Ending},
                        PartyGlobals.FireworkShows.Summer: {'instructions': summerInstructions, 'start': TTLocalizer.FireworksActivityBeginning, 'end': TTLocalizer.FireworksActivityEnding},
                        ToontownGlobals.NEWYEARS_FIREWORKS: {'instructions': normalInstructions, 'start': TTLocalizer.FireworksNewYearsEveBeginning, 'end': TTLocalizer.FireworksNewYearsEveEnding},
                        ToontownGlobals.COMBO_FIREWORKS: {'instructions': normalInstructions, 'start': TTLocalizer.FireworksComboBeginning, 'end': TTLocalizer.FireworksComboEnding}}

fireworkShowMusic = {ToontownGlobals.JULY4_FIREWORKS: 'phase_4/audio/bgm/tt_party2.ogg',
                        PartyGlobals.FireworkShows.Summer: 'phase_4/audio/bgm/tt_summer.ogg',
                        ToontownGlobals.NEWYEARS_FIREWORKS: 'phase_4/audio/bgm/tt_s_ara_gen_fireworks_auldLangSyne.ogg',
                        ToontownGlobals.COMBO_FIREWORKS: 'phase_4/audio/bgm/tt_party2.ogg'}


class FireworkShow(NodePath):

    def r():
        return random.randint(8, 12) / 10.0

    def rV():
        return (random.randint(-60, 60), random.randint(10, 30), random.randint(125, 150))

    def rP():
        return (0, 0, 0)

    def rS():
        return 1.0 + random.random() / 2.0

    def rC():
        return random.choice(colors)

    def rT():
        return random.randint(12, 20) / 10.0

    def rD():
        return random.randint(1, 20) / 10.0

    showData = {}

    vfs = VirtualFileSystem.getGlobalPtr()
    filename = Filename('fireworks2.json')
    searchPath = DSearchPath()
    searchPath.appendDirectory(Filename('/phase_3/etc'))
    found = vfs.resolveFilename(filename, searchPath)
    data = vfs.readFile(filename, 1).decode()

    fireworks = json.loads(data)
    keys = fireworks.keys()
    showIds = []
    for key in keys:
        showIds.append(int(key))

    showIds.sort()
    for showId in showIds:
        fireworkInfo = fireworks.get(str(showId))
        for firework in fireworkInfo:
            for data in firework:
                if isinstance(data, list):
                    newData = tuple(data)
                    firework[firework.index(data)] = newData
            fireworkInfo[fireworkInfo.index(firework)] = firework
        showData[showId] = tuple(fireworkInfo)

    '''''''''''
    # Code to convert Fireworks to json format
    from collections import OrderedDict

    fireworkData = OrderedDict()
    for showId in list(showData.keys()):
        fireworkInfo = list(showData.get(showId))
        fireworkData[showId] = fireworkInfo

    with open('fireworks2.json', 'w') as data:
        json.dump(fireworkData, data, indent=4)
        data.close()
    '''''''''''

    sectionData = {ToontownGlobals.JULY4_FIREWORKS: [(0, 24), (24, len(showData[ToontownGlobals.JULY4_FIREWORKS]))],
     PartyGlobals.FireworkShows.Summer: [(0, 24), (24, len(showData[PartyGlobals.FireworkShows.Summer]))],
     ToontownGlobals.NEWYEARS_FIREWORKS: [(0, len(showData[PartyGlobals.FireworkShows.Summer]))],
     ToontownGlobals.COMBO_FIREWORKS: [(0, len(showData[PartyGlobals.FireworkShows.Summer]))]}
    showMusic = {}

    @classmethod
    def isValidShowType(cls, showType = -1):
        if showType in list(cls.showData.keys()):
            return True
        else:
            return False

    def __init__(self, showType = ToontownGlobals.NEWYEARS_FIREWORKS):
        NodePath.__init__(self, 'FireworkShow')
        self.showType = showType
        self.sectionIvals = []
        self.fireworks = []
        self.delaySectionStart = None
        self.curSection = None
        self.curOffset = 0.0
        return

    def beginSection(self, startIndex, endIndex, offset):
        taskMgr.remove('beginSection' + str(startIndex) + str(endIndex))
        sectionIval = Parallel()
        time = 2.0
        showMusic = self.showMusic.get(self.showType)
        if showMusic:
            base.musicMgr.load(showMusic, looping=False)
            musicOffset = self.getDuration(0, startIndex) - self.getDuration(startIndex, startIndex) + offset
            sectionIval.append(Func(base.musicMgr.request, showMusic, priority=2, looping=False))
            sectionIval.append(Func(base.musicMgr.offsetMusic, musicOffset))
        sectionData = self.showData.get(self.showType)[startIndex:endIndex]
        for fireworkInfo in sectionData:
            typeId = fireworkInfo[0]
            velocity = fireworkInfo[1]
            pos = fireworkInfo[2]
            scale = fireworkInfo[3]
            color1 = fireworkInfo[4]
            color2 = fireworkInfo[5]
            if color2 == -1:
                color2 = color1
            trailDur = fireworkInfo[6]
            delay = fireworkInfo[7]
            firework = Firework(typeId, velocity, scale, color1, color2, trailDur)
            firework.reparentTo(self)
            firework.setPos(pos)
            self.fireworks.append(firework)
            sectionIval.append(Sequence(Wait(time), firework.generateFireworkIval()))
            time += delay

        self.sectionIvals.append(sectionIval)
        self.curSection = sectionIval
        self.curOffset = offset
        self.delaySectionStart = FrameDelayedCall('delaySectionStart', self.startCurSection, frames=24)

    def startCurSection(self):
        self.curSection.start(self.curOffset)

    def begin(self, timestamp):
        time = 0.0
        for section in self.sectionData.get(self.showType):
            startIndex = section[0]
            endIndex = section[1]
            sectionDur = self.getDuration(startIndex, endIndex)
            if timestamp < sectionDur:
                timestamp = max(0.0, timestamp)
                taskMgr.doMethodLater(time, self.beginSection, 'beginSection' + str(startIndex) + str(endIndex), extraArgs=[startIndex, endIndex, timestamp])
                time = time + sectionDur - timestamp
            timestamp -= sectionDur

    def getDuration(self, startIndex = 0, endIndex = None):
        duration = 0.0
        if endIndex == None:
            endIndex = len(self.showData.get(self.showType))
        for firework in self.showData.get(self.showType)[startIndex:endIndex]:
            duration += firework[7]

        return duration

    def getShowDuration(self, eventId = None):
        duration = 0.0
        if eventId:
            for firework in self.showData[eventId]:
                duration += firework[7]

        else:
            for firework in self.showData[self.showType]:
                duration += firework[7]

        return duration

    def isPlaying(self):
        for ival in self.sectionIvals:
            if ival.isPlaying():
                return True

        return False

    def cleanupShow(self):
        if self.delaySectionStart:
            self.delaySectionStart.destroy()
            del self.delaySectionStart
            self.delaySectionStart = None
        showMusic = self.showMusic.get(self.showType)
        if showMusic:
            base.musicMgr.requestFadeOut(showMusic)
        for section in self.sectionData.get(self.showType):
            startIndex = section[0]
            endIndex = section[1]
            taskMgr.remove('beginSection' + str(startIndex) + str(endIndex))

        for ival in self.sectionIvals:
            ival.pause()
            del ival
            ival = None

        self.sectionIvals = []
        for firework in self.fireworks:
            firework.cleanup()
            firework.removeNode()
            del firework
            firework = None

        self.fireworks = []
        return
