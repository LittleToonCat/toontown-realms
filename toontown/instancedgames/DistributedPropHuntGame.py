from enum import Enum
import random
from typing import List, Dict, Tuple

from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObject import DistributedObject
from direct.fsm.ClassicFSM import ClassicFSM
from direct.fsm.FSM import FSM
from direct.fsm.State import State
from direct.gui.DirectFrame import DirectFrame
from direct.gui.DirectGui import DGG
from direct.interval.IntervalGlobal import *
from panda3d.core import CSDefault, NodePath, Vec3, CollisionEntry
from panda3d.toontown import loadDNAFile, DNAStorage

from toontown.battle.BattleProps import globalPropPool
from toontown.battle import MovieUtil
from toontown.effects.DustCloud import DustCloud
from toontown.mainmenu.MainMenuLoadingGUI import MainMenuLoadingGUI
from toontown.sandbox.PropGlobals import PropPool
from toontown.toon.DistributedToon import DistributedToon
from toontown.toonbase import TTLocalizer, ToontownGlobals, HotkeySettings
from toontown.toonbase.ToontownTimer import ToontownTimer

from .InstancedGamesGUI import ToonPortrait
from . import PropHuntGlobals
from .PropHuntGlobals import *
from .PropHuntHiderProp import PropHuntHiderProp
from .PropHuntHunterLoadingScreen import PropHuntHunterLoadingScreen
from ..toonbase.ToonBaseGlobal import base
from ..toonbase.ToontownTypes import TPosHpr, TVec3, TColor


