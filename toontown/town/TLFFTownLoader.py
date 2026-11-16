from . import TownLoader
from . import TLFFStreet
from toontown.suit import Suit


class TLFFTownLoader(TownLoader.TownLoader):

    def __init__(self, hood, parentFSM, doneEvent):
        super().__init__(hood, parentFSM, doneEvent)
        self.streetClass = TLFFStreet.TLFFStreet
        self.musicFile = 'phase_14.5/audio/bgm/ttrm_s_ara_tnl_street.ogg'
        self.activityMusicFile = 'phase_14.5/audio/bgm/ttrm_s_ara_tnl_street.ogg'
        self.battleMusicFile = 'phase_4/audio/bgm/TC_battle.ogg'
        self.townStorageDNAFile = 'phase_14.5/dna/ttrm_d_strg_tnl_street.dna'

    def load(self, zoneId):
        super().load(zoneId)
        Suit.loadSuits()
        dnaFile = 'phase_14.5/dna/ttrm_d_ara_tnl_' + str(self.canonicalBranchZone) + '.dna'
        self.createHood(dnaFile)

        # The toonland funnyfarm streets have their own street texture, apply it to the tunnel floor as well
        newStreetTexture = loader.loadTexture('phase_14.5/maps/ttrm_t_ara_tnl_streetYellow.png')
        for tunnel in self.geom.findAllMatches('**/linktunnel*'):
            tunnel.find('**/tunnel_floor*').setTexture(newStreetTexture, 1)

    def unload(self):
        Suit.unloadSuits()
        super().unload()
