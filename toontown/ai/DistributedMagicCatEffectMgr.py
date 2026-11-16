from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObject
from direct.interval.IntervalGlobal import *
from otp.speedchat import SpeedChatGlobals
from toontown.toonbase import TTLocalizer


class DistributedMagicCatEffectMgr(DistributedObject.DistributedObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedMagicCatEffectMgr')

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)

        def phraseSaid(phraseId, displayType):
            if displayType != 0:
                return

            # "Meet Here" phrase
            helpPhrase = 1012
            if phraseId == helpPhrase:
                self.addMagicCatEffect()

        self.accept(SpeedChatGlobals.SCStaticTextMsgEvent, phraseSaid)

    def announceGenerate(self):
        DistributedObject.DistributedObject.announceGenerate(self)
        DistributedMagicCatEffectMgr.notify.debug('announceGenerate')

    def delete(self):
        self.ignore(SpeedChatGlobals.SCStaticTextMsgEvent)
        DistributedObject.DistributedObject.delete(self)

    def addMagicCatEffect(self):
        DistributedMagicCatEffectMgr.notify.debug('addMagicCatEffect')
        av = base.localAvatar
        self.sendUpdate('addMagicCatEffect', [])
        msgTrack = Sequence(Func(av.setSystemMessage, 0, TTLocalizer.MagicCatEffect1), Wait(5.0),
                            Func(av.setSystemMessage, 0, TTLocalizer.MagicCatEffect2), Wait(6.0),
                            Func(av.setSystemMessage, 0, TTLocalizer.MagicCatEffect3), Wait(6.0),
                            Func(av.setSystemMessage, 0, TTLocalizer.MagicCatEffect4))
        msgTrack.start()
