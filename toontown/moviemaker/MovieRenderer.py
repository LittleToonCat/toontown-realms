"""
Toontown Realms Movie Maker renderer

all hail little cat
"""

import platform
import subprocess
from typing import Tuple

from direct.showbase.DirectObject import DirectObject
from panda3d.core import ClockObject


class MovieMaker(DirectObject):

    def __init__(self, movieMaker):
        self.__movieMaker = movieMaker

        # The first frame is always just black, don't render it
        self.__firstFrame: bool = False

    def renderFFmpeg(self, videoSize: Tuple[int, int] = (1280, 720), frameRate: int = 60, filename: str = 'output.mp4'):
        """
        Render the video using FFmpeg to save to an mp4 file

        :param videoSize:
        :param frameRate:
        :param filename:
        """
        _cmdString = (
            'ffmpeg.exe' if platform.system() is 'Windows' else 'ffmpeg',
            '-y',  # overwrite w/o warning - we will ask the user on our own
            '-r', f'{frameRate}',
            '-an',
            '-analyzedduration', '0',
            '-s', f'{videoSize[0]}x{videoSize[1]}',
            '-f', 'rawvideo',
            '-pix_fmt', 'bgra',
            '-i', '-',
            '-vf', 'vflip',
            '-vcodec', 'libx264',
            filename
        )

        self.ffmpeg = subprocess.Popen(
                _cmdString,
                stdin = subprocess.PIPE,
                bufsize = -1,
                shell = False
        )

        globalClock: ClockObject = ClockObject.getGlobalClock()
        globalClock.setMode(ClockObject.MNonRealTime)
        globalClock.setDt(1.0/float(frameRate))

        self.addTask(self.renderTask)

    def renderTask(self, task):
        tex = base.win.getScreenshot()
         # todo: we should probably make a separate camera buffer
        if tex is None:
            return task.cont
        if self.__firstFrame:
            # dont render the black frame
            self.__firstFrame = False
            return task.cont
        buffer = tex.getRamImage().getData()
        self.ffmpeg.stdin.write(buffer)
        return task.cont

    def finishRendering(self):
        self.ffmpeg.stdin.close()