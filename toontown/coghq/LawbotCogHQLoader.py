from direct.directnotify import DirectNotifyGlobal

from panda3d.core import Shader, Plane, Vec3, Point3, NodePath
from typing import Optional

from otp.otpbase import OTPRender
from . import CogHQLoader
from toontown.toonbase import ToontownGlobals, ClientSettings
from toontown.toon import Toon
from direct.fsm import State
from . import StageInterior
from . import LawbotHQExterior
from . import LawbotHQBossBattle
from . import LawbotOfficeExterior
from ..safezone.Reflection import Reflection
from ..toonbase.ToontownSettings import REFLECTION_RESOLUTIONS

aspectSF = 0.7227

class LawbotCogHQLoader(CogHQLoader.CogHQLoader):
    notify = DirectNotifyGlobal.directNotify.newCategory('LawbotCogHQLoader')

    def __init__(self, hood, parentFSMState, doneEvent):
        CogHQLoader.CogHQLoader.__init__(self, hood, parentFSMState, doneEvent)
        self.fsm.addState(State.State('stageInterior', self.enterStageInterior, self.exitStageInterior, ['quietZone', 'cogHQExterior']))
        self.fsm.addState(State.State('factoryExterior', self.enterFactoryExterior, self.exitFactoryExterior, ['quietZone', 'start', 'cogHQExterior']))
        for stateName in ['start', 'cogHQExterior', 'quietZone']:
            state = self.fsm.getStateNamed(stateName)
            state.addTransition('stageInterior')

        for stateName in ['quietZone', 'start']:
            state = self.fsm.getStateNamed(stateName)
            state.addTransition('factoryExterior')

        self.musicFile = {ToontownGlobals.LawbotHQ: 'phase_11/audio/bgm/LB_courtyard.ogg',
                          ToontownGlobals.LawbotLobby: 'phase_11/audio/bgm/ttrm_s_ara_bgm_lbhq_bosslobby.ogg',
                          ToontownGlobals.LawbotOfficeExt: 'phase_11/audio/bgm/ttrm_s_ara_bgm_lbhq_facilitylobby.ogg'}
        self.cogHQExteriorModelPath = 'phase_11/models/lawbotHQ/LawbotPlaza'
        self.factoryExteriorModelPath = 'phase_11/models/lawbotHQ/LB_DA_Lobby'
        self.cogHQLobbyModelPath = 'phase_11/models/lawbotHQ/LB_CH_Lobby'
        self.reflection: Optional[Reflection] = None
        self.geom = None
        return

    def load(self, zoneId):
        CogHQLoader.CogHQLoader.load(self, zoneId)
        Toon.loadSellbotHQAnims()

    def unloadPlaceGeom(self):
        if self.geom:
            self.geom.removeNode()
            self.geom = None
        if self.reflection:
            self.reflection.enable(False)
            self.reflection.delete()
            self.reflection = None
        CogHQLoader.CogHQLoader.unloadPlaceGeom(self)
        return

    def loadPlaceGeom(self, zoneId):
        self.notify.info('loadPlaceGeom: %s' % zoneId)
        zoneId = zoneId - zoneId % 100
        self.notify.debug('zoneId = %d ToontownGlobals.LawbotHQ=%d' % (zoneId, ToontownGlobals.LawbotHQ))
        if zoneId == ToontownGlobals.LawbotHQ:
            self.geom = loader.loadModel(self.cogHQExteriorModelPath)

            brLinkTunnel = self.geom.find('**/TunnelEntrance1')
            brLinkTunnel.setName('linktunnel_br_3326_DNARoot')
            reflRes = REFLECTION_RESOLUTIONS[ClientSettings.ReflectionQuality.get()]
            ug = self.geom.find('**/underground')
            if reflRes:
                self.reflection = Reflection('reflection', reflRes, reflRes, base.render, Plane(Vec3(0, 0, 1), Vec3(0, 0, -68.37)))
                # self.reflection.createCard('fixed', 20)
                self.reflection.enable(True)
                self.__setupReflection()
                ug.removeNode()
            else:
                ug.setBin('ground', -10)
        elif zoneId == ToontownGlobals.LawbotOfficeExt:
            self.geom = loader.loadModel(self.factoryExteriorModelPath)
            ug = self.geom.find('**/underground')
            ug.setBin('ground', -10)
        elif zoneId == ToontownGlobals.LawbotLobby:
            if base.config.GetBool('want-qa-regression', 0):
                self.notify.info('QA-REGRESSION: COGHQ: Visit LawbotLobby')
            self.notify.debug('cogHQLobbyModelPath = %s' % self.cogHQLobbyModelPath)
            self.geom = loader.loadModel(self.cogHQLobbyModelPath)
            ug = self.geom.find('**/underground')
            ug.setBin('ground', -10)
        else:
            self.notify.warning('loadPlaceGeom: unclassified zone %s' % zoneId)
        CogHQLoader.CogHQLoader.loadPlaceGeom(self, zoneId)

    def __setupReflection(self):
        floor: NodePath = self.geom.find('**/LB_PlazaGround')
        floor.setShader(Shader.load(Shader.SLGLSL,
                                    fragment = 'phase_11/shaders/ttrm_sha_ara_lbhq_floor.frag',
                                    vertex = 'phase_11/shaders/ttrm_sha_ara_lbhq_floor.vert'
                                    )
                        )
        floor.setShaderInput('refl_texture', self.reflection.reflectionTexture)
        OTPRender.renderReflection(True, self.geom, 'geom_refl', None)
        OTPRender.renderReflection(False, floor, 'geom_refl', None)

    def unload(self):
        CogHQLoader.CogHQLoader.unload(self)
        Toon.unloadSellbotHQAnims()

    def enterStageInterior(self, requestStatus):
        self.placeClass = StageInterior.StageInterior
        self.stageId = requestStatus['stageId']
        self.enterPlace(requestStatus)

    def exitStageInterior(self):
        self.exitPlace()
        self.placeClass = None
        return

    def getExteriorPlaceClass(self):
        self.notify.debug('getExteriorPlaceClass')
        return LawbotHQExterior.LawbotHQExterior

    def getBossPlaceClass(self):
        self.notify.debug('getBossPlaceClass')
        return LawbotHQBossBattle.LawbotHQBossBattle

    def enterFactoryExterior(self, requestStatus):
        self.placeClass = LawbotOfficeExterior.LawbotOfficeExterior
        self.enterPlace(requestStatus)
        self.hood.spawnTitleText(requestStatus['zoneId'])

    def exitFactoryExterior(self):
        taskMgr.remove('titleText')
        self.hood.hideTitleText()
        self.exitPlace()
        self.placeClass = None
        return

    def enterCogHQBossBattle(self, requestStatus):
        self.notify.debug('LawbotCogHQLoader.enterCogHQBossBattle')
        CogHQLoader.CogHQLoader.enterCogHQBossBattle(self, requestStatus)
        base.cr.forbidCheesyEffects(1)

    def exitCogHQBossBattle(self):
        self.notify.debug('LawbotCogHQLoader.exitCogHQBossBattle')
        CogHQLoader.CogHQLoader.exitCogHQBossBattle(self)
        base.cr.forbidCheesyEffects(0)
