from panda3d.core import *

from otp.util import random
from . import SafeZoneLoader, TLFFPlayground
from toontown.toonbase import ToontownGlobals, TTLocalizer
from ..estate import DistributedHouse

HOUSE_AV_NAMES = ('Doctor Leroy',
                  'Fluffy',
                  'Evil Blinky')
HOUSE_TITLE_NAMES = ("Doctor Leroy's \nLaboratory",
                     "Fluffy's Dog\nHouse",
                     "Evil Blinky's\nDen")

HOUSE_POSITIONS = (
    (Vec3(-82, 78, 10), Vec3(-59, 0, 0)),
    (Vec3(-35, 79, 10), Vec3(-52, 0, 0)),
    (Vec3(41, 92, 10), Vec3(-118, 0, 0))
)

class TLFFSafeZoneLoader(SafeZoneLoader.SafeZoneLoader):

    def __init__(self, hood, parentFSM, doneEvent):
        SafeZoneLoader.SafeZoneLoader.__init__(self, hood, parentFSM, doneEvent)
        self.playgroundClass = TLFFPlayground.TLFFPlayground
        self.activityMusicFile = 'phase_14.5/audio/bgm/ttrm_s_ara_tnl_nbrhood.ogg'
        self.dnaFile = 'phase_14.5/dna/ttrm_d_ara_tnl_sz.dna'
        self.musicFile = 'phase_14.5/audio/bgm/ttrm_s_ara_tnl_nbrhood.ogg'
        self.safeZoneStorageDNAFile = 'phase_14.5/dna/ttrm_d_strg_tnl_sz.dna'
        self.houses = []
        self.houseNode = []
        self.houseId2house = {}
        self.houseModels = (loader.loadModel('phase_5.5/models/estate/houseB'),)

    def load(self):
        SafeZoneLoader.SafeZoneLoader.load(self)
        self.birdSound = list(map(base.loadSfx, [
            'phase_4/audio/sfx/SZ_TC_bird1.mp3',
            'phase_4/audio/sfx/SZ_TC_bird2.mp3',
            'phase_4/audio/sfx/SZ_TC_bird3.mp3'],
                                  ['environment']))

        for i in range(3):
            np = render.attachNewNode(f'ff_House_{i}')
            np.setPosHpr(*HOUSE_POSITIONS[i])
            self.houseNode.append(np)
        for i in range(3):
            self.__createFakeHouse(i)

        cndTunnel: NodePath = self.geom.find('**/TTREALM_TOONLAND_UNIMPL__linktunnel_ff_19201_DNARoot')
        cndTunnel.find('**/sign').removeNode()
        cndTunnel.find('**/chip_dale').removeNode()

        #########################################################
        # Some of these things can (and should) be moved to DNA #
        #########################################################

        tunnelOrigin: NodePath = cndTunnel.find('**/tunnel_origin')
        originPos, originHpr = tunnelOrigin.getPos(self.geom), tunnelOrigin.getHpr(self.geom)

        # add the bird
        tunnelBirdNP = self.geom.attachNewNode('TTREALM_TOONLAND__tunnelBird')
        tunnelBirdNP.setPosHpr(
            (originPos.x + 5, originPos.y - 5, 45),
            (originHpr.x - 180, originHpr.y, originHpr.z)
        )
        tunnelBirdNP.setScale(350)
        loader.loadModel('phase_5/models/props/bird').reparentTo(tunnelBirdNP)

        deviceA: NodePath = loader.loadModel('phase_4/models/props/tt_m_prp_acs_sillyReader')
        deviceA.reparentTo(self.geom)
        deviceA.setPos(-81.5, 61.4, 17.8)
        deviceA.setScale(2.1)
        deviceA.hprInterval(8.0, Vec3(0, 270, 0), Vec3(360, 270, 0)).loop()
        deviceA.find('**/sillyReader').setX(1.4)
        deviceB: NodePath = loader.loadModel('phase_4/models/props/tt_m_prp_acs_sillyReader')
        deviceB.reparentTo(self.geom)
        deviceB.setPos(-68, 70, 17.8)
        deviceB.setScale(2.1)
        deviceB.hprInterval(8.0, Vec3(0, 270, 0), Vec3(360, 270, 0)).loop()
        deviceB.find('**/sillyReader').setX(1.4)

        thAssets: NodePath = loader.loadModel('phase_3.5/models/modules/tt_m_ara_int_toonhall')
        tallSpaceLamp = thAssets.find('**/prop_tallLamp_space').copyTo(self.geom)
        for nodePath in (tallSpaceLamp.findAllMatches('**/tallLamp') + tallSpaceLamp.findAllMatches('**/collision')):
            nodePath.setPos(76, -22, 0)
        tallSpaceLamp.setPos(-75, 74, 12)
        tallSpaceLamp.setScale(1.2)

        # not sure where this goes, this pos is just sitting in the sky
        #spaceLamp = thAssets.find('**/prop_lamp_space').copyTo(self.geom)
        #for nodePath in (spaceLamp.findAllMatches('**/lamp') + spaceLamp.findAllMatches('**/collision')):
        #    nodePath.setPos(76.6, -36, -2.45)
        #spaceLamp.setPos(-86.5, 67.5, 15.8)
        #spaceLamp.setH(180)

        thAssets.removeNode()

        # TODO: Hiccup Trashcan & Picnic Baskets

    def unload(self):
        del self.birdSound
        for house in self.houses:
            house.delete()
            del house
        SafeZoneLoader.SafeZoneLoader.unload(self)

    def __createFakeHouse(self, index):
        """ Creates a fake distributed house since the dna is a bitch to work with
            this is also close to how they did it in the original mod """
        # this is absoultely a terrible way, ima make it server sided later ~drew
        house = DistributedHouse.DistributedHouse(base.cr)
        house.setHousePos(index)
        house.setHouseType(0)
        house.setAvatarId(0)
        house.setName(HOUSE_AV_NAMES[index])
        house.setColor(3 + index)

        #base.cr.createDistributedObject(house, parentId = base.localAvatar.defaultShard,
        #                                zoneId = ToontownGlobals.ToonLandFunnyFarm,
        #                                doId = (index + 1) << 20, sendFormatGenerate = False)
        house.doId = (index + 1) << 20
        house.load()
        house.nameText.setText(HOUSE_TITLE_NAMES[index])

        randomGen = random.Random()
        randomGen.seed(house.doId)

        r = randomGen.random()
        g = randomGen.random()
        b = randomGen.random()

        house.setNameColor(int(r*255), int(g*255), int(b*255))

        house.house.wrtReparentTo(self.geom)

        self.houses.append(house)

