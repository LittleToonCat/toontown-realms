from direct.interval.IntervalGlobal import *
from otp.avatar import Avatar
from toontown.effects import DustCloud
from toontown.toonbase import ClientSettings

AnimDict = {'s': (('neutral', 'neutral'), ('float', 'float'), ('grow', 'grow'), ('spin', 'spin')),
            'l': (('neutral', 'neutral'), ('fly', 'fly'), ('jump', 'jump'), ('laugh', 'laugh'))}
ModelDict = {'s': 'phase_14.5/models/char/pumpkin-short-',
             'l': 'phase_14.5/models/char/pumpkin-tall-'}
PumpkinDNA = ['s', 'l']

IvalAnimDict = {'s': [['grow', 'float', 'spin', 'float'], ['spin', 'grow', 'float', 'float'],
                      ['float', 'spin', 'grow', 'grow']],
                'l': [['laugh', 'fly', 'jump', 'fly'], ['jump', 'laugh', 'fly', 'fly'],
                      ['fly', 'jump', 'laugh', 'laugh']]}
IvalWaitDict = {'s': [[1, 2, 3, 4], [11, 10, 9, 8]], 'l': [[5, 6, 7, 8], [7, 6, 5, 4]]}


class Pumpkin(Avatar.Avatar):

    def __init__(self):
        try:
            self.Pump_init
        except:
            self.Pump_init = 1
            Avatar.Avatar.__init__(self)

        return

    def delete(self):
        try:
            self.Pump_del
        except:
            self.Pump_del = 1
            filePrefix = ModelDict[self.size]
            loader.unloadModel(filePrefix + 'mod')
            animList = AnimDict[self.size]
            for anim in animList:
                loader.unloadModel(filePrefix + anim[1])

            Avatar.Avatar.delete(self)

        return None

    def setSize(self, size):
        if size in PumpkinDNA:
            self.size = size
        else:
            self.notify.warning("Pumpkin DNA isn't valid! Defaulting to 's'.")
            self.size = 's'

    def setId(self, id):
        self.id = id

    def generatePumpkin(self):
        filePrefix = ModelDict[self.size]
        self.loadModel(filePrefix + 'mod')
        animDict = {}
        animList = AnimDict[self.size]
        for anim in animList:
            animDict[anim[0]] = filePrefix + anim[1]

        self.loadAnims(animDict)
        self.setBlend(frameBlend=ClientSettings.SmoothAnimations.get())
        self.reparentTo(render)

    def getAnim(self, id=None):
        if not id:
            return Sequence(ActorInterval(self, 'neutral'))
        try:
            animList = IvalAnimDict[self.size][id]
            waitTimeList = IvalWaitDict[self.size][id]
            return Sequence(Wait(waitTimeList[0]), ActorInterval(self, animList[0]), Func(self.loop, 'neutral'),
                            Wait(12), ActorInterval(self, animList[1]), Func(self.loop, 'neutral'), Wait(12),
                            ActorInterval(self, animList[2]), Func(self.loop, 'neutral'), Wait(waitTimeList[1]))
        except (AttributeError, IndexError):
            return Sequence(ActorInterval(self, 'neutral'))

    def getDustCloudIval(self):
        dustCloud = DustCloud.DustCloud(fBillboard=0, wantSound=1)
        dustCloud.setBillboardAxis(2.0)
        dustCloud.setZ(3)
        dustCloud.setScale(0.4)
        dustCloud.createTrack()
        return Sequence(Func(dustCloud.reparentTo, self), dustCloud.track, Func(dustCloud.destroy),
                        name='dustCloudIval')

    def showPumpkin(self):
        self.setScale(0.01)

        dustCloudIval = self.getDustCloudIval()
        ival = Parallel(dustCloudIval, LerpScaleInterval(self, 0.5, 1.0))
        ival.start()

    def hidePumpkin(self):
        dustCloudIval = self.getDustCloudIval()
        ival = Parallel(dustCloudIval, Sequence(LerpScaleInterval(self, 0.5, 0.01), Func(self.hide)))
        ival.start()
