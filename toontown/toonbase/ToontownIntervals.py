# This contains some intervals similar to the bounce track ones defined below
from direct.showutil.Effects import *
from direct.interval.IntervalGlobal import Func, LerpPosInterval, LerpScaleInterval, Sequence, Wait

PULSE_GUI_DURATION = 0.2
PULSE_GUI_CHANGE = 0.333


def cleanup(name):
    taskMgr.remove(name)


def start(ival):
    cleanup(ival.getName())
    ival.start()
    return ival


def loop(ival):
    cleanup(ival.getName())
    ival.loop()
    return ival


def getPulseLargerIval(np, name, duration=PULSE_GUI_DURATION, scale=1):
    return getPulseIval(np, name, 1 + PULSE_GUI_CHANGE, duration=duration, scale=scale)


def getPulseSmallerIval(np, name, duration=PULSE_GUI_DURATION, scale=1):
    return getPulseIval(np, name, 1 - PULSE_GUI_CHANGE, duration=duration, scale=scale)


def getPulseIval(np, name, change, duration=PULSE_GUI_CHANGE, scale=1):
    return Sequence(np.scaleInterval(duration, scale * change, blendType='easeOut'), np.scaleInterval(duration, scale, blendType='easeIn'), name=name, autoFinish=1)


def getPresentGuiIval(np, name, waitDuration=0.5, moveDuration=1.0, parent=aspect2d, startPos=(0, 0, 0)):
    endPos = np.getPos()
    np.setPos(parent, startPos[0], startPos[1], startPos[2])
    return Sequence(Func(np.show), getPulseLargerIval(np, '', scale=np.getScale()), Wait(waitDuration), np.posInterval(moveDuration, endPos, blendType='easeInOut'), name=name, autoFinish=1)


# Moved here from DistributedBuilding so it can be used anywhere (DistributedBuilding still calls it though)
def createScaleBounceTrack(np, name, numBounces = 1, startScale = 1, totalTime = 1, slowInitBounce = 0.0, endScale = None):
    result = Sequence(name=name)
    numBounces += 1
    if slowInitBounce:
        bounceTime = totalTime / (numBounces + slowInitBounce - 1.0)
        currTime = bounceTime * float(slowInitBounce)
    else:
        bounceTime = totalTime / float(numBounces)
        currTime = bounceTime

    realScale = np.getScale()
    if endScale is None:
        endScale = realScale[2]
    currScaleDiff = startScale - endScale

    for currBounceScale in range(numBounces):
        if currBounceScale == numBounces - 1:
            currScale = endScale
        elif currBounceScale % 2:
            currScale = endScale - currScaleDiff
        else:
            currScale = endScale + currScaleDiff

        result.append(LerpScaleInterval(np, currTime, Vec3(realScale[0], realScale[1], currScale), blendType='easeInOut'))
        currScaleDiff *= 0.5
        if currTime != bounceTime:
            currTime = bounceTime

    return result


# A copy of createScaleBounceTrack but manipulates position instead of scale
def createPosBounceTrack(np, name, numBounces = 1, startPos = 1, totalTime = 1, slowInitBounce = 0.0, endPos = None):
    result = Sequence(name=name)
    numBounces += 1
    if slowInitBounce:
        bounceTime = totalTime / (numBounces + slowInitBounce - 1.0)
        currTime = bounceTime * float(slowInitBounce)
    else:
        bounceTime = totalTime / float(numBounces)
        currTime = bounceTime

    realPos = np.getPos()
    if endPos is None:
        endPos = realPos[2]
    currPosDiff = startPos - endPos

    for currBouncePos in range(numBounces):
        if currBouncePos == numBounces - 1:
            currPos = endPos
        elif currBouncePos % 2:
            currPos = endPos - currPosDiff
        else:
            currPos = endPos + currPosDiff

        result.append(LerpPosInterval(np, currTime, Vec3(realPos[0], realPos[1], currPos), blendType='easeInOut'))
        currPosDiff *= 0.5
        if currTime != bounceTime:
            currTime = bounceTime

    return result
