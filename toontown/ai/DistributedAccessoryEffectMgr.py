from direct.distributed.DistributedObject import DistributedObject
from direct.interval.IntervalGlobal import *
from otp.speedchat import SpeedChatGlobals
from toontown.toonbase import TTLocalizer

class DistributedAccessoryEffectMgr(DistributedObject):

    def __init__(self, cr):
        DistributedObject.__init__(self, cr)
        self.phraseId = 0

        def phraseSaid(phraseId, displayType):
            if displayType != 0:
                return
            if phraseId == self.phraseId:
                self.addAccessoryEffect()

        self.accept(SpeedChatGlobals.SCStaticTextMsgEvent, phraseSaid)

    def setPhraseId(self, phraseId: int):
        self.phraseId = phraseId

    def delete(self):
        self.ignore(SpeedChatGlobals.SCStaticTextMsgEvent)
        DistributedObject.delete(self)

    def addAccessoryEffect(self):
        self.sendUpdate('addAccessoryEffect', [])

    def addAccessoryEffectSuccess(self):
        msgTrack = Sequence(Func(base.localAvatar.setSystemMessage, 0, TTLocalizer.AccessoryEffectMsg))
        msgTrack.start()
