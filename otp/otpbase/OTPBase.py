import builtins
import math
import re
import time
from direct.showbase import SfxPlayer
from panda3d.core import Camera, TPLow, VBase4, ColorWriteAttrib, Filename, getModelPath, NodePath, AudioManager
from typing import Optional

from direct.showbase.ShowBase import ShowBase
from direct.task.TaskManagerGlobal import taskMgr

from toontown.toonbase import ClientSettings
from . import OTPRender


class OTPBase(ShowBase):

    def __init__(self, windowType = None):
        self.wantEnviroDR = False

        self.sfxMgrMaster: Optional[AudioManager] = None
        self.sfxMgrDialog: Optional[AudioManager] = None
        self.sfxMgrEnvironment: Optional[AudioManager] = None
        self.sfxMgrGui: Optional[AudioManager] = None
        self.sfxMgrBattle: Optional[AudioManager] = None
        self.sfxMgrStreetProps: Optional[AudioManager] = None
        ShowBase.__init__(self, windowType=windowType)
        if config.GetBool('want-phase-checker', 0):
            from direct.showbase import Loader
            Loader.phaseChecker = self.loaderPhaseChecker
            self.errorAccumulatorBuffer = ''
            taskMgr.add(self.delayedErrorCheck, 'delayedErrorCheck', priority=10000)
        self.idTags = config.GetBool('want-id-tags', 0)
        if not self.idTags:
            del self.idTags
        self.wantNametags = self.config.GetBool('want-nametags', 1)
        self.slowCloseShard = self.config.GetBool('slow-close-shard', 0)
        self.slowCloseShardDelay = self.config.GetFloat('slow-close-shard-delay', 10.0)
        self.fillShardsToIdealPop = self.config.GetBool('fill-shards-to-ideal-pop', 1)
        self.logPrivateInfo = self.config.GetBool('log-private-info', __dev__)
        self.wantDynamicShadows = 1
        self.stereoEnabled = False
        self.enviroDR = None
        self.enviroCam = None
        self.pixelZoomSetup = False
        self.gameOptionsCode = ''
        self.locationCode = ''
        self.locationCodeChanged = time.time()

        if self.cam:
            if self.wantEnviroDR:
                self.cam.node().setCameraMask(OTPRender.MainCameraBitmask)
            else:
                self.cam.node().setCameraMask(OTPRender.MainCameraBitmask | OTPRender.EnviroCameraBitmask)
        if ClientSettings.ThreadedNetwork.get():
            self.setTaskChainNetThreaded()
        else:
            self.setTaskChainNetNonthreaded()

    def setTaskChainNetThreaded(self):
        taskMgr.setupTaskChain('net', numThreads=1, frameBudget=0.001, threadPriority=TPLow)

    def setTaskChainNetNonthreaded(self):
        taskMgr.setupTaskChain('net', numThreads=0, frameBudget=-1)

    def toggleStereo(self):
        self.stereoEnabled = not self.stereoEnabled
        if self.stereoEnabled:
            if not self.win.isStereo():
                self.win.setRedBlueStereo(True, ColorWriteAttrib.CRed, ColorWriteAttrib.CGreen | ColorWriteAttrib.CBlue)
        if self.wantEnviroDR:
            self.setupEnviroCamera()
            return
        mainDR = self.camNode.getDisplayRegion(0)
        if self.stereoEnabled:
            if not mainDR.isStereo():
                self.win.removeDisplayRegion(mainDR)
                mainDR = self.win.makeStereoDisplayRegion()
                mainDR.getRightEye().setClearDepthActive(True)
                mainDR.setCamera(self.cam)
        elif mainDR.isStereo():
            self.win.removeDisplayRegion(mainDR)
            mainDR = self.win.makeMonoDisplayRegion()
            mainDR.setCamera(self.cam)

    def setupEnviroCamera(self):
        clearColor = VBase4(0, 0, 0, 1)
        if self.enviroDR:
            clearColor = self.enviroDR.getClearColor()
            self.win.removeDisplayRegion(self.enviroDR)
        if not self.enviroCam:
            self.enviroCam = self.cam.attachNewNode(Camera('enviroCam'))
        mainDR = self.camNode.getDisplayRegion(0)
        if self.stereoEnabled:
            self.enviroDR = self.win.makeStereoDisplayRegion()
            if not mainDR.isStereo():
                self.win.removeDisplayRegion(mainDR)
                mainDR = self.win.makeStereoDisplayRegion()
                mainDR.setCamera(self.cam)
            ml = mainDR.getLeftEye()
            mr = mainDR.getRightEye()
            el = self.enviroDR.getLeftEye()
            er = self.enviroDR.getRightEye()
            el.setSort(-8)
            ml.setSort(-6)
            er.setSort(-4)
            er.setClearDepthActive(True)
            mr.setSort(-2)
            mr.setClearDepthActive(False)
        else:
            self.enviroDR = self.win.makeMonoDisplayRegion()
            if mainDR.isStereo():
                self.win.removeDisplayRegion(mainDR)
                mainDR = self.win.makeMonoDisplayRegion()
                mainDR.setCamera(self.cam)
            self.enviroDR.setSort(-10)
        self.enviroDR.setClearColor(clearColor)
        self.win.setClearColor(clearColor)
        self.enviroDR.setCamera(self.enviroCam)
        self.enviroCamNode = self.enviroCam.node()
        self.enviroCamNode.setLens(self.cam.node().getLens())
        self.enviroCamNode.setCameraMask(OTPRender.EnviroCameraBitmask)
        render.hide(OTPRender.EnviroCameraBitmask)
        self.camList.append(self.enviroCam)
        self.backgroundDrawable = self.enviroDR
        self.enviroDR.setTextureReloadPriority(-10)
        if self.pixelZoomSetup:
            self.setupAutoPixelZoom()

    def setupAutoPixelZoom(self):
        self.win.setPixelZoom(1)
        self.enviroDR.setPixelZoom(1)
        if not self.stereoEnabled:
            self.enviroDR.setClearColorActive(True)
            self.enviroDR.setClearDepthActive(True)
            self.win.setClearColorActive(False)
            self.win.setClearDepthActive(False)
            self.backgroundDrawable = self.enviroDR
        else:
            self.enviroDR.setClearColorActive(False)
            self.enviroDR.setClearDepthActive(False)
            self.enviroDR.getRightEye().setClearDepthActive(True)
            self.win.setClearColorActive(True)
            self.win.setClearDepthActive(True)
            self.backgroundDrawable = self.win
        self.pixelZoomSetup = True
        self.targetPixelZoom = 1.0
        self.pixelZoomTask = None
        self.pixelZoomCamHistory = 2.0
        self.pixelZoomCamMovedList = []
        self.pixelZoomStarted = None
        flag = self.config.GetBool('enable-pixel-zoom', True)
        self.enablePixelZoom(flag)
        return

    def enablePixelZoom(self, flag):
        if not self.backgroundDrawable.supportsPixelZoom():
            flag = False
        self.pixelZoomEnabled = flag
        taskMgr.remove('chasePixelZoom')
        if flag:
            taskMgr.add(self.__chasePixelZoom, 'chasePixelZoom', priority=-52)
        else:
            self.backgroundDrawable.setPixelZoom(1)

    def __chasePixelZoom(self, task):
        now = globalClock.getFrameTime()
        pos = self.cam.getNetTransform().getPos()
        prevPos = self.cam.getNetPrevTransform().getPos()
        d2 = (pos - prevPos).lengthSquared()
        if d2:
            d = math.sqrt(d2)
            self.pixelZoomCamMovedList.append((now, d))
        while self.pixelZoomCamMovedList and self.pixelZoomCamMovedList[0][0] < now - self.pixelZoomCamHistory:
            del self.pixelZoomCamMovedList[0]

        dist = sum([pair[1] for pair in self.pixelZoomCamMovedList])
        speed = dist / self.pixelZoomCamHistory
        if speed < 5:
            self.backgroundDrawable.setPixelZoom(4)
            self.pixelZoomStart = None
        elif speed > 10:
            if self.pixelZoomStart == None:
                self.pixelZoomStart = now
            elapsed = now - self.pixelZoomStart
            if elapsed > 10:
                self.backgroundDrawable.setPixelZoom(16)
            elif elapsed > 5:
                self.backgroundDrawable.setPixelZoom(8)
        return task.cont

    def setLocationCode(self, locationCode):
        if locationCode != self.locationCode:
            self.locationCode = locationCode
            self.locationCodeChanged = time.time()

    def delayedErrorCheck(self, task):
        if self.errorAccumulatorBuffer:
            buffer = self.errorAccumulatorBuffer
            self.errorAccumulatorBuffer = ''
            self.notify.error('\nAccumulated Phase Errors!:\n %s' % buffer)
        return task.cont

    def loaderPhaseChecker(self, path, loaderOptions):
        if 'audio/' in path:
            return 1
        file = Filename(path)
        if not file.getExtension():
            file.setExtension('bam')
        mp = getModelPath()
        path = mp.findFile(file).cStr()
        if not path:
            return
        match = re.match('.*phase_([^/]+)/', path)
        if not match:
            if 'dmodels' in path:
                return
            else:
                self.errorAccumulatorBuffer += 'file not in phase (%s, %s)\n' % (file, path)
                return
        basePhase = float(match.groups()[0])
        if not launcher.getPhaseComplete(basePhase):
            self.errorAccumulatorBuffer += 'phase is not loaded for this model %s\n' % path
        model = loader.loader.loadSync(Filename(path), loaderOptions)
        if model:
            model = NodePath(model)
            for tex in model.findAllTextures():
                texPath = tex.getFullpath().cStr()
                match = re.match('.*phase_([^/]+)/', texPath)
                if match:
                    texPhase = float(match.groups()[0])
                    if texPhase > basePhase:
                        self.errorAccumulatorBuffer += 'texture phase is higher than the models (%s, %s)\n' % (path, texPath)

    def getRepository(self):
        return self.cr

    def openMainWindow(self, *args, **kw):
        result = ShowBase.openMainWindow(self, *args, **kw)
        if result:
            self.wantEnviroDR = not self.win.getGsg().isHardware() or config.GetBool('want-background-region', 1)
            self.backgroundDrawable = self.win
        return result

    def isMainWindowOpen(self):
        if self.win != None:
            return self.win.isValid()
        return 0

    def destroy(self):
        if hasattr(builtins, 'localServer') and localServer:
            localServer.killProcesses()

        ShowBase.destroy(self)

    def enableParticles(self):
        if not self.particleMgrEnabled:
            # Overriding this from ShowBase because we can't use import_module
            # in Pypperoni builds...

            if not self.particleMgr:
                from direct.particles import ParticleManagerGlobal as PMG
                self.particleMgr = PMG.particleMgr
                self.particleMgr.setFrameStepping(1)

            if not self.physicsMgr:
                from direct.showbase import PhysicsManagerGlobal as PMG
                from panda3d.physics import LinearEulerIntegrator
                self.physicsMgr = PMG.physicsMgr
                integrator = LinearEulerIntegrator()
                self.physicsMgr.attachLinearIntegrator(integrator)

            self.particleMgrEnabled = 1
            self.physicsMgrEnabled = 1
            self.taskMgr.remove('manager-update')
            self.taskMgr.add(self.updateManagers, 'manager-update')

    def SetAllSfxEnables(self, bEnabled):
        """Calls ``setActive(bEnabled)`` on all valid SFX managers."""
        # Override from ShowBase to add code to force all sounds to stop
        for i in range(len(self.sfxManagerList)):
            if self.sfxManagerIsValidList[i]:
                self.sfxManagerList[i].setActive(bEnabled)
                # Force all sounds to stop because there are cases
                # where sounds that started playing while the sfxManager
                # was disabled will not stop when they should.
                if bEnabled:
                    self.sfxManagerList[i].stopAllSounds()

    def createBaseAudioManagers(self):
        """
        Panda's default is to allow only 1 song at a time. stupid. change it to 3
        """
        self.sfxPlayer = SfxPlayer.SfxPlayer()
        self.sfxMgrMaster = AudioManager.createAudioManager()
        self.addSfxManager(self.sfxMgrMaster)

        self.sfxMgrDialog = AudioManager.createAudioManager()
        self.addSfxManager(self.sfxMgrDialog)

        self.sfxMgrEnvironment = AudioManager.createAudioManager()
        self.addSfxManager(self.sfxMgrEnvironment)

        self.sfxMgrGui = AudioManager.createAudioManager()
        self.addSfxManager(self.sfxMgrGui)

        self.sfxMgrBattle = AudioManager.createAudioManager()
        self.sfxMgrBattle.setCacheLimit(15)
        self.addSfxManager(self.sfxMgrBattle)

        self.sfxMgrStreetProps = AudioManager.createAudioManager()
        self.addSfxManager(self.sfxMgrStreetProps)

        self.musicManager = AudioManager.createAudioManager()
        self.musicManagerIsValid = self.musicManager is not None \
            and self.musicManager.isValid()
        if self.musicManagerIsValid:
            self.musicManager.setConcurrentSoundLimit(3)
            self.musicManager.setActive(self.musicActive)