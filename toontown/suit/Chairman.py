from otp.avatar.Avatar import Avatar
from panda3d.toontown import *
from toontown.toonbase import ToontownGlobals, ClientSettings

ChairmanDialogArray = []


def loadDialog():
    global ChairmanDialogArray
    if len(ChairmanDialogArray) > 0:
        return
    else:
        loadPath = 'phase_14/audio/sfx/'
        ChairmanDialogFiles = ['Chairman_COG_VO_grunt',
                               'Chairman_COG_VO_murmur',
                               'Chairman_COG_VO_statement',
                               'Chairman_COG_VO_question']
        for file in ChairmanDialogFiles:
            ChairmanDialogArray.append(base.loader.loadSfx(loadPath + file + '.ogg'))

        ChairmanDialogArray.append(ChairmanDialogArray[2])
        ChairmanDialogArray.append(ChairmanDialogArray[2])


def unloadDialog():
    global ChairmanDialogArray
    ChairmanDialogArray = []


class Chairman(Avatar):
    def __init__(self):
        Avatar.__init__(self)
        self.setFont(ToontownGlobals.getSuitFont())
        self.setPlayerType(NametagGroup.CCSuit)
        self.initializeNametag3d()
        self.initializeDropShadow()
        self.nametag3d.setPos(0, 0, 19.75)
        self.dropShadow.setScale(2)
        self.nametag3d.setScale(1.4)
        self.setPickable(0)
        self.loadModel('phase_14/models/char/chairman-mod')
        self.loadAnims({'neutral': 'phase_14/models/char/chairman-neutral',
                        'walk': 'phase_14/models/char/chairman-walk',
                        'into-type': 'phase_14/models/char/chairman-into-type',
                        'type': 'phase_14/models/char/chairman-type',
                        'capture': 'phase_14/models/char/chairman-capture'})
        self.setBlend(frameBlend=ClientSettings.SmoothAnimations.get())

    def getNametagJoints(self):
        return []

    def getDialogueArray(self):
        loadDialog()
        return ChairmanDialogArray

    def getTTSDarwinVoice(self):
        return ToontownGlobals.DefaultVoiceChairman
