from . import TownLoader
from . import TTTownLoader
from . import EpisodeStreet
from toontown.suit import Suit
from toontown.toon import Toon
from toontown.hood import ZoneUtil

class EpisodeTownLoader(TTTownLoader.TTTownLoader):

    def __init__(self, hood, parentFSM, doneEvent):
        TTTownLoader.TTTownLoader.__init__(self, hood, parentFSM, doneEvent)
        self.streetClass = EpisodeStreet.EpisodeStreet

    def load(self, zoneId):
        TownLoader.TownLoader.load(self, zoneId)

    def loadBattleAnims(self):
        Toon.loadTutorialBattleAnims()

    def unloadBattleAnims(self):
        Toon.unloadTutorialBattleAnims()
