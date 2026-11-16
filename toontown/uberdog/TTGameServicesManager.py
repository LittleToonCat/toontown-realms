from direct.directnotify import DirectNotifyGlobal
from typing import List, Optional, Tuple

from otp.uberdog.GameServicesManager import GameServicesManager
from toontown.toonbase.ToontownTypes import TPickAToonProp, TPosHpr

if game.process == 'client':
    from toontown.toontowngui.MOTDDialog import MOTDDialog


class TTGameServicesManager(GameServicesManager):
    notify = DirectNotifyGlobal.directNotify.newCategory('TTGameServicesManager')

    def __init__(self, cr):
        GameServicesManager.__init__(self, cr)
        self.motdDialog: Optional[MOTDDialog] = None
        self.pickAToonBackground: Optional[Tuple[List[str], str, int, List[TPickAToonProp], List[TPosHpr], TPosHpr]] = None

    def sendSetNamePattern(self, avId, p1, f1, p2, f2, p3, f3, p4, f4, callback):
        self._callback = callback
        self.sendUpdate('setNamePattern', [avId, p1, f1, p2, f2, p3, f3, p4, f4])

    def namePatternResponse(self, avId, status):
        self._callback(avId, status)

    def sendSetNameTyped(self, avId, name, callback):
        self._callback = callback
        self.sendUpdate('setNameTyped', [avId, name])

    def nameTypedResponse(self, avId, status):
        self._callback(avId, status)

    def sendCreateAvatar(self, avDNA, _, index):
        self.sendUpdate('createAvatar', [avDNA.makeNetString(), _, index])

    def createAvatarResponse(self, avId):
        messenger.send('nameShopCreateAvatarDone', [avId])

    def sendAcknowledgeAvatarName(self, avId, callback):
        self._callback = callback
        self.sendUpdate('acknowledgeAvatarName', [avId])

    def acknowledgeAvatarNameResponse(self):
        self._callback()

    def setMotd(self, text: str):
        self.motdDialog = MOTDDialog(text)

    def setPickAToonBackground(self, dnaStorages: List[str], dnaFile: str, sky: int, props: List[TPickAToonProp], toonPositions: List[TPosHpr], cameraPos: TPosHpr):
        if not dnaFile and not props:
            # If this is empty, we wer probably sent nothing, so we will fallback to the main menu backgrounds
            self.pickAToonBackground = None
            return
        self.pickAToonBackground = (dnaStorages, dnaFile, sky, props, toonPositions, cameraPos)

