from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.interval.IntervalGlobal import *
from .DistributedNPCToonBase import DistributedNPCToonBase
from panda3d.toontown import CFTimeout, CFSpeech
from toontown.toonbase import TTLocalizer, ToontownGlobals, ControlManager


class DistributedNPCPeriscope(DistributedNPCToonBase):
    notify = directNotify.newCategory('DistributedNPCPeriscope')

    def __init__(self, cr):
        DistributedNPCToonBase.__init__(self, cr)
        self.ival = None
        self.alertSfx = loader.loadSfx('phase_9/audio/sfx/CHQ_GOON_tractor_beam_alarmed.ogg')
        self.lightSwitchSfx = loader.loadSfx('phase_11/audio/sfx/LB_camera_shutter_2.ogg')
        self.megaDefeatSfx = loader.loadSfx('phase_6/audio/sfx/Golf_Crowd_Applause.ogg')
        self.cheerSfx = loader.loadSfx('phase_6/audio/sfx/KART_Applause_2.ogg')
        self.accept('notifyHolidayStart', self.speakAboutHolidayStart)
        self.accept('notifyHolidayOngoing', self.speakAboutHolidayOngoing)
        self.accept('notifyHolidayEnd', self.speakAboutHolidayEnd)
        self.accept('notifyMisc', self.speakAboutMisc)

    def disable(self):
        if self.ival and self.ival.isPlaying():
            self.ival.finish()
        self.ignore('notifyHolidayStart')
        self.ignore('notifyHolidayOngoing')
        self.ignore('notifyHolidayEnd')
        self.ignore('notifyMisc')
        DistributedNPCToonBase.disable(self)

    def initToonState(self):
        self.ignoreAvatars()
        self.reparentTo(render)
        self.initPos()

    def initPos(self):
        self.clearMat()
        adjustScale = (0.85 - self.scale) * 2.5
        self.setPos(-5.25, 32.45 - adjustScale, 5.45)
        self.setH(180)

        periscope = render.find('**/periscope-base')
        if periscope:
            periscope.setZ(periscope.getZ() - adjustScale)

    # The reason a lot of these are empty and/or segmented methods is
    # in case someone wants to add more intervals or unique events
    # in the future
    def speakAboutInvasionStatus(self, cogList, special, virtual, msgType, mega):
        self.ival = Sequence()
        self.chatIval = Sequence()
        if msgType == ToontownGlobals.SuitInvasionBegin:
            if mega:
                music = None
                musicTime = 0.0
                musicVol = 0.7
                place = base.cr.playGame.getPlace()
                if place:
                    music = place.loader.activityMusic
                if music:
                    musicVol = music.getVolume()
                    musicTime = music.getTime()
                    music.stop()

                self.chatIval.append(Sequence(
                    Wait(2),
                    Func(self.__cleanupAndSpeak, TTLocalizer.NPCPeriscopeMegaInv),
                    Wait(3),
                    Func(self.__cleanupAndSpeak, TTLocalizer.SuitMegaInvasionAnnounce),
                    Wait(3),
                    Func(self.__cleanupAndSpeak, base.cr.newsManager.getInvadingCogMessage(cogList, special, virtual, msgType))
                ))
                self.ival.append(Parallel(Func(render.setColorScale, (0, 0, 0, 1)),
                                          SoundInterval(self.lightSwitchSfx, volume=0.8)))
                for i in range(3):
                    self.ival.append(Sequence(
                        Parallel(SoundInterval(self.alertSfx), LerpColorScaleInterval(render, 1, (1, 0, 0, 1))),
                        LerpColorScaleInterval(render, 1, (0, 0, 0, 1))))
                self.ival.append(Parallel(Func(render.clearColorScale), SoundInterval(self.lightSwitchSfx, volume=0.8),
                                          Func(base.playMusic, music, looping=1, time=musicTime, volume=musicVol)))
            else:
                self.chatIval.append(Sequence(
                    Wait(0.5),
                    Func(self.__cleanupAndSpeak, TTLocalizer.SuitInvasionAnnounce),
                    Wait(3),
                    Func(self.__cleanupAndSpeak, base.cr.newsManager.getInvadingCogMessage(cogList, special, virtual, msgType))
                ))
                for i in range(3):
                    self.ival.append(SoundInterval(self.alertSfx))
        elif msgType == ToontownGlobals.SuitInvasionUpdate:
            if mega:
                pass
            else:
                pass
        elif msgType == ToontownGlobals.SuitInvasionEnd:
            self.chatIval.append(Sequence(
                Wait(0.5),
                Func(self.__cleanupAndSpeak, base.cr.newsManager.getInvadingCogMessage(cogList, special, virtual, msgType)),
                Wait(3),
                Func(self.__cleanupAndSpeak, TTLocalizer.NPCPeriscopeInvFinish)
                ))
            if mega:
                self.ival.append(SoundInterval(self.megaDefeatSfx))
            else:
                self.ival.append(SoundInterval(self.cheerSfx))
        elif msgType == ToontownGlobals.SuitInvasionBulletin:
            if mega:
                pass
            else:
                pass
        else:
            self.notify.warning(f'setInvasionStatus: invalid msgType: {msgType}')
            return
        self.chatIval.start()
        self.ival.start()

    def __cleanupMsg(self, msg):
        msg = msg.replace(TTLocalizer.lToonHQ + ': ', '', 1)
        return msg

    def __cleanupAndSpeak(self, msg):
        msg = self.__cleanupMsg(msg)
        self.setChatAbsolute(msg, CFSpeech | CFTimeout)

    def speakAboutHolidayStart(self, msg):
        self.__cleanupAndSpeak(msg)
        base.playSfx(self.cheerSfx)

    def speakAboutHolidayOngoing(self, msg):
        self.__cleanupAndSpeak(msg)

    def speakAboutHolidayEnd(self, msg):
        self.__cleanupAndSpeak(msg)

    def speakAboutFireworks(self, msg):
        # Some messages have hotkeys that need to be converted
        msg = ControlManager.ControlManager.parseHotkeyString(msg)
        self.__cleanupAndSpeak(msg)

    def speakAboutMaintenance(self):
        base.playSfx(self.alertSfx)

    def speakAboutMisc(self, msg):
        if TTLocalizer.lToonHQ in msg:
            self.__cleanupAndSpeak(msg)
