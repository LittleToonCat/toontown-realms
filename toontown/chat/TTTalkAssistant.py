from direct.directnotify import DirectNotifyGlobal
from direct.showbase.MessengerGlobal import messenger

from otp.chat.ChatGlobals import *
from otp.chat.TalkAssistant import TalkAssistant


class TTTalkAssistant(TalkAssistant):
    notify = DirectNotifyGlobal.directNotify.newCategory('TTTalkAssistant')

    def sendToonTaskSpeedChat(self, taskId, toNpcId, toonProgress, msgIndex):
        error = None
        messenger.send(SCChatEvent)
        messenger.send('chatUpdateSCToontask', [taskId,
         toNpcId,
         toonProgress,
         msgIndex])
        return error
