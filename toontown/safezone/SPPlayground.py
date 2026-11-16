from panda3d.toontown import DNAStorage, NametagGlobals, loadDNAFileAI

from direct.fsm import State
from direct.showbase.PythonUtil import Functor

from otp.distributed.TelemetryLimiter import RotationLimitToH, TLGatherAllAvs

from toontown.battle import BattleParticles
from toontown.building import Elevator
from toontown.hood import ZoneUtil
from toontown.safezone import PicnicBasket
from toontown.toonbase import ToontownGlobals

from . import Playground


class SPPlayground(Playground.Playground):

    def __init__(self, loader, parentFSM, doneEvent):
        Playground.Playground.__init__(self, loader, parentFSM, doneEvent)
        self.parentFSM = parentFSM

        self.fsm.addState(State.State('picnicBasketBlock', self.enterPicnicBasketBlock, self.exitPicnicBasketBlock, ['walk']))
        self.fsm.addState(State.State('elevatorIn', self.enterElevatorIn, self.exitElevatorIn, ['walk', 'start']))
        self.fsm.addState(State.State('elevator', self.enterElevator, self.exitElevator, ['walk', 'start']))

        state = self.fsm.getStateNamed('walk')
        state.addTransition('picnicBasketBlock')

        stateNames = ('walk', 'start')
        for stateName in stateNames:
            state = self.fsm.getStateNamed(stateName)
            state.addTransition('elevatorIn')
            state.addTransition('elevator')

        self.picnicBasketBlockDoneEvent = 'picnicBasketBlockDone'
        self.picnicBasketDoneEvent = 'picnicBasketDone'

        self.elevatorDoneEvent = 'elevatorDone'

    def enter(self, requestStatus):
        self.fsm.enterInitialState()
        messenger.send('enterPlayground')
        self.accept('doorDoneEvent', self.handleDoorDoneEvent)
        self.accept('DistributedDoor_doorTrigger', self.handleDoorTrigger)
        if not base.cr.doFind('DistributedSafezoneJukebox'):
            base.playMusic(self.loader.music, looping=1, volume=0.8)
        self.loader.geom.reparentTo(render)
        for i in self.loader.nodeList:
            self.loader.enterAnimatedProps(i)

        self._telemLimiter = TLGatherAllAvs('Playground', RotationLimitToH)

        NametagGlobals.setMasterArrowsOn(1)
        self.zoneId = requestStatus['zoneId']
        self.tunnelOriginList = base.cr.hoodMgr.addLinkTunnelHooks(self, self.loader.nodeList)
        how = requestStatus['how']
        if how == 'teleportIn':
            how = 'deathAck'
        self.fsm.request(how, [requestStatus])
        base.cr.discordManager.setInfo(base.cr.discordManager.getState(), None, ToontownGlobals.Zone2String.get(ZoneUtil.getHoodId(self.zoneId)), None, None, None, self.zoneId)

        def __lightDecorationOn__():
            geom = base.cr.playGame.hood.loader.geom
            self.loader.hood.halloweenLights = geom.findAllMatches('**/*light*')
            self.loader.hood.halloweenLights += geom.findAllMatches('**/*lamp*')
            self.loader.hood.halloweenLights += geom.findAllMatches('**/prop_snow_tree*')
            for light in self.loader.hood.halloweenLights:
                light.setColorScaleOff(0)

        def __enableSnow():
            if hasattr(self, 'snow') and self.snow:
                return
            self.snow = BattleParticles.loadParticleFile('snowdisk.ptf')
            self.snow.setPos(0, 0, 5)
            self.snowRender = base.cr.playGame.hood.loader.geom.attachNewNode('snowRender')
            self.snowRender.setDepthWrite(0)
            self.snowRender.setBin('fixed', 1)
            self.snow.start(camera, self.snowRender)

        # Get theme information
        decoration = ToontownGlobals.Theme2Decoration.get('tt')

        # Enable Fog and unique skybox for Winter Holiday
        fog = decoration[ToontownGlobals.ThemeFog]
        snow = decoration[ToontownGlobals.ThemeSnow]
        newsManager = base.cr.newsManager
        if newsManager:
            holidayIds = base.cr.newsManager.getDecorationHolidayId()
            if (ToontownGlobals.WINTER_DECORATIONS in holidayIds or ToontownGlobals.WINTER_CAROLING in holidayIds) and decoration[ToontownGlobals.ThemeWinter]:
                fog = True
                snow = True
                self.loader.hood.startWinterSky()
                __lightDecorationOn__()
            elif (ToontownGlobals.HALLOWEEN_COSTUMES in holidayIds or ToontownGlobals.SPOOKY_COSTUMES in holidayIds) and decoration[ToontownGlobals.ThemeHalloween]:
                self.loader.hood.startSpookySky()
                self.loader.geom.setColorScale(0.55, 0.55, 0.65, 1)
                __lightDecorationOn__()
            else:
                self.loader.hood.startSky()
        else:
            self.loader.hood.startSky()

        # Enable Snow regardless of the winter holiday if the theme calls for it
        if snow:
            __enableSnow()

        # Enable Fog regardless of the winter holiday if the theme calls for it
        if fog:
            self.loader.hood.setWhiteFog()

        # First, we need to load the DNA file for the Outskirts
        self.dnaStore = DNAStorage()
        dnaFileName = 'phase_14.5/dna/special_hood_sz_tt.dna'
        loadDNAFileAI(self.dnaStore, dnaFileName)

        # Next, we need to collect all of the visgroup zone IDs
        self.zoneVisDict = {}
        for i in range(self.dnaStore.getNumDNAVisGroupsAI()):
            visGroup = self.dnaStore.getDNAVisGroupAI(i)
            groupFullName = visGroup.getName()
            visZoneId = int(base.cr.hoodMgr.extractGroupName(groupFullName))
            visibles = []
            for i in range(visGroup.getNumVisibles()):
                visibles.append(int(visGroup.getVisibleName(i)))

            visibles.append(ZoneUtil.getBranchZone(visZoneId))
            self.zoneVisDict[visZoneId] = visibles

        # Finally, we want interest in all visgroups due to the nature of this zone
        base.cr.sendSetZoneMsg(self.zoneId, list(self.zoneVisDict.values())[0])

    def exit(self):
        Playground.Playground.exit(self)

        decoration = ToontownGlobals.Theme2Decoration.get('tt')

        # Disable snow if we have any
        if hasattr(self, 'snow'):
            self.snow.cleanup()
            del self.snow
        if hasattr(self, 'snowRender'):
            del self.snowRender

        # Disable Fog for Winter Holiday
        newsManager = base.cr.newsManager
        if newsManager:
            holidayIds = base.cr.newsManager.getDecorationHolidayId()
            if ToontownGlobals.WINTER_DECORATIONS in holidayIds or ToontownGlobals.WINTER_CAROLING in holidayIds:
                self.loader.hood.setNoFog()
                return

        # Remove Fog if the theme called for it
        if decoration[ToontownGlobals.ThemeFog]:
            self.loader.hood.setNoFog()

    def createPicnic(self, picnicBasket):
        self.accept(self.picnicBasketDoneEvent, self.handlePicnicBasketDone)
        place = base.cr.playGame.getPlace()

        if not hasattr(place, 'picnic') or not place.picnic:
            place.picnic = PicnicBasket.PicnicBasket(place, place.fsm, self.picnicBasketDoneEvent,
                                                     picnicBasket.getDoId(), picnicBasket.seatNumber)
            place.picnic.load()
            place.picnic.enter()

    def enterPicnicBasketBlock(self, picnicBasket):
        base.localAvatar.laffMeter.start()
        base.localAvatar.b_setAnimState('off', 1)
        self.createPicnic(picnicBasket)

    def exitPicnicBasketBlock(self):
        base.localAvatar.laffMeter.stop()
        self.ignore(self.picnicBasketDoneEvent)
        place = base.cr.playGame.getPlace()
        if hasattr(place, 'picnic') and place.picnic:
            place.picnic.unload()
            place.picnic.exit()

        place.picnic = None

    def detectedPicnicTableSphereCollision(self, picnicBasket):
        if self.fsm.getCurrentState().getName() != 'picnicBasketBlock':
            self.fsm.request('picnicBasketBlock', [picnicBasket])

    def handlePicnicBasketDone(self, doneStatus):
        self.notify.debug('handling picnic basket done event')
        mode = doneStatus['mode']
        if mode == 'reject':
            self.fsm.request('walk')
        elif mode == 'exit':
            self.fsm.request('walk')
        else:
            self.notify.error('Unknown mode: ' + mode + ' in handlePicnicBasketDone')

    def showPaths(self):
        from toontown.classicchars import CCharPaths
        from toontown.toonbase import TTLocalizer
        self.showPathPoints(CCharPaths.getPaths(TTLocalizer.MagicMinnie))

    def enterElevatorIn(self, requestStatus):
        self._eiwbTask = taskMgr.add(Functor(self._elevInWaitBldgTask, requestStatus['bldgDoId']), uniqueName('elevInWaitBldg'))

    def _elevInWaitBldgTask(self, bldgDoId, task):
        # Restart laff regen when exiting cog bldg through elevator (victory)
        messenger.send('enterSafeZone')
        bldg = base.cr.doId2do.get(bldgDoId)
        if bldg:
            if bldg.elevatorNodePath is not None:
                self._enterElevatorGotElevator()
                return task.done
        return task.cont

    def _enterElevatorGotElevator(self):
        messenger.send('insideVictorElevator')

    def exitElevatorIn(self):
        taskMgr.remove(self._eiwbTask)

    def enterElevator(self, distElevator):
        self.accept(self.elevatorDoneEvent, self.handleElevatorDone)
        self.elevator = Elevator.Elevator(self.fsm.getStateNamed('elevator'), self.elevatorDoneEvent, distElevator)
        self.elevator.load()
        self.elevator.enter()

    def exitElevator(self):
        self.ignore(self.elevatorDoneEvent)
        self.elevator.unload()
        self.elevator.exit()
        del self.elevator

    def enterTeleportIn(self, requestStatus):
        # Restart laff regen for exiting cog bldg through book
        messenger.send('enterSafeZone')
        Playground.Playground.enterTeleportIn(self, requestStatus)

    def detectedElevatorCollision(self, distElevator):
        self.fsm.request('elevator', [distElevator])

    def handleElevatorDone(self, doneStatus):
        self.notify.debug('handling elevator done event')
        where = doneStatus['where']
        if where == 'reject':
            if hasattr(base.localAvatar, 'elevatorNotifier') and base.localAvatar.elevatorNotifier.isNotifierOpen():
                pass
            else:
                self.fsm.request('walk')
        elif where == 'exit':
            self.fsm.request('walk')
        elif where in ('suitInterior', 'cogdoInterior'):
            self.doneStatus = doneStatus
            # Stop laff regen when entering cog bldg
            messenger.send('exitSafeZone')
            messenger.send(self.doneEvent)
        else:
            self.notify.error('Unknown mode: ' + where + ' in handleElevatorDone')
