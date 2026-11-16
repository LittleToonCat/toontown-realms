from panda3d.core import VBase4
from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObjectGlobalAI
from otp.distributed.OtpDoGlobals import *
from toontown.toonbase import ToontownGlobals, TTLocalizer, ServerSettings
from toontown.toon import ToonDNA, NPCToons

import json
import os


sosJsonDefaultValues = '''{
    "name" : ["Von", "Von II"],
    "id": [1014, 1015],
    "head": ["dss", "hss"],
    "torso": ["ls", "ms"],
    "legs": ["m", "m"],
    "gender": ["m", "f"],
    "head-color": [27, 7],
    "arm-color": [27, 7],
    "leg-color": [27, 7],
    "glove-color": [27, 7],
    "shirt-id": [0, 95],
    "shirt-color": [0, 27],
    "sleeve-id": [0, 95],
    "sleeve-color": [0, 27],
    "bottoms-id": [0, 6],
    "bottoms-color": [0, 2],
    "has-building": [0, 0],
    "gag-track": [6, 1],
    "gag-level": [0, 6],
    "gag-damage": [255, 200],
    "rating": [5, 5],
    "zone": [-1, -1],
    "type": [0, 0],
    "hat": [[0, 0, 0], [0, 0, 0]],
    "glasses": [[0, 0, 0], [0, 0, 0]],
    "backpack": [[0, 0, 0], [0, 0, 0]],
    "shoes": [[0, 0, 0], [0, 0, 0]]
}
'''


class ModdingManagerAI(DistributedObjectGlobalAI.DistributedObjectGlobalAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('ModdingManagerAI')

    def __init__(self, air):
        DistributedObjectGlobalAI.DistributedObjectGlobalAI.__init__(self, air)
        self.cards = {}
        self.generateCards()
        self.defaultMaxToon = ServerSettings.StartAsMaxToon.get()
        self.defaultZone = ServerSettings.NewToonStartingArea.get().value
        self.proRacer = False
        self.sendExtraData = True
        self.timeZone = 'US/Pacific'

    def b_loadCards(self):
        self.d_loadCards()
        self.loadCards()

    def d_loadCards(self):
        self.sendUpdate('loadCards', [])

    def loadCards(self):
        cards = json.loads(self.cards)
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

    def generateCards(self):
        if not os.path.exists('config/'):
            os.mkdir('config/')

        if not os.path.isfile('config/sos.json'):
            with open('config/sos.json', 'w') as data:
                data.write(sosJsonDefaultValues)
                data.close()

        with open('config/sos.json') as data:
            sos = json.load(data)

        sos = json.dumps(sos)
        self.setCards(sos)

    def setCardsAiToUd(self, sos):
        self.sendUpdateToUD('setCardsAiToUd', [sos])

    def setCards(self, cards):
        self.cards = cards

    def getCards(self):
        return self.cards

    def b_setDefaultMaxToon(self, state):
        self.setDefaultMaxToon(state)
        self.d_setDefaultMaxToon(state)

    def setDefaultMaxToon(self, state):
        self.defaultMaxToon = state

    def d_setDefaultMaxToon(self, state):
        self.sendUpdate('setDefaultMaxToon', [state])
        self.setDefaultMaxToonAiToUd(state)

    def getDefaultMaxToon(self):
        return self.defaultMaxToon

    def setDefaultMaxToonAiToUd(self, state):
        self.sendUpdateToUD('setDefaultMaxToonAiToUd', [state])

    def b_setDefaultZone(self, zone):
        self.setDefaultZone(zone)
        self.d_setDefaultZone(zone)

    def setDefaultZone(self, zone):
        self.defaultZone = (2000, 1000, 5000, 4000, 3000, 9000)[zone]

    def d_setDefaultZone(self, zone):
        self.sendUpdate('setDefaultZone', [zone])

    def getDefaultZone(self):
        return self.defaultZone

    def b_setProRacer(self, proRacer):
        self.setProRacer(proRacer)
        self.d_setProRacer(proRacer)

    def setProRacer(self, proRacer):
        self.proRacer = proRacer

    def d_setProRacer(self, proRacer):
        self.sendUpdate('setProRacer', [proRacer])

    def getProRacer(self):
        return self.proRacer

    def b_setSendExtraData(self, sendExtraData):
        self.setSendExtraData(sendExtraData)
        self.d_setSendExtraData(sendExtraData)

    def setSendExtraData(self, sendExtraData):
        self.sendExtraData = sendExtraData

    def d_setSendExtraData(self, sendExtraData):
        self.sendUpdate('setSendExtraData', [sendExtraData])

    def getSendExtraData(self):
        return self.sendExtraData

    def b_setTimezone(self, timeZone):
        self.setTimezone(timeZone)
        self.d_setTimezone(timeZone)

    def setTimezone(self, timeZone):
        self.timeZone = timeZone

    def d_setTimezone(self, timeZone):
        self.sendUpdate('setTimezone', [timeZone])

    def getTimezone(self):
        return self.timeZone

    def sendUpdateToUD(self, field, args=[]):
        dg = self.dclass.aiFormatUpdate(field, OTP_DO_ID_MODDING_MANAGER, OTP_DO_ID_MODDING_MANAGER, self.doId, args)
        self.air.send(dg)
