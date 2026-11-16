from typing import Optional

from panda3d.core import AudioSound
from direct.interval.IntervalGlobal import *

FULL_A = 0.0
FULL_B = 1.0


class AdaptiveMusic:

    def __init__(self, songAPath: str, songBPath: str):
        """
        Simple class to handle adaptive soundtracks
        :param songAPath: Filepath to Song A
        :param songBPath: Filepath to Song B
        """
        self.__musicA, self.__musicB = loader.loadMusic((songAPath, songBPath))
        self.__mix = 0.0
        self.__activeIval: Optional[Sequence] = None

    def play(self, looping = False, interrupt = True, time = 0.0):
        for music in (self.__musicA, self.__musicB):

            # if interrupt was set to 0, start over even if it's
            # already playing
            if interrupt or (music.status() != AudioSound.PLAYING):
                music.setTime(time)
                music.setLoop(looping)
                music.setVolume(1.0)
                music.play()
        self.__setVolume()

    def stop(self):
        for music in (self.__musicA, self.__musicB):
            music.stop()

    def setMix(self, mix = 0.0):
        """
        Instantly set mix value
        :param mix:
        :return:
        """
        self.__mix = mix
        self.__setVolume()

    def __setVolume(self):
        self.__musicA.setVolume(1-self.__mix)
        self.__musicB.setVolume(self.__mix)

    def changeMix(self, targetMix: float, duration: float = 1.0):
        """
        Smoothly blend between different mixes
        :param targetMix: Target mix value
        :param duration: Blend duration
        """
        if self.__mix == targetMix:
            return

        if self.__activeIval:
            self.__activeIval.pause()
            self.__activeIval = None

        self.__activeIval = LerpFunctionInterval(self.setMix, duration, fromData = self.__mix, toData = targetMix,
                                                 name = 'AdaptiveMusicFade')
        self.__activeIval.start()
