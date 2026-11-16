from panda3d.core import VBase4, loadPrcFileData
from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObjectGlobal

from toontown.parties.ToontownTimeManager import ToontownTimeManager
from toontown.toon import NPCToons
from toontown.toonbase import ToontownGlobals, TTLocalizer

import json


class ModdingManager(DistributedObjectGlobal.DistributedObjectGlobal):
    notify = DirectNotifyGlobal.directNotify.newCategory('ModdingManager')
    neverDisable = 1

    def __init__(self, cr):
        DistributedObjectGlobal.DistributedObjectGlobal.__init__(self, cr)
        cr.moddingManager = self
        self.cards = {}
        self.cardsLoaded = False
        self.defaultMaxToon = False
        self.defaultZone = ToontownGlobals.ToontownCentral
        self.timeZone = 'US/Pacific'

    def loadCards(self):
        cards = self.cards
        for i in range(len(cards['name'])):
            TTLocalizer.NPCToonNames[cards['id'][i]] = str(cards['name'][i])
            if len(cards) < 27:
                NPCToons.NPCToonDict[cards['id'][i]] = (
                    cards['zone'][i],
                    cards['name'][i],
                    (
                        cards['head'][i],
                        cards['torso'][i],
                        cards['legs'][i],
                        cards['gender'][i],
                        cards['arm-color'][i],
                        cards['glove-color'][i],
                        cards['leg-color'][i],
                        cards['head-color'][i],
                        cards['shirt-id'][i],
                        cards['shirt-color'][i],
                        cards['sleeve-id'][i],
                        cards['sleeve-color'][i],
                        cards['bottoms-id'][i],
                        cards['bottoms-color'][i]
                    ),
                    cards['gender'][i],
                    cards['has-building'][i],
                    cards['type'][i]
                )
            else:
                NPCToons.NPCToonDict[cards['id'][i]] = (
                    cards['zone'][i],
                    cards['name'][i],
                    (
                        cards['head'][i],
                        cards['torso'][i],
                        cards['legs'][i],
                        cards['gender'][i],
                        cards['arm-color'][i],
                        cards['glove-color'][i],
                        cards['leg-color'][i],
                        cards['head-color'][i],
                        cards['shirt-id'][i],
                        cards['shirt-color'][i],
                        cards['sleeve-id'][i],
                        cards['sleeve-color'][i],
                        cards['bottoms-id'][i],
                        cards['bottoms-color'][i]
                    ),
                    cards['gender'][i],
                    cards['has-building'][i],
                    cards['type'][i],
                    cards['hat'][i],
                    cards['glasses'][i],
                    cards['backpack'][i],
                    cards['shoes'][i]
                )
            NPCToons.customNpcFriends[cards['id'][i]] = (
                cards['gag-track'][i],
                cards['gag-level'][i],
                cards['gag-damage'][i],
                cards['rating'][i]
            )

        NPCToons.npcFriends.update(NPCToons.customNpcFriends)

    def setCards(self, cards):
        cards = json.loads(cards)
        self.cards = cards

    def getCards(self):
        return self.cards

    def setDefaultMaxToon(self, state):
        self.defaultMaxToon = state

    def getDefaultMaxToon(self):
        return self.defaultMaxToon

    def setDefaultZone(self, zone):
        self.defaultZone = (2000, 1000, 5000, 4000, 3000, 9000)[zone]

    def getDefaultZone(self):
        return self.defaultZone

    def setProRacer(self, proRacer):
        self.proRacer = proRacer

    def getProRacer(self):
        return self.proRacer

    def setSendExtraData(self, sendExtraData):
        self.sendExtraData = sendExtraData

    def getSendExtraData(self):
        return self.sendExtraData

    def setTimezone(self, timezone):
        self.timeZone = timezone
        loadPrcFileData('Modding Manager', f'server-timezone {timezone}')
        base.cr.toontownTimeManager.serverTimeZone = ToontownTimeManager.TimeZoneStringToClass.get(
                base.config.GetString('server-timezone', TTLocalizer.TimeZone), None)()
        self.notify.info(f'Retrieved Server Time Zone: {base.config.GetString("server-timezone", TTLocalizer.TimeZone)}')

    def getTimezone(self):
        return self.timeZone