"""MakeAToon module: contains the MakeAToon class"""

from panda3d.core import *
from direct.fsm import ClassicFSM, State
from direct.fsm import StateData
from toontown.toonbase import ToontownGlobals
from direct.gui.DirectGui import *
from toontown.toonbase import TTLocalizer
from toontown.makeatoon.MakeAToonGlobals import *
from direct.interval.IntervalGlobal import *
from direct.directnotify import DirectNotifyGlobal
from . import GenderShop
from . import BodyShop
from . import ClothesShop
import random

MATCamFoolsHeight = ToontownGlobals.MakeAToonCameraDefaultHeight + 1


class MakeAToon(StateData.StateData):
    """MakeAToon class"""

    # special methods
    notify = DirectNotifyGlobal.directNotify.newCategory('MakeAToon')

    def __init__(self, parentFSM, avList, doneEvent, index):
        """
        MakeAToon constructor: create a toon and let the guest customize it
        """
        StateData.StateData.__init__(self, doneEvent)
        # download phase
        self.phase = 3

        self.dnastring = None
        self.dna = None
        self.progressing = 0

        self.toonPosition = Point3(-5.7, 5.3501, 0)
        self.toonScale = Point3(1, 1, 1)
        self.toonHpr = Point3(-90, 0, 0)
        self.leftTime = 1.6
        self.rightTime = 1
        self.slide = 0

        self.fsm = ClassicFSM.ClassicFSM('MakeAToon', [State.State('Init', self.enterInit, self.exitInit, ['GenderShop']),
         State.State('GenderShop', self.enterGenderShop, self.exitGenderShop, ['BodyShop']),
         State.State('BodyShop', self.enterBodyShop, self.exitBodyShop, ['GenderShop', 'ClothesShop']),
         State.State('ClothesShop', self.enterClothesShop, self.exitClothesShop, ['BodyShop']),
         State.State('Done', self.enterDone, self.exitDone, [])], 'Init', 'Done')
        self.parentFSM = parentFSM
        self.parentFSM.getStateNamed('createAvatar').addChild(self.fsm)

        # create the shops
        self.gs = GenderShop.GenderShop(self, 'GenderShop-done')
        self.bs = BodyShop.BodyShop('BodyShop-done')
        self.cls = ClothesShop.ClothesShop(self, 'ClothesShop-done', avList, index)
        self.shop = GENDERSHOP
        self.shopsVisited = []

        # sound
        self.music = None
        self.soundBack = None

        self.fsm.enterInitialState()

        # Mouse control events
        # left click drag rotation
        self.accept('mouse1', self.beginMouseRotationTask)
        # scroll wheel zoom
        self.accept('wheel_up', lambda: self.adjustZoom(0.1))
        self.accept('wheel_down', lambda: self.adjustZoom(-0.1))

        # this is called when the toon is updated to adjust the camera
        self.accept('mat-toon-updated', self.updateCamera)

        self.hprDelta = -1
        self.dropIval = None
        self.roomSquishIval = None
        self.propSquishIval = None
        self.focusOutIval = None
        self.focusInIval = None
        self.toon = None
        self.zoomLevel = 0.0

    # accessors
    def getToon(self):
        return self.toon

    def enter(self):
        self.notify.debug('Starting Make A Toon.')
        base.cr.discordManager.setInfo(base.cr.discordManager.getState(), TTLocalizer.DiscordMakingAToon,
                                       ToontownGlobals.DefaultIcon, TTLocalizer.DiscordMakeAToon, None, None)
        if base.config.GetBool('want-qa-regression', 0):
            self.notify.info('QA-REGRESSION: MAKEATOON: Starting Make A Toon')
        base.cr.centralLogger.writeClientEvent('MAT - startingMakeAToon')
        base.camLens.setMinFov(ToontownGlobals.MakeAToonCameraFarFov)
        base.playMusic(self.music, looping=1, volume=self.musicVolume)
        camera.setPosHpr(10.7, 5.3501, MATCamFoolsHeight, 90, 2.73, 0)
        self.guiTopBar.show()
        self.guiBottomBar.show()
        self.guiCancelButton.show()
        self.fsm.request('GenderShop')

    def exit(self):
        base.camLens.setMinFov(ToontownGlobals.DefaultCameraFov / (4. / 3.))
        self.guiTopBar.hide()
        self.guiBottomBar.hide()
        self.guiCheckButton.hide()
        self.guiCancelButton.hide()
        self.guiNextButton.hide()
        self.guiLastButton.hide()
        self.music.stop()
        self.fsm.request('Done')
        self.room.reparentTo(hidden)
        camera.reparentTo(render)

    def load(self):
        gui = loader.loadModel('phase_3/models/gui/tt_m_gui_mat_mainGui')
        guiAcceptUp = gui.find('**/tt_t_gui_mat_okUp')
        guiAcceptDown = gui.find('**/tt_t_gui_mat_okDown')
        guiCancelUp = gui.find('**/tt_t_gui_mat_closeUp')
        guiCancelDown = gui.find('**/tt_t_gui_mat_closeDown')
        guiNextUp = gui.find('**/tt_t_gui_mat_nextUp')
        guiNextDown = gui.find('**/tt_t_gui_mat_nextDown')
        guiNextDisabled = gui.find('**/tt_t_gui_mat_nextDisabled')
        rotateUp = gui.find('**/tt_t_gui_mat_arrowRotateUp')
        rotateDown = gui.find('**/tt_t_gui_mat_arrowRotateDown')
        self.guiTopBar = DirectFrame(relief=None, text=TTLocalizer.CreateYourToon, text_font=ToontownGlobals.getSuitFont(),
                                     text_fg=(1.0, 1.0, 1.0, 1.0), text_shadow=(0.0, 0.0, 0.0, 1.0), text_scale=0.18, text_pos=(0, -0.03), pos=(0, 0, 0.86))
        self.guiTopBar.hide()
        self.guiBottomBar = DirectFrame(relief=None, image_scale=(1.25, 1, 1), pos=(0.01, 0, -0.86))
        self.guiBottomBar.hide()

        self.guiCheckButton = DirectButton(parent=base.a2dBottomRight, relief=None, image=(guiAcceptUp, guiAcceptDown, guiAcceptUp, guiAcceptDown), image_scale=halfButtonScale,
                                           image1_scale=halfButtonHoverScale, image2_scale=halfButtonHoverScale, pos=(-0.158333, 0, 0.122), command=self.__handleNext,
                                           text=('', TTLocalizer.MakeAToonDone, TTLocalizer.MakeAToonDone), text_font=ToontownGlobals.getSuitFont(), text_scale=0.08,
                                           text_align=TextNode.ARight, text_pos=(0.13, 0.13), text_fg=(1, 1, 1, 1), text_shadow=(0, 0, 0, 1))
        self.guiCheckButton.hide()

        self.guiCancelButton = DirectButton(parent=base.a2dBottomLeft, relief=None, image=(guiCancelUp, guiCancelDown, guiCancelUp, guiCancelDown), image_scale=halfButtonScale,
                                            image1_scale=halfButtonHoverScale, image2_scale=halfButtonHoverScale, pos=(0.164333, 0, 0.129), command=self.__handleCancel,
                                            text=('', TTLocalizer.MakeAToonCancel, TTLocalizer.MakeAToonCancel), text_font=ToontownGlobals.getSuitFont(),
                                            text_scale=TTLocalizer.MATguiCancelButton, text_pos=(0, 0.115), text_fg=(1, 1, 1, 1), text_shadow=(0, 0, 0, 1))
        self.guiCancelButton.hide()

        self.guiNextButton = DirectButton(parent=base.a2dBottomRight, relief=None, image=(guiNextUp, guiNextDown, guiNextUp, guiNextDisabled), image_scale=(0.3, 0.3, 0.3),
                                          image1_scale=(0.35, 0.35, 0.35), image2_scale=(0.35, 0.35, 0.35), pos=(-0.158333, 0, 0.122), command=self.__handleNext,
                                          text=('', TTLocalizer.MakeAToonNext, TTLocalizer.MakeAToonNext, ''), text_font=ToontownGlobals.getSuitFont(),
                                          text_scale=TTLocalizer.MATguiNextButton, text_pos=(0, 0.115), text_fg=(1, 1, 1, 1), text_shadow=(0, 0, 0, 1))
        self.guiNextButton.hide()

        self.guiLastButton = DirectButton(parent=base.a2dBottomRight, relief=None, image=(guiNextUp,
         guiNextDown,
         guiNextUp,
         guiNextDown), image3_color=Vec4(0.5, 0.5, 0.5, 0.75), image_scale=(-0.3, 0.3, 0.3), image1_scale=(-0.35, 0.35, 0.35), image2_scale=(-0.35, 0.35, 0.35), pos=(-0.498333, 0, 0.122), command=self.__handleLast, text=('',
         TTLocalizer.MakeAToonLast,
         TTLocalizer.MakeAToonLast,
         ''), text_font=ToontownGlobals.getSuitFont(), text_scale=0.08, text_pos=(0, 0.115), text_fg=(1, 1, 1, 1), text_shadow=(0, 0, 0, 1))
        self.guiLastButton.hide()

        self.rotateLeftButton = DirectButton(parent=self.guiBottomBar, relief=None, image=(rotateUp,
         rotateDown,
         rotateUp,
         rotateDown), image_scale=(-0.4, 0.4, 0.4), image1_scale=(-0.5, 0.5, 0.5), image2_scale=(-0.5, 0.5, 0.5), pos=ToontownGlobals.MakeAToonRotArrowPos[0][0])
        self.rotateLeftButton.hide()
        self.rotateLeftButton.bind(DGG.B1PRESS, self.rotateToonLeft)
        self.rotateLeftButton.bind(DGG.B1RELEASE, self.stopToonRotateLeftTask)

        self.rotateRightButton = DirectButton(parent=self.guiBottomBar, relief=None, image=(rotateUp,
         rotateDown,
         rotateUp,
         rotateDown), image_scale=(0.4, 0.4, 0.4), image1_scale=(0.5, 0.5, 0.5), image2_scale=(0.5, 0.5, 0.5), pos=ToontownGlobals.MakeAToonRotArrowPos[1][0])
        self.rotateRightButton.hide()
        self.rotateRightButton.bind(DGG.B1PRESS, self.rotateToonRight)
        self.rotateRightButton.bind(DGG.B1RELEASE, self.stopToonRotateRightTask)

        gui.removeNode()

        ee = DirectFrame(pos=(-1, 1, 1), frameSize=(-.01, 0.01, -.01, 0.01), frameColor=(0, 0, 0, 0.05), state='normal')
        ee.bind(DGG.B1PRESS, lambda x, ee = ee: self.toggleSlide())
        self.eee = ee

        self.room = loader.loadModel('phase_9/models/cogHQ/SelbotLegFactory')

        self.background = self.room.find('**/ZONE15')
        self.background.reparentTo(render)
        camera.reparentTo(self.background)

        smokeSeqNode = SequenceNode('smoke')
        smokeModel = loader.loadModel('phase_3/models/makeatoon/tt_m_ara_mat_smoke')
        smokeFrameList = list(smokeModel.findAllMatches('**/smoke_*'))
        smokeFrameList.reverse()
        for smokeFrame in smokeFrameList:
            smokeSeqNode.addChild(smokeFrame.node())
        smokeSeqNode.setFrameRate(12)
        self.smoke = render.attachNewNode(smokeSeqNode)
        self.smoke.setScale(1, 1, 0.75)
        self.smoke.hide()
        self.gs.load()
        self.bs.load()
        self.cls.load()
        self.music = base.loader.loadMusic('phase_9/audio/bgm/CHQ_FACT_bg.ogg')
        self.musicVolume = base.config.GetFloat('makeatoon-music-volume', 1)
        self.sfxVolume = base.config.GetFloat('makeatoon-sfx-volume', 1)
        # TODO: Use the sounds another time if this is revisited - I was thinking maybe a smoke effect
        #  where steam appears for the transitions and it makes a hiss or whistling sound (maybe also could use
        #  the unused body shop sound)
        self.soundBack = base.loader.loadSfx('phase_3/audio/sfx/GUI_create_toon_back.ogg')
        self.crashSounds = []
        self.crashSounds.append(base.loader.loadSfx('phase_3/audio/sfx/tt_s_ara_mat_crash_boing.ogg'))
        self.crashSounds.append(base.loader.loadSfx('phase_3/audio/sfx/tt_s_ara_mat_crash_glassBoing.ogg'))
        self.crashSounds.append(base.loader.loadSfx('phase_3/audio/sfx/tt_s_ara_mat_crash_wood.ogg'))
        self.crashSounds.append(base.loader.loadSfx('phase_3/audio/sfx/tt_s_ara_mat_crash_woodBoing.ogg'))
        self.crashSounds.append(base.loader.loadSfx('phase_3/audio/sfx/tt_s_ara_mat_crash_woodGlass.ogg'))
        return

    def unload(self):
        self.exit()

        self.gs.unload()
        self.bs.unload()
        self.cls.unload()

        del self.gs
        del self.bs
        del self.cls

        self.guiTopBar.destroy()
        self.guiBottomBar.destroy()
        self.guiCancelButton.destroy()
        self.guiCheckButton.destroy()
        self.eee.destroy()
        self.guiNextButton.destroy()
        self.guiLastButton.destroy()
        self.rotateLeftButton.destroy()
        self.rotateRightButton.destroy()

        del self.guiTopBar
        del self.guiBottomBar
        del self.guiCancelButton
        del self.guiCheckButton
        del self.eee
        del self.guiNextButton
        del self.guiLastButton
        del self.rotateLeftButton
        del self.rotateRightButton
        del self.dnastring
        del self.music
        del self.soundBack
        del self.dna

        if self.toon:
            self.toon.delete()

        del self.toon

        self.cleanupDropIval()
        self.cleanupRoomSquishIval()
        self.cleanupPropSquishIval()
        self.cleanupFocusInIval()
        self.cleanupFocusOutIval()

        self.room.removeNode()
        del self.room

        self.background.removeNode()
        del self.background

        self.smoke.removeNode()
        del self.smoke

        while len(self.crashSounds):
            del self.crashSounds[0]

        self.parentFSM.getStateNamed('createAvatar').removeChild(self.fsm)
        del self.parentFSM
        del self.fsm

        self.ignoreAll()

        loader.unloadModel('phase_3/models/gui/create_a_toon_gui')
        loader.unloadModel('phase_3/models/gui/create_a_toon')
        ModelPool.garbageCollect()
        TexturePool.garbageCollect()

    def getDNA(self):
        return self.dnastring

    def __handleBodyShop(self):
        self.fsm.request('BodyShop')

    def __handleClothesShop(self):
        self.fsm.request('ClothesShop')

    def __handleCancel(self):
        self.doneStatus = 'cancel'
        self.shopsVisited = []
        # Idk why but the fade effect isn't being cleared by itself so we'll have to do it manually
        base.transitions.fadeOut(finishIval=Sequence(EventInterval(self.doneEvent), Func(base.transitions.noFade)))

    def toggleSlide(self):
        self.slide = 1 - self.slide

    def goToNextShop(self):
        self.progressing = 1
        # go to the next shop
        if self.shop == GENDERSHOP:
            self.fsm.request('BodyShop')
        elif self.shop == BODYSHOP:
            self.fsm.request('ClothesShop')

    def goToLastShop(self):
        self.progressing = 0
        # go to the last shop
        if self.shop == BODYSHOP:
            self.fsm.request('GenderShop')
        elif self.shop == CLOTHESSHOP:
            self.fsm.request('BodyShop')
        else:
            self.fsm.request('ClothesShop')

    # Specific State functions

    def enterInit(self):
        pass

    def exitInit(self):
        pass

    ##### GenderShop state #####

    def enterGenderShop(self):
        base.cr.centralLogger.writeClientEvent('MAT - enteringGenderShop')
        self.shop = GENDERSHOP
        if GENDERSHOP not in self.shopsVisited:
            self.shopsVisited.append(GENDERSHOP)
            self.guiNextButton['state'] = DGG.DISABLED
        self.guiTopBar['text'] = TTLocalizer.CreateYourToonTitleFools
        self.guiTopBar['text_fg'] = (1.0, 1.0, 1.0, 1.0)
        self.guiTopBar['text_scale'] = TTLocalizer.MATenterGenderShop
        base.transitions.fadeIn()
        self.accept('GenderShop-done', self.__handleGenderShopDone)
        self.gs.enter()
        self.guiNextButton.show()
        self.gs.showButtons()
        self.rotateLeftButton.hide()
        self.rotateRightButton.hide()

    def exitGenderShop(self):
        self.gs.exit()
        self.ignore('GenderShop-done')

    def __handleGenderShopDone(self):
        self.guiNextButton.hide()
        self.gs.hideButtons()
        self.goToNextShop()

    ##### BodyShop state #####

    def bodyShopOpening(self):
        self.bs.showButtons()
        self.guiNextButton.show()
        self.guiLastButton.show()
        self.rotateLeftButton.show()
        self.rotateRightButton.show()

    def enterBodyShop(self):
        base.cr.centralLogger.writeClientEvent('MAT - enteringBodyShop')
        self.toon.show()
        self.shop = BODYSHOP
        self.guiTopBar['text'] = TTLocalizer.ShapeYourToonTitle
        self.guiTopBar['text_fg'] = (1.0, 1.0, 1.0, 1.0)
        self.guiTopBar['text_scale'] = TTLocalizer.MATenterBodyShop
        self.accept('BodyShop-done', self.__handleBodyShopDone)
        self.bs.enter(self.toon)
        if BODYSHOP not in self.shopsVisited:
            self.shopsVisited.append(BODYSHOP)
        self.bodyShopOpening()

    def exitBodyShop(self):
        self.bs.exit()
        self.ignore('BodyShop-done')

    def __handleBodyShopDone(self):
        self.guiNextButton.hide()
        self.guiLastButton.hide()
        if self.bs.doneStatus == 'next':
            self.bs.hideButtons()
            self.goToNextShop()
        else:
            self.bs.hideButtons()
            self.goToLastShop()

    ##### ClothesShop state #####

    def clothesShopOpening(self):
        self.guiCheckButton.show()
        self.guiLastButton.show()
        self.cls.showButtons()
        self.rotateLeftButton.show()
        self.rotateRightButton.show()

    def enterClothesShop(self):
        base.cr.centralLogger.writeClientEvent('MAT - enteringClothesShop')
        self.shop = CLOTHESSHOP
        self.guiTopBar['text'] = TTLocalizer.PickClothesTitle
        self.guiTopBar['text_fg'] = (1.0, 1.0, 1.0, 1.0)
        self.guiTopBar['text_scale'] = TTLocalizer.MATenterClothesShop
        self.accept('ClothesShop-done', self.__handleClothesShopDone)
        self.toon.setScale(self.toonScale)
        self.toon.setPos(self.toonPosition)
        if not self.progressing:
            self.toon.setHpr(self.toonHpr)
        self.clothesShopOpening()
        self.cls.enter(self.toon)
        if CLOTHESSHOP not in self.shopsVisited:
            self.shopsVisited.append(CLOTHESSHOP)

    def exitClothesShop(self):
        self.cls.exit()
        self.ignore('ClothesShop-done')

    def __handleClothesShopDone(self):
        if base.config.GetBool('want-qa-regression', 0):
            self.notify.info('QA-REGRESSION: MAKEATOON: Creating A Toon')
        self.guiLastButton.hide()
        self.guiCheckButton.hide()
        if self.cls.getDoneStatus() == 'last':
            self.cls.hideButtons()
            self.goToLastShop()
        else:
            self.doneStatus = 'created'
            base.transitions.fadeOut(finishIval=EventInterval(self.doneEvent))

    def __handleNext(self):
        messenger.send('next')

    def __handleLast(self):
        messenger.send('last')

    def __handleSkipTutorial(self):
        messenger.send('skipTutorial')

     ##### Done state #####

    def enterDone(self):
        pass

    def exitDone(self):
        pass

    def create3DGui(self):
        self.proto = loader.loadModel('phase_3/models/makeatoon/tt_m_ara_mat_protoMachine')
        self.proto.setScale(0.2)
        self.proto.reparentTo(render)

    def setup3DPicker(self):
        self.accept('mouse1', self.mouseDown)
        self.accept('mouse1-up', self.mouseUp)
        self.pickerQueue = CollisionHandlerQueue()
        self.pickerTrav = CollisionTraverser('MousePickerTraverser')
        self.pickerTrav.setRespectPrevTransform(True)
        self.pickerNode = CollisionNode('mouseRay')
        self.pickerNP = camera.attachNewNode(self.pickerNode)
        self.pickerNode.setFromCollideMask(GeomNode.getDefaultCollideMask())
        self.pickerRay = CollisionRay()
        self.pickerNode.addSolid(self.pickerRay)
        self.pickerTrav.addCollider(self.pickerNP, self.pickerQueue)

    def mouseDown(self):
        self.notify.debug('Mouse 1 Down')
        mpos = base.mouseWatcherNode.getMouse()
        self.pickerRay.setFromLens(base.camNode, mpos.getX(), mpos.getY())
        self.pickerTrav.traverse(render)
        if self.pickerQueue.getNumEntries() > 0:
            self.pickerQueue.sortEntries()
            self.pickedObj = self.pickerQueue.getEntry(0).getIntoNodePath()

    def mouseUp(self):
        self.notify.debug('Mouse 1 Up')

    def startFocusOutIval(self):
        if self.focusInIval.isPlaying():
            self.focusInIval.pause()

    def startFocusInIval(self):
        if self.focusOutIval.isPlaying():
            self.focusOutIval.pause()

    def cleanupFocusOutIval(self):
        if self.focusOutIval:
            self.focusOutIval.finish()
            del self.focusOutIval

    def cleanupFocusInIval(self):
        if self.focusInIval:
            self.focusInIval.finish()
            del self.focusInIval

    def cleanupDropIval(self):
        if self.dropIval:
            self.dropIval.finish()
            del self.dropIval

    def cleanupRoomSquishIval(self):
        if self.roomSquishIval:
            self.roomSquishIval.finish()
            del self.roomSquishIval

    def cleanupPropSquishIval(self):
        if self.propSquishIval:
            self.propSquishIval.finish()
            del self.propSquishIval

    def setToon(self, toon):
        self.toon = toon

    def setNextButtonState(self, state):
        self.guiNextButton['state'] = state

    def playRandomCrashSound(self):
        index = random.randint(0, len(self.crashSounds) - 1)
        base.playSfx(self.crashSounds[index], volume=self.sfxVolume)

    def rotateToonLeft(self, event):
        taskMgr.add(self.rotateToonLeftTask, 'rotateToonLeftTask')

    def rotateToonLeftTask(self, task):
        self.toon.setH(self.toon.getH() + self.hprDelta)
        return task.cont

    def stopToonRotateLeftTask(self, event):
        taskMgr.remove('rotateToonLeftTask')

    def rotateToonRight(self, event):
        taskMgr.add(self.rotateToonRightTask, 'rotateToonRightTask')

    def rotateToonRightTask(self, task):
        self.toon.setH(self.toon.getH() - self.hprDelta)
        return task.cont

    def stopToonRotateRightTask(self, event):
        taskMgr.remove('rotateToonRightTask')

    ''' Mouse Controls '''

    # Mouse Rotation
    async def beginMouseRotationTask(self):
        if not base.mouseWatcherNode.hasMouse() or not self.toon:
            return
        mx = base.mouseWatcherNode.getMouseX()

        self.lastFrameMouse = mx

        taskMgr.add(self.rotationTask, 'mouseRotationTask')
        await messenger.future('mouse1-up')
        taskMgr.remove('mouseRotationTask')

    def rotationTask(self, task):
        """
        Calculates how far the mouse has traveled since
        the last frame, and rotates the toon respectively
        """

        if not base.mouseWatcherNode.hasMouse():
            return task.cont
        mx = base.mouseWatcherNode.getMouseX()

        # calculate how far the mouse has traveled since last frame
        delta = (self.lastFrameMouse - mx) * 120  # < - change this value to make it faster or slower

        self.toon.setH(self.toon.getH() - delta)

        # save this as this frame's position
        self.lastFrameMouse = mx

        return task.cont

    # Camera Zoom - Scroll Up/Down, zooms into the characters face
    def adjustZoom(self, delta):
        """ Adjusts zoom level """
        self.zoomLevel = bound(self.zoomLevel + delta, 0, 1)
        self.updateCamera()

    def updateCamera(self):
        """ Zoom into the character's face """
        if self.toon:
            # adjust camera
            height = lerp(MATCamFoolsHeight,
                          self.toon.getHeight() + ToontownGlobals.MakeAToonCameraHeightOffset,
                          self.zoomLevel)
            fov = lerp(ToontownGlobals.MakeAToonCameraFarFov,
                       ToontownGlobals.MakeAToonCameraCloseFov,
                       self.zoomLevel)
            # smoothly lerp to the new position
            base.camera.posInterval(0.1, Point3(base.camera.getX(), base.camera.getY(), height),
                                    blendType = 'easeInOut').start()
            LerpFunctionInterval(base.camLens.setMinFov, 0.1, base.camLens.getMinFov(), fov,
                                 blendType = 'easeInOut').start()

            # adjust rotation button positions
            # left x
            leftX = lerp(ToontownGlobals.MakeAToonRotArrowPos[0][0][0], ToontownGlobals.MakeAToonRotArrowPos[0][1][0],
                      self.zoomLevel)

            # right x
            rightX = lerp(ToontownGlobals.MakeAToonRotArrowPos[1][0][0], ToontownGlobals.MakeAToonRotArrowPos[1][1][0],
                      self.zoomLevel)

            # the y is the same on both - it goes slightly down when zoomed in
            y = lerp(ToontownGlobals.MakeAToonRotArrowPos[0][0][2], ToontownGlobals.MakeAToonRotArrowPos[0][1][2],
                     self.zoomLevel)

            self.rotateLeftButton.posInterval(0.1, Point3(leftX, 0, y), blendType = 'easeInOut').start()
            self.rotateRightButton.posInterval(0.1, Point3(rightX, 0, y), blendType = 'easeInOut').start()
