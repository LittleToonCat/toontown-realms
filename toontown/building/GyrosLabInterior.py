from .ToonInterior import ToonInterior
from toontown.hood.BetaPlace import BetaPlace


class GyrosLabInterior(ToonInterior, BetaPlace):
    def load(self):
        ToonInterior.load(self)
        BetaPlace.load(self)

    def enter(self, requestStatus):
        ToonInterior.enter(self, requestStatus)
        BetaPlace.enter(self)

    def exit(self):
        BetaPlace.exit(self)
        ToonInterior.exit(self)

    def getCustomSong(self):
        return 'phase_14.5/audio/bgm/flash_intro.ogg'
