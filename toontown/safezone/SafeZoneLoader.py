from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM
from direct.fsm import State
from direct.fsm import StateData
from direct.showbase.MessengerGlobal import messenger
from panda3d.core import ModelPool, TexturePool

from otp.otpbase.PythonUtil import uniqueName
from toontown.building import BuildingUtil
from toontown.hood import QuietZoneState
from toontown.hood import ZoneUtil
from toontown.toon.Toon import teleportDebug
from toontown.toonbase import ToontownGlobals, ClientSettings
from toontown.toonbase.ToonBaseGlobal import *
from toontown.town import TownBattle


class SafeZoneLoader(StateData.StateData):
    notify = DirectNotifyGlobal.directNotify.newCategory('SafeZoneLoader')

    def __init__(self, hood, parentFSMState, doneEvent):
        StateData.StateData.__init__(self, doneEvent)
        self.hood = hood
        self.parentFSMState = parentFSMState
        self.fsm = ClassicFSM.ClassicFSM('SafeZoneLoader', [State.State('start', self.enterStart, self.exitStart, ['quietZone', 'playground', 'toonInterior']),
                                                            State.State('playground', self.enterPlayground, self.exitPlayground, ['quietZone']),
                                                            State.State('toonInterior', self.enterToonInterior, self.exitToonInterior, ['quietZone']),
                                                            State.State('quietZone', self.enterQuietZone, self.exitQuietZone, ['playground', 'toonInterior']),
                                                            State.State('golfcourse', self.enterGolfcourse, self.exitGolfcourse, ['quietZone', 'playground']),
                                                            State.State('final', self.enterFinal, self.exitFinal, ['start'])], 'start', 'final')
        self.placeDoneEvent = 'placeDone'
        self.townBattleDoneEvent = 'town-battle-done'
        self.place = None
        self.playgroundClass = None
        return

    def load(self):
        if self.musicFile:
            self.music = base.loader.loadMusic(self.musicFile)
        else:
            self.music = None
        self.activityMusic = base.loader.loadMusic(self.activityMusicFile)
        if not hasattr(self, 'battleMusicFile') or not ClientSettings.NewStreetBattleMusic.get():
            self.battleMusic = base.loader.loadMusic('phase_3.5/audio/bgm/encntr_general_bg.ogg')
        else:
            self.battleMusic = base.loader.loadMusic(self.battleMusicFile)

        self.townBattle = TownBattle.TownBattle(self.townBattleDoneEvent)
        self.townBattle.load()

        self.createSafeZone(self.dnaFile)
        self.parentFSMState.addChild(self.fsm)

    def unload(self):
        self.parentFSMState.removeChild(self.fsm)
        del self.parentFSMState
        self.geom.removeNode()
        del self.geom
        del self.fsm
        del self.hood
        del self.nodeList
        del self.playgroundClass
        del self.music
        del self.activityMusic
        del self.battleMusic
        self.townBattle.unload()
        self.townBattle.cleanup()
        del self.holidayPropTransforms
        self.deleteAnimatedProps()
        self.ignoreAll()
        ModelPool.garbageCollect()
        TexturePool.garbageCollect()

    def enter(self, requestStatus):
        self.fsm.enterInitialState()
        messenger.send('enterSafeZone')
        self.setState(requestStatus['where'], requestStatus)

    def exit(self):
        messenger.send('exitSafeZone')

    def setState(self, stateName, requestStatus):
        self.fsm.request(stateName, [requestStatus])

    def createSafeZone(self, dnaFile):
        if self.safeZoneStorageDNAFile:
            if isinstance(self.safeZoneStorageDNAFile, tuple):
                for storage in self.safeZoneStorageDNAFile:
                    loader.loadDNAFile(self.hood.dnaStore, storage)
            else:
                loader.loadDNAFile(self.hood.dnaStore, self.safeZoneStorageDNAFile)
        node = loader.loadDNAFile(self.hood.dnaStore, dnaFile)
        if node.getNumParents() == 1:
            self.geom = NodePath(node.getParent(0))
            self.geom.reparentTo(hidden)
        else:
            self.geom = hidden.attachNewNode(node)
        self.makeDictionaries(self.hood.dnaStore)
        self.createAnimatedProps(self.nodeList)
        self.holidayPropTransforms = {}
        npl = self.geom.findAllMatches('**/=DNARoot=holiday_prop')
        for i in range(npl.getNumPaths()):
            np = npl.getPath(i)
            np.setTag('transformIndex', repr(i))
            self.holidayPropTransforms[i] = np.getNetTransform()

        self.geom.flattenMedium()
        gsg = base.win.getGsg()
        if gsg:
            self.geom.prepareScene(gsg)

    def makeDictionaries(self, dnaStore):
        self.nodeList = []
        for i in range(dnaStore.getNumDNAVisGroups()):
            groupFullName = dnaStore.getDNAVisGroupName(i)
            groupName = base.cr.hoodMgr.extractGroupName(groupFullName)
            groupNode = self.geom.find('**/' + groupFullName)
            if groupNode.isEmpty():
                self.notify.error('Could not find visgroup')
            else:
                self.nodeList.append(groupNode)

        self.removeLandmarkBlockNodes()
        self.hood.dnaStore.resetPlaceNodes()
        self.hood.dnaStore.resetDNAGroups()
        self.hood.dnaStore.resetDNAVisGroups()
        self.hood.dnaStore.resetDNAVisGroupsAI()

    def removeLandmarkBlockNodes(self):
        npc = self.geom.findAllMatches('**/suit_building_origin')
        for i in range(npc.getNumPaths()):
            npc.getPath(i).removeNode()

    def enterStart(self):
        pass

    def exitStart(self):
        pass

    def enterPlayground(self, requestStatus):
        self.acceptOnce(self.placeDoneEvent, self.handlePlaygroundDone)
        self.place = self.playgroundClass(self, self.fsm, self.placeDoneEvent)
        self.place.load()
        self.place.enter(requestStatus)
        base.cr.playGame.setPlace(self.place)

        occluders = self.geom.findAllMatches('**/+OccluderNode')
        for occluder in occluders:
            render.setOccluder(occluder)
            occluder.node().setDoubleSided(True)

        if base.cr.newsManager.isHolidayRunning(ToontownGlobals.HALLOWEEN_COSTUMES):
            pumpkins = render.findAllMatches('**/decorPumpkin*')
            for pumpkin in pumpkins:
                pumpkin.reparentTo(self.geom)

    def exitPlayground(self):
        self.ignore(self.placeDoneEvent)
        self.place.exit()
        self.place.unload()
        self.place = None
        base.cr.playGame.setPlace(self.place)

        render.clearOccluder()

    def handlePlaygroundDone(self):
        status = self.place.doneStatus
        teleportDebug(status, 'handlePlaygroundDone, doneStatus=%s' % (status,))
        if ZoneUtil.getBranchZone(status['zoneId']) == self.hood.hoodId:
            teleportDebug(status, 'same branch')
            self.fsm.request('quietZone', [status])
        else:
            self.doneStatus = status
            teleportDebug(status, 'different hood/branch')
            messenger.send(self.doneEvent)

    def enterToonInterior(self, requestStatus):
        self.acceptOnce(self.placeDoneEvent, self.handleToonInteriorDone)
        self.place = BuildingUtil.getInteriorPlaceFromZoneId(requestStatus['zoneId'])(self, self.fsm.getStateNamed('toonInterior'), self.placeDoneEvent)
        base.cr.playGame.setPlace(self.place)
        self.place.load()
        self.place.enter(requestStatus)

    def exitToonInterior(self):
        self.ignore(self.placeDoneEvent)
        self.place.exit()
        self.place.unload()
        self.place = None
        base.cr.playGame.setPlace(self.place)

    def handleToonInteriorDone(self):
        status = self.place.doneStatus
        if ZoneUtil.getBranchZone(status['zoneId']) == self.hood.hoodId:
            self.fsm.request('quietZone', [status])
        else:
            self.doneStatus = status
            messenger.send(self.doneEvent)

    def enterQuietZone(self, requestStatus):
        self.quietZoneDoneEvent = uniqueName('quietZoneDone')
        self.acceptOnce(self.quietZoneDoneEvent, self.handleQuietZoneDone)
        self.quietZoneStateData = QuietZoneState.QuietZoneState(self.quietZoneDoneEvent)
        self.quietZoneStateData.load()
        self.quietZoneStateData.enter(requestStatus)

    def exitQuietZone(self):
        self.ignore(self.quietZoneDoneEvent)
        del self.quietZoneDoneEvent
        self.quietZoneStateData.exit()
        self.quietZoneStateData.unload()
        self.quietZoneStateData = None

    def handleQuietZoneDone(self):
        status = self.quietZoneStateData.getRequestStatus()
        if status['where'] == 'estate':
            self.doneStatus = status
            messenger.send(self.doneEvent)
        else:
            self.fsm.request(status['where'], [status])

    def enterFinal(self):
        pass

    def exitFinal(self):
        pass

    def createAnimatedProps(self, nodeList):
        from toontown.hood.GenericAnimatedProp import GenericAnimatedProp
        from toontown.hood.HQTelescopeAnimatedProp import HQTelescopeAnimatedProp
        from toontown.hood.HQPeriscopeAnimatedProp import HQPeriscopeAnimatedProp
        from toontown.hood.PetShopFishAnimatedProp import PetShopFishAnimatedProp
        from toontown.hood.HalloweenBloodsuckerAnimatedProp import HalloweenBloodsuckerAnimatedProp
        from toontown.hood.HydrantZeroAnimatedProp import HydrantZeroAnimatedProp
        from toontown.hood.HydrantOneAnimatedProp import HydrantOneAnimatedProp
        from toontown.hood.HydrantTwoAnimatedProp import HydrantTwoAnimatedProp
        from toontown.hood.MailboxZeroAnimatedProp import MailboxZeroAnimatedProp
        from toontown.hood.MailboxOneAnimatedProp import MailboxOneAnimatedProp
        from toontown.hood.MailboxTwoAnimatedProp import MailboxTwoAnimatedProp
        from toontown.hood.TrashcanZeroAnimatedProp import TrashcanZeroAnimatedProp
        from toontown.hood.TrashcanOneAnimatedProp import TrashcanOneAnimatedProp
        from toontown.hood.TrashcanTwoAnimatedProp import TrashcanTwoAnimatedProp

        name2Module = {
            'GenericAnimatedProp': GenericAnimatedProp,
            'HQTelescopeAnimatedProp': HQTelescopeAnimatedProp,
            'HQPeriscopeAnimatedProp': HQPeriscopeAnimatedProp,
            'PetShopFishAnimatedProp': PetShopFishAnimatedProp,
            'HalloweenBloodsuckerAnimatedProp': HalloweenBloodsuckerAnimatedProp,
            'HydrantZeroAnimatedProp': HydrantZeroAnimatedProp,
            'HydrantOneAnimatedProp': HydrantOneAnimatedProp,
            'HydrantTwoAnimatedProp': HydrantTwoAnimatedProp,
            'MailboxZeroAnimatedProp': MailboxZeroAnimatedProp,
            'MailboxOneAnimatedProp': MailboxOneAnimatedProp,
            'MailboxTwoAnimatedProp': MailboxTwoAnimatedProp,
            'TrashcanZeroAnimatedProp': TrashcanZeroAnimatedProp,
            'TrashcanOneAnimatedProp': TrashcanOneAnimatedProp,
            'TrashcanTwoAnimatedProp': TrashcanTwoAnimatedProp,
        }

        self.animPropDict = {}
        for i in nodeList:
            animPropNodes = i.findAllMatches('**/animated_prop_*')
            numAnimPropNodes = animPropNodes.getNumPaths()
            for j in range(numAnimPropNodes):
                animPropNode = animPropNodes.getPath(j)
                if animPropNode.getName().startswith('animated_prop_generic'):
                    className = 'GenericAnimatedProp'
                else:
                    className = animPropNode.getName()[14:-8]
                animPropModule = name2Module.get(className)
                if not animPropModule:
                    self.notify.error(f'Class for animated prop {className} not found.')
                    return
                animPropObj = animPropModule(animPropNode)
                animPropList = self.animPropDict.setdefault(i, [])
                animPropList.append(animPropObj)

            interactivePropNodes = i.findAllMatches('**/interactive_prop_*')
            numInteractivePropNodes = interactivePropNodes.getNumPaths()
            for j in range(numInteractivePropNodes):
                interactivePropNode = interactivePropNodes.getPath(j)
                className = 'GenericAnimatedProp'
                interactivePropModule = name2Module.get(className)
                if not interactivePropModule:
                    self.notify.error(f'Class for interactive prop {className} not found.')
                    return
                interactivePropObj = interactivePropModule(interactivePropNode)
                animPropList = self.animPropDict.get(i)
                if animPropList is None:
                    animPropList = self.animPropDict.setdefault(i, [])
                animPropList.append(interactivePropObj)

        return

    def deleteAnimatedProps(self):
        for zoneNode, animPropList in list(self.animPropDict.items()):
            for animProp in animPropList:
                animProp.delete()

        del self.animPropDict

    def enterAnimatedProps(self, zoneNode):
        for animProp in self.animPropDict.get(zoneNode, ()):
            animProp.enter()

    def exitAnimatedProps(self, zoneNode):
        for animProp in self.animPropDict.get(zoneNode, ()):
            animProp.exit()

    def enterGolfcourse(self, requestStatus):
        base.transitions.fadeOut(t=0)

    def exitGolfcourse(self):
        pass
