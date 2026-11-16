from direct.fsm import State
from direct.task import Task

from panda3d.core import *

from toontown.battle import BattleParticles
from toontown.safezone import PicnicBasket

from . import Street


class OZStreet(Street.Street):
    waterLevel = 1.5

    def __init__(self, loader, parentFSM, doneEvent):
        Street.Street.__init__(self, loader, parentFSM, doneEvent)
        self.sky = self.loader.hood.sky
        self.skyFile = 'phase_8/models/props/DL_sky'
        self.underwaterSound = base.loader.loadSfx('phase_4/audio/sfx/AV_ambient_water.ogg')
        self.swimSound = base.loader.loadSfx('phase_4/audio/sfx/AV_swim_single_stroke.ogg')
        self.submergeSound = base.loader.loadSfx('phase_5.5/audio/sfx/AV_jump_in_water.ogg')
        self.cameraSubmerged = -1
        self.toonSubmerged = -1
        self.underwaterFogColor = Vec4(0.0, 0.0, 0.6, 1.0)
        self.fsm.addState(State.State('picnicBasketBlock', self.enterPicnicBasketBlock, self.exitPicnicBasketBlock, ['walk']))
        state = self.fsm.getStateNamed('walk')
        state.addTransition('picnicBasketBlock')
        self.picnicBasketDoneEvent = 'picnicBasketDone'

    def enter(self, requestStatus, visibilityFlag = 1, arrowsOn = 1):
        Street.Street.enter(self, requestStatus, visibilityFlag, arrowsOn)

        messenger.send('enterSafeZone')

        if hasattr(self, 'sky') and self.sky:
            self.loader.hood.stopSky()

        self.sky = loader.loadModel(self.skyFile)
        self.sky.setTag('sky', 'Night')
        self.sky.setScale(1.0)
        self.sky.setDepthTest(0)
        self.sky.setDepthWrite(0)
        self.sky.setColor(0.5, 0.5, 0.5, 1)
        self.sky.setBin('background', 100)
        self.sky.setFogOff()
        self.sky.reparentTo(camera)
        self.sky.setTransparency(TransparencyAttrib.MDual, 1)
        fadeIn = self.sky.colorScaleInterval(1.5, Vec4(1, 1, 1, 1), startColorScale=Vec4(1, 1, 1, 0.25),
                                             blendType='easeInOut')
        fadeIn.start()
        self.sky.setZ(0.0)
        self.sky.setHpr(0.0, 0.0, 0.0)
        ce = CompassEffect.make(NodePath(), CompassEffect.PRot | CompassEffect.PZ)
        self.sky.node().setEffect(ce)

        self.loader.hood.sky = self.sky

        self.campfire = BattleParticles.loadParticleFile('campfire.ptf')
        self.campfire.start(render)

        self.fireCollSphere = CollisionSphere(5, 0, 10, 7.5)
        self.fireCollSphere.setTangible(0)
        self.fireCollNode = CollisionNode('ouch')
        self.fireCollNode.addSolid(self.fireCollSphere)
        self.fireCollNodePath = render.attachNewNode(self.fireCollNode)

        render.setColorScale(0.65, 0.65, 0.65, 1.0)

        self.cameraSubmerged = 0
        self.toonSubmerged = 0
        taskMgr.add(self.__checkToonUnderwater, 'oz-check-toon-underwater')
        taskMgr.add(self.__checkCameraUnderwater, 'oz-check-cam-underwater')

        self.accept('enterouch', self.startFire)
        self.accept('exitouch', self.stopFire)

    def exit(self, visibilityFlag = 1):
        Street.Street.exit(self, visibilityFlag)

        messenger.send('exitSafeZone')

        self.campfire.cleanup()

        del self.fireCollSphere
        del self.fireCollNode
        self.fireCollNodePath.removeNode()

        render.setColorScale(1.0, 1.0, 1.0, 1.0)

        taskMgr.remove('oz-check-toon-underwater')
        taskMgr.remove('oz-check-cam-underwater')
        self.loader.hood.setNoFog()

        taskMgr.remove('fire-tick')
        self.ignore('enterouch')
        self.ignore('exitouch')

    def __fireTick(self, task):
        base.localAvatar.b_squish(5, True)
        task.delayTime = 1.0
        return task.again

    def startFire(self, collision):
        taskMgr.add(self.__fireTick, 'fire-tick')

    def stopFire(self, collision):
        taskMgr.remove('fire-tick')

    def __checkCameraUnderwater(self, task):
        if camera.getZ(render) < self.waterLevel:
            self.__submergeCamera()
        else:
            self.__emergeCamera()
        return Task.cont

    def __checkToonUnderwater(self, task):
        if base.localAvatar.getZ() < -2.90:
            self.__submergeToon()
        else:
            self.__emergeToon()
        return Task.cont

    def __submergeCamera(self):
        if self.cameraSubmerged == 1:
            return
        self.loader.hood.setUnderwaterFog()
        base.playSfx(self.underwaterSound, looping=1, volume=0.8)
        self.cameraSubmerged = 1
        self.walkStateData.setSwimSoundAudible(1)

    def __emergeCamera(self):
        if self.cameraSubmerged == 0:
            return
        self.loader.hood.setNoFog()
        self.underwaterSound.stop()
        self.cameraSubmerged = 0
        self.walkStateData.setSwimSoundAudible(0)

    def __submergeToon(self):
        if self.toonSubmerged == 1:
            return
        base.playSfx(self.submergeSound)
        if base.config.GetBool('disable-flying-glitch') == 0:
            self.fsm.request('walk')
        self.walkStateData.fsm.request('swimming', [self.swimSound])
        pos = base.localAvatar.getPos(render)
        base.localAvatar.d_playSplashEffect(pos[0], pos[1], self.waterLevel)
        self.toonSubmerged = 1

    def __emergeToon(self):
        if self.toonSubmerged == 0:
            return
        self.walkStateData.fsm.request('walking')
        self.toonSubmerged = 0

    def createPicnic(self, picnicBasket):
        self.accept(self.picnicBasketDoneEvent, self.handlePicnicBasketDone)
        place = base.cr.playGame.getPlace()

        if not hasattr(place, 'picnic') or not place.picnic:
            place.picnic = PicnicBasket.PicnicBasket(place, place.fsm, self.picnicBasketDoneEvent,
                                                     picnicBasket.getDoId(), picnicBasket.seatNumber)
            place.picnic.load()
            place.picnic.enter()

    def enterPicnicBasketBlock(self, picnicBasket):
        taskMgr.remove('oz-check-toon-underwater')
        taskMgr.remove('oz-check-cam-underwater')

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

        taskMgr.add(self.__checkToonUnderwater, 'oz-check-toon-underwater')
        taskMgr.add(self.__checkCameraUnderwater, 'oz-check-cam-underwater')

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
