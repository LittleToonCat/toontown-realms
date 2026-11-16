from .FireworkGlobals import *
from toontown.toonbase import ToontownGlobals
from toontown.parties import PartyGlobals
from panda3d.core import Filename, DSearchPath, VirtualFileSystem
import json

# Code to load fireworks from json
shows = {}

vfs = VirtualFileSystem.getGlobalPtr()
filename = Filename('fireworks.json')
searchPath = DSearchPath()
searchPath.appendDirectory(Filename('/phase_3/etc'))
found = vfs.resolveFilename(filename, searchPath)
data = vfs.readFile(filename, 1).decode()

quests = json.loads(data)
keys = quests.keys()
questIds = []
for key in keys:
    questIds.append(int(key))

questIds.sort()
for questId in questIds:
    questInfo = quests.get(str(questId))
    shows[questId] = tuple(questInfo)

# Code to convert Fireworks to json format
'''''''''
from collections import OrderedDict

questData = OrderedDict()
for questId in list(shows.keys()):
    questInfo = list(shows.get(questId))
    questData[questId] = questInfo

with open('fireworks.json', 'w') as data:
    json.dump(questData, data, indent=4)
    data.close()
'''''''''

def getShow(holidayId, index):
    showList = shows.get(holidayId, [])
    if index < len(showList):
        return showList[index]
    else:
        return None
    return None


def getShowDuration(eventId, index):
    show = getShow(eventId, index)
    duration = 0.0
    duration += skyTransitionDuration
    duration += preShowPauseDuration
    for effect in show:
        waitTime, style, colorIndex1, colorIndex2, amp, x, y, z = effect
        duration += waitTime

    duration += postShowPauseDuration
    duration += preNormalMusicPauseDuration
    return duration
