from panda3d.core import Vec4

from direct.gui.DirectGui import DirectFrame
from direct.interval.IntervalGlobal import Sequence, LerpHprInterval
import random


class DialMeter(DirectFrame):
    notify = directNotify.newCategory('DialMeter')

    MeterFull = None
    MeterHalf = None

    NeedleOffset = -90

    def __init__(self, parent=aspect2d, **kw):
        optiondefs = (('baseColor', Vec4(0.87, 0.87, 0.827, 1), None),
                      ('meterColor', Vec4(0.7, 0.3, 0.3, 1), None),
                      ('markerColor', Vec4(0.3, 0.3, 0.3, 1), None),
                      ('showNeedle', True, None))
        self.defineoptions(kw, optiondefs)
        DirectFrame.__init__(self, parent, **kw)
        self.initialiseoptions(DialMeter)
        if not self.MeterFull:
            gui = loader.loadModel('phase_9/models/gui/cog_disguises')
            self.MeterFull = gui.find('**/meter_face_whole')
            self.MeterHalf = gui.find('**/meter_face_half')
            gui.removeNode()
        self.meterFace = self.MeterFull.copyTo(self)
        self.meterFace.flattenStrong()
        self.meterFace.setColor(self['baseColor'])
        self.meterFaceHalf1 = self.MeterHalf.copyTo(self)
        self.meterFaceHalf1.flattenStrong()
        self.meterFaceHalf1.setColor(self['meterColor'])
        self.meterFaceHalf2 = self.MeterHalf.copyTo(self)
        self.meterFaceHalf2.flattenStrong()
        self.meterFaceHalf2.setColor(self['baseColor'])
        self.meterFaceHalf1.hide()
        self.meterFaceHalf2.hide()
        self.needleIval = None
        self.notify.debug(f"show needle? {self['showNeedle']}")
        if self['showNeedle']:
            self.meterNeedle = self.MeterHalf.copyTo(self)
            self.meterNeedle.setScale(1, 1, 0.05)
            self.meterNeedle.flattenStrong()
            self.meterNeedle.setColor(self['markerColor'])
            self.meterNeedle.setR(self.NeedleOffset)
            self.needleIval = self.__makeNewIval()
            self.needleIval.loop()

    def destroy(self):
        self.__cleanupIval()

        DirectFrame.destroy(self)

    def __cleanupIval(self):
        if self.needleIval and self.needleIval.isPlaying():
            self.needleIval.finish()

    def __makeNewIval(self):
        currHpr = self.meterNeedle.getHpr()

        def getRandomNum():
            return random.uniform(0.01, 0.1)

        seq = Sequence()

        for i in range(4):
            seq.append(LerpHprInterval(self.meterNeedle, getRandomNum(), currHpr + (0, 0, 5)))
            seq.append(LerpHprInterval(self.meterNeedle, getRandomNum(), currHpr))

        return seq

    def update(self, progress):
        self.__cleanupIval()
        oldProgress = progress
        if progress == 0:
            self.meterFaceHalf1.hide()
            self.meterFaceHalf2.hide()
            self.meterFace.setColor(self['baseColor'])
        elif progress == 1:
            self.meterFaceHalf1.hide()
            self.meterFaceHalf2.hide()
            self.meterFace.setColor(self['meterColor'])
        else:
            self.meterFaceHalf1.show()
            self.meterFaceHalf2.show()
            self.meterFace.setColor(self['baseColor'])
            if progress < 0.5:
                self.meterFaceHalf2.setColor(self['baseColor'])
            else:
                self.meterFaceHalf2.setColor(self['meterColor'])
                progress -= 0.5
            self.meterFaceHalf2.setR(180 * (progress / 0.5))

        if self['showNeedle']:
            self.meterNeedle.setR(180 * (oldProgress / 0.5) + self.NeedleOffset)
            self.needleIval = self.__makeNewIval()
            self.needleIval.loop()
