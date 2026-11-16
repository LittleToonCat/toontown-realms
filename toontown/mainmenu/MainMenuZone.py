from direct.showbase.DirectObject import DirectObject
from panda3d.core import CSDefault, NodePath, VBase4, Vec3, Vec4, Fog
from panda3d.toontown import DNAStorage, loadDNAFile

from toontown.avatar import ToontownAvatarUtils
from toontown.battle import BattleParticles
from toontown.hood import SkyUtil
from toontown.hood.GenericAnimatedProp import GenericAnimatedProp
from toontown.hood.HydrantInteractiveProp import HydrantInteractiveProp
from toontown.hood.InteractiveAnimatedProp import InteractiveAnimatedProp
from toontown.hood.MailboxInteractiveProp import MailboxInteractiveProp
from toontown.hood.TrashcanInteractiveProp import TrashcanInteractiveProp
from toontown.toon.Toon import Toon
from toontown.toonbase import ToontownGlobals


class MainMenuZone(DirectObject):
    DNAStorage = DNAStorage()
    zone = '?'  # type: str
    storages = []  # type: list[str]
    skyModel = 'phase_3.5/models/props/TT_sky'  # type: str
    billboardColor = VBase4(1.0, 1.0, 1.0, 1.0)
    billboardPos = (
        Vec3(-2, 25, -5),
        Vec3(-15, 0, 0),
        Vec3(1.0),
    )
    char = {
        ToontownGlobals.HolidayNormal:     'mk',
        ToontownGlobals.HolidayHalloween:  'vmk',
        ToontownGlobals.HolidayWinter:     'mk',
        ToontownGlobals.HolidayAprilFools: 'mk'
    }

    def __init__(self):
        DirectObject.__init__(self)
        self.toons = []  # type: list[Toon]
        self.load()
        if self.zone == 'BR' or loader.loadingScreen.getActiveHoliday() == ToontownGlobals.HolidayWinter:
            self.snow = BattleParticles.loadParticleFile('ttoff_p_efx_launch_tbrSnow')
            self.snow.setPos(0, 40, 10)
            self.snowRender = self.geom.attachNewNode('snowRender')
            self.snowRender.setDepthWrite(0)
            self.snowRender.setBin('fixed', 1)
            self.snow.start(base.camera, self.snowRender)

            if self.zone != 'DD':
                self.fog = Fog('SnowMainMenuFog')
                self.fog.setColor(Vec4(0.8, 0.8, 0.8, 1))
                self.fog.setLinearRange(0.0, 400)
                self.geom.setFog(self.fog)
                self.sky.setFog(self.fog)
        else:
            self.snow = None
            self.fog = None

    def load(self):
        loadDNAFile(self.DNAStorage, 'phase_4/dna/ttrm_d_strg.dna', CSDefault, 1)

        for storage in self.storages:
            loadDNAFile(self.DNAStorage, storage, CSDefault, 1)
            base.loader.tick()

        np = loadDNAFile(self.DNAStorage, f'phase_3/dna/ttoff_d_launch_background{self.zone}.dna', CSDefault,
                         1)  # type: NodePath
        if np.getNumParents() == 1:
            self.geom = NodePath(np.getParent(0))
            self.geom.reparentTo(render)
        else:
            self.geom = render.attachNewNode(np)  # type: NodePath
        base.loader.tick()

        if loader.loadingScreen.getActiveHoliday() == ToontownGlobals.HolidayHalloween:
            self.geom.setColorScale(0.6, 0.6, 0.6, 1.0)

        # Hide the black parts in the doors
        doorHoles = self.geom.findAllMatches('**/doorFrameHole*')
        for hole in doorHoles:
            hole.removeNode()

        self.sky = loader.loadModel(self.skyModel)  # type: NodePath
        self.sky.reparentTo(render)
        if loader.loadingScreen.getActiveHoliday() == 0:
            self.startCloudSky()

        if loader.loadingScreen.getActiveHoliday() in [ToontownGlobals.HolidayHalloween, ToontownGlobals.HolidayWinter]:
            lights = self.geom.findAllMatches('**/*light*')
            lights += self.geom.findAllMatches('**/*lamp*')
            lights += self.geom.findAllMatches('**/prop_snow_tree*')
            for light in lights:
                light.setColorScaleOff(0)
        base.loader.tick()

        if loader.loadingScreen.getActiveHoliday() not in self.char:
            char = self.char[ToontownGlobals.HolidayNormal]
        else:
            char = self.char[loader.loadingScreen.getActiveHoliday()]

        self.char = ToontownAvatarUtils.createChar(char)
        self.char.unloadDialogue()
        self.char.nametag.getNametag2d().setContents(0)
        self.char.setPosHpr(-6, -2, 0.02, 140, 0, 0)
        self.char.loop('neutral')
        self.char.reparentTo(self.geom)

        base.loader.tick()

        self.loadAnimatedProps()
        base.loader.tick()

        gsg = base.win.getGsg()
        if gsg:
            self.geom.prepareScene(gsg)

        self.sequence = self.setupToonAnimation()
        if self.sequence:
            self.sequence.loop()

    def setupToonAnimation(self):  # type: () -> Sequence
        return None

    def unload(self):
        if self.snow:
            self.snow.cleanup()
        if self.fog:
            self.geom.clearFog()
            self.sky.clearFog()
            del self.fog
        self.geom.removeNode()
        self.sky.removeNode()
        taskMgr.remove('skyTrack')

        self.DNAStorage.resetNodes()
        self.DNAStorage.resetTextures()
        self.removeAllTasks()

        if self.sequence:
            self.sequence.finish()

    def startCloudSky(self):
        return SkyUtil.startCloudSky(self)

    def skyTrack(self, task):
        return SkyUtil.cloudSkyTrack(task)

    def loadAnimatedProps(self):
        name2Module = {  # type: dict[str, GenericAnimatedProp]
            'GenericAnimatedProp': GenericAnimatedProp,
            'InteractiveAnimatedProp': InteractiveAnimatedProp,
            'HydrantInteractiveProp': HydrantInteractiveProp,
            'MailboxInteractiveProp': MailboxInteractiveProp,
            'TrashcanInteractiveProp': TrashcanInteractiveProp,
        }

        self.animPropList = []

        for animPropNode in self.geom.findAllMatches('**/animated_prop_*'):  # type: NodePath
            if animPropNode.getName().startswith('animated_prop_generic'):
                className = 'GenericAnimatedProp'
            elif animPropNode.getName().startswith('animated_prop_'):
                name = animPropNode.getName()[len('animated_prop_'):]
                splits = name.split('_')
                className = splits[0]
            else:
                className = animPropNode.getName()[14:-8]
            animPropModule = name2Module.get(className)
            if not animPropModule:
                self.notify.error(f'Class for animated prop {className} not found.')
                return
            animPropObj = animPropModule(animPropNode)  # type: GenericAnimatedProp
            self.animPropList.append(animPropObj)
            animPropObj.enter()
