from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI
from direct.fsm.FSM import FSM
import random

from typing import List, Tuple

from . import PropHuntGlobals
from .DistributedPropHuntPropAI import DistributedPropHuntPropAI


class DistributedPropHuntGameAI(DistributedObjectAI, FSM):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistPropHuntGameAI')
    numFeathers = 100

    def __init__(self, air):
        DistributedObjectAI.__init__(self, air)
        FSM.__init__(self, 'PropHuntFSM')

        self.fakeProps: List[DistributedPropHuntPropAI] = []
        self.allowedProps: List[str] = []
        self.looseToons = []
        self.toons: List[int] = []
        self.involvedToons: List[int] = []
        self.nearToons: List[int] = []

        self.hiders = []
        self.hunters = []
        self.spectators = []

        self.hunter2PieTimestamp = {}

    def avatarEnter(self):
        avId = self.air.getAvatarIdFromSender()
        self.addToon(avId)

    def avatarExit(self):
        avId = self.air.getAvatarIdFromSender()
        self.removeToon(avId)

    def avatarNearEnter(self):
        avId = self.air.getAvatarIdFromSender()
        if avId not in self.nearToons:
            self.nearToons.append(avId)

    def avatarNearExit(self):
        avId = self.air.getAvatarIdFromSender()
        try:
            self.nearToons.remove(avId)
        except:
            pass

    def __handleUnexpectedExit(self, avId: int, zoneNew: int = None, zoneOld: int = None):
        # A zone change event is sent when entering so we'll ignore it
        if zoneNew != self.zoneId:
            self.removeToon(avId)

    def addToon(self, avId: int):
        if avId not in self.looseToons and avId not in self.involvedToons:
            self.looseToons.append(avId)
            event = self.air.getAvatarExitEvent(avId)
            # Zone change is used to handle someone exiting via ~setZone
            otherEvent = self.staticGetLogicalZoneChangeEvent(avId)
            self.acceptOnce(otherEvent, self.__handleUnexpectedExit, extraArgs = [avId])
            self.acceptOnce(event, self.__handleUnexpectedExit, extraArgs = [avId])

    def removeToon(self, avId: int):
        try:
            self.looseToons.remove(avId)
        except:
            pass

        try:
            self.involvedToons.remove(avId)
        except:
            pass

        try:
            self.hunters.remove(avId)
        except:
            pass

        try:
            self.hiders.remove(avId)
        except:
            pass

        try:
            self.nearToons.remove(avId)
        except:
            pass

        event = self.air.getAvatarExitEvent(avId)
        self.ignore(event)
        otherEvent = self.staticGetLogicalZoneChangeEvent(avId)
        self.ignore(otherEvent)
        if not (self.looseToons or self.involvedToons):
            self.doMethodLater(10, self.__gameDone, 'PropHuntDone')

    def __gameDone(self, task):
        if self.air:
            self.air.writeServerEvent('prophuntDone', self.doId)
        self.b_setState('Off')
        messenger.send(self.uniqueName('PartyGameDone'))
        self.ignoreAll()
        for prop in self.fakeProps:
            prop.requestDelete()
        return task.done

    def enterWaitForToons(self):
        self.acceptNewToons()
        # Wait for all the players to connect
        self.barrier = self.beginBarrier('WaitForToons', self.involvedToons, PropHuntGlobals.LoadMapTimeout,
                                         self.__doneWaitForToons)

    def resetToons(self):
        if self.hunters or self.hiders:
            self.looseToons = self.looseToons + self.involvedToons
            self.involvedToons = []
            self.hunters = []
            self.hiders = []

    def __doneWaitForToons(self, toons: List[int]):
        self.notify.info('All Players are loaded in! Loading map...')
        self.notify.info(f'Connected Players: {toons}')
        self.b_setState('LoadMap')

    def __randomizeTeams(self, allToons: List[int]) -> Tuple[List[int], List[int]]:
        allToons = list(allToons)
        random.shuffle(allToons)
        hiders = allToons[:len(allToons) // 2]
        hunters = allToons[len(allToons) // 2:]
        self.sendUpdate('setToonIds', [self.involvedToons, hiders, hunters])
        return hiders, hunters

    def exitWaitForToons(self):
        self.ignoreBarrier(self.barrier)

    def acceptNewToons(self):
        sourceToons = self.looseToons
        self.looseToons = []
        for toonId in sourceToons:
            toon = self.air.doId2do.get(toonId)
            if toon and not toon.ghostMode:
                self.involvedToons.append(toonId)
            else:
                self.looseToons.append(toonId)

        self.hiders, self.hunters = self.__randomizeTeams(self.involvedToons)

    def b_setState(self, state: str):
        self.notify.info(f"Requesting state {state}")
        self.setState(state)
        self.d_setState(state)

    def d_setState(self, state: str):
        self.sendUpdate('setState', [state])

    def setState(self, state: str):
        self.demand(state)

    def enterOff(self):
        self.resetToons()

    def exitOff(self):
        pass

    def enterLoadMap(self):
        mapChoice = self.air.datapackMgr.propHuntMaps[random.choice(list(self.air.datapackMgr.propHuntMaps.keys()))]
        self.notify.info(f"enterLoadMap:: Chose Map {mapChoice['map_info']['identifier']}")
        # Wait for everyone to load the map
        self.beginBarrier('WaitForMapLoads', self.involvedToons,
                          PropHuntGlobals.LoadMapTimeout,
                          self.__finishWaitForMapLoad)

        allPossibles = mapChoice.get('prop_spawn_locations',
                                     ((0.0, 0.0, 0.0, 0.0, 0.0, 0.0),)
                                     )
        propSpawns = random.sample(allPossibles, random.randrange(15, 17))  # PLACE HOLDER VALUES,
        # real world we wanna use like 40-60%?

        self.allowedProps = mapChoice['allowed_props']
        self.playerSpawnPoints = mapChoice.get('player_spawn_locations',
                                               ((0.0, 0.0, 0.0, 0.0),)
                                               )
        mapScreenshotPoints = mapChoice.get('map_screenshot_points',
                                            ((0.0, 0.0, 0.0, 0.0, 0.0, 0.0),)
                                            )

        for spawn in propSpawns:
            prop = DistributedPropHuntPropAI(self.air)
            prop.generateWithRequired(self.zoneId)
            prop.b_setPosHpr(*spawn)
            prop.d_setPropModel(random.choice(self.allowedProps))
            self.fakeProps.append(prop)

        self.sendPlayerSpawnPoints()

        geomData = []

        for gi in mapChoice['level_geometry']:
            geomData.append((
                gi['type'], gi['path'],
                gi.get('pos', (0.0, 0.0, 0.0)), gi.get('hpr', (0.0, 0.0, 0.0)), gi.get('scale', (1.0, 1.0, 1.0)),
                gi.get('color', (255, 255, 255, 255)))
            )

        self.sendUpdate('setMapData', [(mapChoice['map_info']['identifier'],
                                        mapChoice['map_info']['name'],
                                        mapChoice['map_info']['author']),
                                       mapChoice['allowed_props'],
                                       mapScreenshotPoints,
                                       geomData])

        # self.sendUpdate('setMap', [mapChoice])

    def __finishWaitForMapLoad(self, task):
        self.notify.info("All players have loaded in. Starting INTRO!")
        self.b_setState('Introduction')

    def sendPlayerSpawnPoints(self):
        hiderSpawnPoints = self.playerSpawnPoints[:]
        hunterSpawnPoints = self.playerSpawnPoints[:]
        for toonId in self.involvedToons:
            if toonId in self.hiders:
                if not hiderSpawnPoints:
                    # We ran out of unique spawn points, so we will need to reallocated all of our spawn points.
                    hiderSpawnPoints = self.playerSpawnPoints[:]
                spawnPoint = random.choice(hiderSpawnPoints)
                spawnPointIndex = hiderSpawnPoints.index(spawnPoint)

                # Remove the spawn point from being used for now.
                # We want to distance hiders from each other.
                del hiderSpawnPoints[spawnPointIndex]
            else:
                if not hunterSpawnPoints:
                    # We ran out of unique spawn points, so we will need to reallocated all of our spawn points.
                    hunterSpawnPoints = self.playerSpawnPoints[:]
                spawnPoint = random.choice(hunterSpawnPoints)
                spawnPointIndex = hunterSpawnPoints.index(spawnPoint)

                # Remove the spawn point from being used for now.
                # We want to distance hunters from each other.
                del hunterSpawnPoints[spawnPointIndex]

            self.sendUpdateToAvatarId(toonId, 'setPlayerSpawnPoint', [spawnPoint[0],
                                                                      spawnPoint[1],
                                                                      spawnPoint[2],
                                                                      spawnPoint[3]])

    def exitLoadMap(self):
        pass

    def enterIntroduction(self):
        self.doMethodLater(PropHuntGlobals.IntroductionLength, self.b_setState, 'introductionTimeout', ['GracePeriod'])
        pass

    def exitIntroduction(self):
        pass

    def enterGracePeriod(self):
        for toonId in self.hiders:
            toon = simbase.air.doId2do.get(toonId)
            if toon:
                self.sendUpdate('hiderTransformedIntoProp', [toonId, random.choice(self.allowedProps)])
        self.doMethodLater(PropHuntGlobals.GracePeriodLength, self.b_setState, 'gracePeriodTimeout', ['Hunt'])

    def transformPropRequest(self):  # propName
        hiderId = self.air.getAvatarIdFromSender()
        if hiderId not in self.hiders:
            self.air.writeServerEvent('suspicious', hiderId,
                                      'Player tried to transform into prop despite not being a hider.')
            return
        hider = self.air.doId2do.get(hiderId)
        if not hider:
            return
        # if propName not in self.allowedProps:
        #     self.air.writeServerEvent('suspicious', hiderId, 'uh oh! prince frizzy is hacking the servers!')
        #     return

        # TEMP
        self.sendUpdate('hiderTransformedIntoProp', [hiderId, random.choice(self.allowedProps)])

    def exitGracePeriod(self):
        pass

    def enterHunt(self):
        for toonId in self.hunters:
            toon = simbase.air.doId2do.get(toonId)
            if toon:
                toon.b_setPieType(9)
                toon.b_setNumPies(self.numFeathers)
        self.doMethodLater(PropHuntGlobals.HuntLength, self.b_setState, 'HuntTimeout', ['Victory'])

    def hiderTickledRequest(self, hiderId: int):
        hunterId = self.air.getAvatarIdFromSender()
        if hunterId not in self.hunters:
            self.air.writeServerEvent('suspicious', hunterId,
                                      'Player tried to tickle prop despite not being a hunter.')
            return

        hunter = self.air.doId2do.get(hunterId)
        if not hunter:
            return

        if hunterId not in self.hunter2PieTimestamp:
            self.hunter2PieTimestamp[hunterId] = 0

        # Is this feather different from our last one?
        # If so, add a feather to our hunter.
        # Otherwise, don't even bother giving us an extra feather.
        hunterPieTimestamp = hunter.pieTimestamp
        if self.hunter2PieTimestamp[hunterId] != hunterPieTimestamp:
            self.hunter2PieTimestamp[hunterId] = hunterPieTimestamp
            hunter.b_setNumPies(hunter.numPies + 1)            

        self.sendUpdate('hiderTickled', [hiderId])

    def hunterFinishedFeatherIval(self):
        hunterId = self.air.getAvatarIdFromSender()
        if hunterId not in self.hunters:
            self.air.writeServerEvent('suspicious', hunterId,
                                      'Player tried to tickle a prop despite not being a hunter.')
            return

        hunter = self.air.doId2do.get(hunterId)
        if not hunter:
            return
            
        if hunter.numPies == 0:
            self.sendUpdate('hunterDied', [hunterId])

    def toonRequestSpectatorMode(self):
        requesterId = self.air.getAvatarIdFromSender()

        if requesterId in self.hiders:
            self.hiders.remove(requesterId)
        elif requesterId in self.hunters:
            self.hunters.remove(requesterId)
        if requesterId not in self.spectators:
            self.spectators.append(requesterId)

        if not self.hiders or not self.hunters:
            self.doMethodLater(1, self.b_setState, 'startVictory', ['Victory'])
            taskMgr.remove('HuntTimeout')
        else:
            self.sendUpdate('toonEnteredSpectatorMode', [requesterId])

    def exitHunt(self):
        pass

    def enterVictory(self):
        for prop in self.fakeProps:
            prop.requestDelete()
        
        for toonId in self.hunters:
            toon = self.air.doId2do.get(toonId)
            toon.b_setNumPies(0)

        if len(self.hunters) > len(self.hiders):
            winners = self.hunters
            losers = self.hiders
            self.d_setWinnerPositions(winners, losers)
        elif len(self.hunters) == len(self.hiders):
            self.sendUpdate('setGameTiePositions', [self.hiders + self.hunters])
        else:
            winners = self.hiders
            losers = self.hunters
            self.d_setWinnerPositions(winners, losers)

    def d_setWinnerPositions(self, winners: List[int], losers: List[int]):
        self.sendUpdate('setWinnerPositions', [winners, losers])

    def exitVictory(self):
        pass