class DistributedPropHuntGame(DistributedObject, FSM):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistPropHuntGame')

    def __init__(self, cr):
        DistributedObject.__init__(self, cr)
        FSM.__init__(self, 'PropHuntCLFSM')

        self.map = None
        self.geom = None
        self.timer = None

        self.victoryGeom = None
        self.sky = None
        self.winningTrack = None

        self.toons: List[int] = []
        self.involvedToons: List[int] = []
        self.__clientRole: PropHuntRole = PropHuntRole.WAITING
        self.winners: List[DistributedToon] = []

        self.mapScreenshotPoints: List[TPosHpr] = [(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)]

        self.hiders: List[int] = []
        self.hiderProps: Dict[int, PropHuntHiderProp] = {}
        self.hunters: List[int] = []
        self.spectators: List[int] = []
        self.spectatingAvId: int = 0

        self.__toonRequest = None

        self.__gotAllToons: bool = False

        self.dnaStore = DNAStorage()

        self.localPlayerFSM = ClassicFSM(
                'PropHuntLocalPlayerFSM',
                [
                    State('waiting', self.lp_enterWaiting, self.lp_exitWaiting, ['hunting',
                                                                                 'hiding']),
                    # Hunter
                    State('hunting', self.lp_enterHunting, self.lp_exitHunting, ['waiting',
                                                                                 'hunterDie']),
                    State('hunterDie', self.lp_enterHunterDie, ['spectator']),

                    # Hider
                    State('hiding', self.lp_enterHiding, self.lp_exitHiding, ['waiting',
                                                                              'hiderStoppedForTickle']),
                    State('hiderStoppedForTickle', self.lp_enterHiderStoppedForTickle,
                          self.lp_exitHiderStoppedForTickle, ['hiding',
                                                              'spectator']),
                    State('spectator', self.lp_enterSpectator, ['final']),
                    State('final', self.lp_enterFinal, self.lp_exitFinal, ['hunting',
                                                                           'spectator',
                                                                           'hiding',
                                                                           'hiderStoppedForTickle',
                                                                           'hiderDie'])
                ], 'waiting', 'waiting'
        )

        # Bgm
        self.victoryTheme = base.loader.loadMusic('phase_13/audio/bgm/party_generic_theme_jazzy.ogg')

        # Sfx's
        self.applause = base.loader.loadSfx('phase_6/audio/sfx/Golf_Crowd_Applause.ogg')

    def setState(self, state: str):
        self.notify.info(f'PropHunt: Setting State to {state}')
        self.request(state)

    def announceGenerate(self):
        super().announceGenerate()
        self.timer = ToontownTimer()
        self.timer.reparentTo(base.a2dpTopCenter, DGG.NO_FADE_SORT_INDEX)
        self.timer.setScale(0.2)
        self.timer.setZ(-0.075)
        self.timer.hide()

    def disable(self):
        self.cr.relatedObjectMgr.abortRequest(self.__toonRequest)
        self.__toonRequest = None
        if self.winningTrack:
            self.winningTrack.finish()
            self.winningTrack = None

    def delete(self):
        super().delete()
        if self.geom:
            self.geom.removeNode()
            del self.geom
        if self.map:
            self.map.removeNode()
            del self.map
        if self.victoryGeom:
            self.victoryGeom.removeNode()
            del self.victoryGeom
        if self.sky:
            self.sky.removeNode()
            del self.sky
        if self.timer:
            self.timer.destroy()

    def enterWaitForToons(self):
        self.loadingBlocker = MainMenuLoadingGUI(text = TTLocalizer.CogdoMazeGameWaitingForToons,
                                                 indeterminate = True,
                                                 mini = False)
        self.localPlayerFSM.request('waiting')
        self.__doneWaitForToons()

    def exitWaitForToons(self):
        if self.loadingBlocker:
            self.loadingBlocker.destroy()
            del self.loadingBlocker

    def enterLoadMap(self):
        pass

    def setMapData(self,
                   mapInfo: Tuple[str, str, str],
                   allowedProps: List[str],
                   mapScreenshotPoints: List[TPosHpr],
                   levelGeometry: List[Tuple[str, str, TVec3, TVec3, TVec3, TColor]]
                   ):
        base.loader.beginBulkLoad(
                'prophuntgame',
                TTLocalizer.HeadingToHood % {
                    'to': 'to',
                    'hood': TTLocalizer.PropHuntLoadingHoodText % {
                        'mapName': mapInfo[PropHuntMapInfo.Name],
                        'author': mapInfo[PropHuntMapInfo.Author]
                    }
                }, len(levelGeometry) + 1, 1, TTLocalizer.TIP_GENERAL)

        self.notify.info(
            f'Loading prop hunt map "{mapInfo[PropHuntMapInfo.Name]}" by {mapInfo[PropHuntMapInfo.Author]}')
        self.mapInfo = mapInfo
        self.allowedProps = allowedProps
        self.mapScreenshotPoints = mapScreenshotPoints

        loadDNAFile(self.dnaStore, 'phase_4/dna/storage.dna', CSDefault, 1)
        base.loader.tick()

        self.geom = NodePath(f"PropHuntGeom {mapInfo[0]}")
        self.geom.reparentTo(base.render)

        for geomObj in levelGeometry:
            _type = geomObj[PropHuntGeom.Type]
            _path = geomObj[PropHuntGeom.Path]
            _pos = geomObj[PropHuntGeom.Pos]
            _hpr = geomObj[PropHuntGeom.Hpr]
            _scale = geomObj[PropHuntGeom.Scale]
            _color = geomObj[PropHuntGeom.Color]

            # Load DNA storage files
            if _type == PropHuntGeomType.DNAStorageFile:
                loadDNAFile(self.dnaStore, _path, CSDefault, 1)
                base.loader.tick()

            elif _type == PropHuntGeomType.DNAFile:
                self.map = loadDNAFile(self.dnaStore, _path, CSDefault, 1)
                if self.map.getNumParents() == 1:
                    self.map = NodePath(self.map.getParent(0))
                self.map.reparentTo(render)
                base.loader.tick()

            elif _type == PropHuntGeomType.Model:
                np = loader.loadModel(_path)
                np.reparentTo(self.geom)
                np.setPosHprScale(*_pos, *_hpr, *_scale)
                np.setColorScale(*_color)
                base.loader.tick()

            elif _type == PropHuntGeomType.Prop:
                np = self.geom.attachNewNode('_PROP')
                PropPool.getProp(_path).reparentTo(np)
                np.setPosHprScale(*_pos, *_hpr, *_scale)
                np.setColorScale(*_color)
                base.loader.tick()

        # Hide the black parts in the doors
        doorHoles = self.geom.findAllMatches('**/doorFrameHole*')
        for hole in doorHoles:
            hole.removeNode()

        base.loader.tick()
        base.loader.endBulkLoad('prophuntgame')
        if base.localAvatar.getDoId() in self.hiders:
            base.cr.playGame.getPlace().fsm.request('teleportIn')
        self.doneBarrier('WaitForMapLoads')

    def setPlayerSpawnPoint(self, x, y, z, h):
        base.cr.playGame.getPlace().setPlayerSpawnPoint(x, y, z, h)

    def exitLoadMap(self):
        pass

    def enterIntroduction(self):
        self.localPlayerFSM.request('waiting')
        localId = base.localAvatar.getDoId()
        if localId in self.hiders:
            self.notify.info("YOU ARE A HIDER")
        elif localId in self.hunters:
            self.notify.info("YOU ARE A HUNTER")
            self.loadingBlocker = PropHuntHunterLoadingScreen(random.choice(self.mapScreenshotPoints))
        elif localId in self.spectators:
            self.notify.error("YOU ARE SPECTATING. You shouldn't be right now though. Please report this!")
        else:
            self.notify.warning("Local AV is not a hider, hunter, or spectator. "
                                "(TODO: Make this an ERROR later in dev)")

        self.headerFrame = DirectFrame(parent = base.a2dTopCenter, pos = (0.0, 0.0, -0.1))

        self.headerToonIcons = {}

        for index, avId in enumerate(self.hiders):
            toon = self.getToon(avId)
            icn = ToonPortrait(toon, 0)
            icn.reparentTo(base.a2dpTopCenter, DGG.NO_FADE_SORT_INDEX)
            icn.setZ(-0.075)
            icn.setX(-0.2 - (0.2 * index))
            self.headerToonIcons[avId] = icn

            prop = PropHuntHiderProp(toon)
            self.hiderProps[toon.doId] = prop

        for index, avId in enumerate(self.hunters):
            toon = self.getToon(avId)
            icn = ToonPortrait(toon, 1)
            icn.reparentTo(base.a2dpTopCenter, DGG.NO_FADE_SORT_INDEX)
            icn.setZ(-0.075)
            icn.setX(+0.2 + (0.2 * index))
            self.headerToonIcons[avId] = icn

    def exitIntroduction(self):
        self.timer.hide()

    def enterGracePeriod(self):
        self.timer.show()
        self.timer.countdown(PropHuntGlobals.GracePeriodLength)
        if base.localAvatar.getDoId() in self.hiders:
            self.localPlayerFSM.request('hiding')

    def exitGracePeriod(self):
        self.timer.hide()
        pass

    def enterHunt(self):
        self.timer.show()
        self.timer.countdown(PropHuntGlobals.HuntLength)
        if base.localAvatar.getDoId() in self.hunters:
            self.localPlayerFSM.request('hunting')

    def exitHunt(self):
        pass

    def setToonIds(self, involvedToons: List[int], hiders: List[int], hunters: List[int]):
        self.involvedToons = involvedToons
        self.hiders = hiders
        self.hunters = hunters
        self.cr.relatedObjectMgr.abortRequest(self.__toonRequest)
        self.__gotAllToons = False
        self.__toonRequest = self.cr.relatedObjectMgr.requestObjects(self.involvedToons,
                                                                     allCallback = self.__gotAllToonsCallback,
                                                                     eachCallback = self.__gotToon)

    def __gotAllToonsCallback(self, toons: List[int]):
        self.__gotAllToons = True
        messenger.send('gotAllToons')

    def __gotToon(self, toon):
        pass

    ''' === Local Player FSM === '''

    def lp_enterWaiting(self):
        base.cr.playGame.getPlace().fsm.request('stopped')

    def lp_exitWaiting(self):
        pass

    def lp_enterFinal(self):
        pass

    def lp_exitFinal(self):
        pass

    ''' Hunter Specific '''

    def lp_enterHunting(self):
        if hasattr(self, 'loadingBlocker'):
            self.loadingBlocker.destroy()
            del self.loadingBlocker

        base.cr.playGame.getPlace().fsm.request('teleportIn', ['walk'])
        self.accept('localFeatherTouch', self.__hunterInteractedWithHider)
        self.accept('localFeatherIvalDone', self.__hunterFinishedFeatherIval)

    def __hunterInteractedWithHider(self, entry: CollisionEntry):
        node = entry.getIntoNodePath()
        hiderDoId = node.getNetTag('hiderDoId')
        if hiderDoId == '':
            return
        hiderDoId = int(hiderDoId)
        # temp print
        print(f'hiderDoId of the toons!!! {hiderDoId}')
        self.sendUpdate('hiderTickledRequest', [hiderDoId])

    def __hunterFinishedFeatherIval(self):
        self.sendUpdate('hunterFinishedFeatherIval')

    def hunterDied(self, hunterId: int):
        if base.localAvatar.doId == hunterId:
            self.localPlayerFSM.request('hunterDie')

        toon = self.getToon(hunterId)
        toonGeom = toon.getGeomNode()

        def getDustCloudIval(toon: DistributedToon = toon) -> Sequence:
            dustCloud = DustCloud(toon, fBillboard = 0, wantSound = 1)
            dustCloud.setBillboardAxis(2.0)
            dustCloud.setZ(3)
            dustCloud.setScale(0.4)
            dustCloud.createTrack()
            return Sequence(dustCloud.track, Func(dustCloud.destroy), name='dustCloadIval')

        deathIval = Sequence(
            Func(toon.sadEyes),
            Func(toon.blinkEyes),
            Parallel(
                Sequence(
                    Wait(1),
                    getDustCloudIval()
                ),
                Sequence(
                    Wait(1),
                    LerpColorScaleInterval(toon, 0.3, (1, 1, 1, 0), blendType='easeInOut'),
                    Func(toonGeom.hide),
                    Func(toon.hideNametag2d),
                    Func(toon.hideNametag3d)
                )
            )
        )
        if hunterId == base.localAvatar.getDoId():
            deathIval.append(Func(self.__toonRequestSpectatorMode))
        deathIval.start()

    def lp_exitHunting(self):
        self.ignore('localFeatherTouch')
        self.ignore('featherIvalDone')

    def lp_interactedWithProp(self, propId: int):
        self.localPlayerFSM.request('hunterStoppedForTickle', [propId])

    def lp_enterHunterDie(self):
        base.cr.playGame.getPlace().fsm.request('stopped')

    def lp_exitHunterDie(self):
        pass

    ''' Hider Specific '''

    def lp_enterHiding(self):
        base.cr.playGame.getPlace().fsm.request('walk')
        # temp
        self.accept(HotkeySettings.Action.getPressed(),
                    self.d_transformPropRequest)

    def d_transformPropRequest(self):
        self.sendUpdate('transformPropRequest')

    def lp_exitHiding(self):
        self.ignore(HotkeySettings.Action.getPressed())

    def lp_enterHiderStoppedForTickle(self):
        """
        Hider was interacted with, stop the toon and play the animation, and disable prop switching
        """
        base.cr.playGame.getPlace().fsm.request('stopped')

    def lp_exitHiderStoppedForTickle(self):
        pass

    def hiderTransformedIntoProp(self, hiderId: int, propName: str):
        prop = self.getProp(hiderId)
        if prop:
            prop.transformProp(propName)

    def hiderTickled(self, hiderId: int):
        if base.localAvatar.doId == hiderId:
            self.localPlayerFSM.request('hiderStoppedForTickle')

        prop = self.getProp(hiderId)
        if prop:
            callback = None
            if hiderId == base.localAvatar.getDoId():
               callback = self.__toonRequestSpectatorMode
            prop.playDeathInterval(callback)

    ''' All Players '''

    def __toonRequestSpectatorMode(self):
        self.sendUpdate('toonRequestSpectatorMode')

    def toonEnteredSpectatorMode(self, avId: int):
        toon = self.getToon(avId)
        if not toon:
            return

        self.spectators.append(avId)
        if avId in self.hiders:
            self.hiders.remove(avId)
        if avId in self.hunters:
            self.hunters.remove(avId)

        toonIcn = self.headerToonIcons[avId]
        toonIcn.setTeamColor(3)
        toonIcn['command'] = None

        if avId == self.spectatingAvId:
            remainingPlayerIds = self.hiders + self.hunters
            newSpectatorAvId = random.choice(remainingPlayerIds)
            self.lp_spectateToon(newSpectatorAvId)

        if avId == base.localAvatar.getDoId():
            self.localPlayerFSM.request('spectator')

    def lp_enterSpectator(self):
        remainingPlayerIds = self.hiders + self.hunters
        spectatingAvId = random.choice(remainingPlayerIds)

        for avId in self.headerToonIcons:
            if avId != base.localAvatar.doId and avId != spectatingAvId and \
                    avId not in self.spectators:
                icn = self.headerToonIcons[avId]
                icn['command'] = self.lp_spectateToon
                icn['extraArgs'] = [avId]

        self.lp_spectateToon(spectatingAvId)

    def lp_spectateToon(self, avId: int):
        toon = self.getToon(avId)

        icn = self.headerToonIcons[avId]
        icn.setTeamColor(2)
        icn['command'] = None

        if self.spectatingAvId:
            previousIcn = self.headerToonIcons[self.spectatingAvId]
            if self.spectatingAvId in self.spectators:
                previousIcn.setTeamColor(3)
                icn['command'] = None
            else:
                teamNum = 0 if self.spectatingAvId in self.hiders else 1
                previousIcn.setTeamColor(teamNum)
                icn['command'] = self.lp_spectateToon
                icn['extraArgs'] = [self.spectatingAvId]

        self.spectatingAvId = avId
        base.localAvatar.setPos(toon.getPos())
        base.localAvatar.setHpr(toon.getHpr())
        base.localAvatar.reparentTo(toon)

    def lp_exitSpectator(self):
        pass

    def __doneWaitForToons(self):
        self.doneBarrier('WaitForToons')

    def getToon(self, avId: int) -> DistributedToon:
        if avId in self.cr.doId2do:
            return self.cr.doId2do[avId]

    def getProp(self, hiderId: int):
        if hiderId in self.hiderProps:
            return self.hiderProps[hiderId]

    def removeHeaderToonIcons(self):
        for avId in self.headerToonIcons:
            self.headerToonIcons[avId].removeNode()

    def setWinnerPositions(self, winners: List[int], losers: List[int]):
        # Should we keep the spectators hidden or should they be showcased with the rest of the toons?
        for avId in winners:
            toon = self.getToon(avId)
            self.winners.append(toon)
                
        for avId in losers:
            toon = self.getToon(avId)
            toon.hide()

        for x in range(len(self.winners)):
            seq = Sequence(
                Wait(0.5),
                Func(self.winners[x].setPosHpr, -6 + x, 41, 0.03, 180, 0, 0),
                Func(self.winners[x].loop, random.choice(PropHuntGlobals.VICTORY_ANIMS))
            )
            seq.start()
        self.removeHeaderToonIcons()

    def setGameTiePositions(self, toons: List[int]):
        # TODO: Transform the hiders back into toons
        aliveToons = []
        for avId in toons:
            toon = self.getToon(avId)
            aliveToons.append(toon)

        for x in range(len(aliveToons)):
            seq = Sequence(
                Wait(0.5),
                Func(aliveToons[x].setPosHpr, -6 + x, 41, 0.03, 180, 0, 0),
                Func(aliveToons[x].loop, 'shrug')
            )
            seq.start()
        self.removeHeaderToonIcons()

    def loadVictoryGeom(self):
        self.map.removeNode()
        self.geom.removeNode()

        self.victoryGeom = loader.loadModel('phase_4/models/minigames/tag_arena.bam')
        self.victoryGeom.reparentTo(render)

        self.sky = loader.loadModel('phase_3.5/models/props/TT_sky')
        self.sky.reparentTo(render)

        LerpHprInterval(self.sky, 100, (360, 0, 0)).loop()

    def enterVictory(self):
        self.timer.hide()
        base.localAvatar.disableAvatarControls()
        base.localAvatar.b_setAnimState('neutral')
        
        self.winningTrack = Sequence(
            # TODO: Finish feather animation or any death tracks before showcasing the toons
            Func(base.transitions.irisOut, 0.5),
            Wait(4),
            Parallel(
                Func(base.localAvatar.deactivateCamera),
                Func(base.camera.reparentTo, render),
                Func(base.camera.setPosHpr, -32.9, -0.27, 2.2, -33, 5, 0),
                Func(base.camLens.setFov, 60)
            ),
            Parallel(
                Func(base.transitions.irisIn, 0.5),
                Func(base.playMusic, self.victoryTheme, looping = 1, volume = 0.5),
                Func(self.loadVictoryGeom)
            ),
            Parallel(
                base.camera.posHprInterval(4, (-1.7, 25.0, 3.0), (-4.4, 5, 0), blendType='easeInOut'),
                SoundInterval(self.applause)
            )
        )
        self.winningTrack.start()

    def exitVictory(self):
        self.winningTrack.finish()
        