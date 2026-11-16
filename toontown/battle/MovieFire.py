from panda3d.core import *
from direct.interval.IntervalGlobal import *
from .BattleBase import *
from .BattleProps import *
from .BattleSounds import *
from toontown.toon.ToonDNA import *
from toontown.suit.SuitDNA import *
from direct.directnotify import DirectNotifyGlobal
from . import MovieCamera
from . import MovieUtil
from otp.otpbase.PythonUtil import cmp_to_key
from math import sqrt

notify = DirectNotifyGlobal.directNotify.newCategory('MovieFire')


def addHit(dict, suitId, hitCount):
    if suitId in dict:
        dict[suitId] += hitCount
    else:
        dict[suitId] = hitCount


def doFires(fires):
    if len(fires) == 0:
        return (None, None)

    suitFiresDict = {}
    for fire in fires:
        suitId = fire['target']['suit'].doId
        if suitId in suitFiresDict:
            suitFiresDict[suitId].append(fire)
        else:
            suitFiresDict[suitId] = [fire]

    suitFires = list(suitFiresDict.values())
    def compFunc(a, b):
        if len(a) > len(b):
            return 1
        elif len(a) < len(b):
            return -1
        return 0
    suitFires.sort(key=cmp_to_key(compFunc))

    totalHitDict = {}
    singleHitDict = {}
    groupHitDict = {}

    for fire in fires:
        suitId = fire['target']['suit'].doId
        if 1:
            if fire['target']['hp'] > 0:
                addHit(singleHitDict, suitId, 1)
                addHit(totalHitDict, suitId, 1)
            else:
                addHit(singleHitDict, suitId, 0)
                addHit(totalHitDict, suitId, 0)

    notify.debug(f'singleHitDict = {singleHitDict}')
    notify.debug(f'groupHitDict = {groupHitDict}')
    notify.debug(f'totalHitDict = {totalHitDict}')

    delay = 0.0
    mtrack = Parallel()
    firedTargets = []
    for sf in suitFires:
        if len(sf) > 0:
            ival = __doSuitFires(sf)
            if ival:
                mtrack.append(Sequence(Wait(delay), ival))
            delay = delay + TOON_FIRE_SUIT_DELAY

    retTrack = Sequence()
    retTrack.append(mtrack)
    camDuration = retTrack.getDuration()
    camTrack = MovieCamera.chooseFireShot(fires, suitFiresDict, camDuration)
    return (retTrack, camTrack)

def __doSuitFires(fires):
    toonTracks = Parallel()
    delay = 0.0
    hitCount = 0
    for fire in fires:
        if fire['target']['hp'] > 0:
            hitCount += 1
        else:
            break

    suitList = []
    for fire in fires:
        if fire['target']['suit'] not in suitList:
            suitList.append(fire['target']['suit'])

    for fire in fires:
        showSuitCannon = 1
        if fire['target']['suit'] not in suitList:
            showSuitCannon = 0
        else:
            suitList.remove(fire['target']['suit'])
        tracks = __fireSuit(fire, delay, hitCount, showSuitCannon)
        if tracks:
            for track in tracks:
                toonTracks.append(track)

        delay = delay + TOON_THROW_DELAY

    return toonTracks


def __getSoundTrack(level, delay, dur, node = None, isCog = False):
    if isCog:
        sfx = globalBattleSoundCache.getSound('SA_pink_slip.ogg')
    else:
        sfx = globalBattleSoundCache.getSound('AA_drop_trigger_box.ogg')
    throwTrack = Sequence(Wait(delay), SoundInterval(sfx, node=node, duration=dur))
    return throwTrack


def __fireSuit(throw, delay, hitCount, showCannon = 1):
    toon = throw['toon']
    hpbonus = throw['hpbonus']
    target = throw['target']
    suit = target['suit']
    hp = target['hp']
    kbbonus = target['kbbonus']
    sidestep = throw['sidestep']
    died = target['died']
    revived = target['revived']
    leftSuits = target['leftSuits']
    rightSuits = target['rightSuits']
    level = throw['level']
    battle = throw['battle']
    suitPos = suit.getPos(battle)
    origHpr = toon.getHpr(battle)

    notify.debug(f'toon: {toon.getName()} fires suit: {suit.doId} for hp: {hp}')

    toonTrack = Sequence()
    propTrack = Sequence()
    atkHit = hp > 0
    if toon.getTransformationsIndex(0):
        if toon.suit.getBodyType() == 'a':
            animRate = 1.23
        elif toon.suit.getBodyType() == 'b':
            animRate = 1.2
        elif toon.suit.getBodyType() == 'c':
            animRate = 0.95
        pinkSlip = globalPropPool.getProp('pink-slip')
        pinkSlip.setPosHpr(0.07, -0.06, -0.18, -172.075, -26.715, -89.131)

        dust = globalPropPool.getProp('dust')
        dust.setPos(suit.getPos(battle))
        dust.setZ(dust.getZ() - 0.55)
        dust.setScale(1.5)
        dust.setBillboardPointEye()

        toonTrack.append(Wait(delay))
        toonTrack.append(Func(toon.headsUp, battle, suitPos))
        toonTrack.append(ActorInterval(toon.suit, 'throw-paper', playRate=animRate))
        toonTrack.append(Func(toon.suit.loop, 'neutral'))
        toonTrack.append(Func(toon.setHpr, battle, origHpr))

        propTrack.append(Wait(delay + 0.4))
        propTrack.append(Func(pinkSlip.reparentTo, toon.suit.rightHand))
        propTrack.append(pinkSlip.scaleInterval(0.5, Point3(8, 8, 8)))
        propTrack.append(Wait(1.6))
        propTrack.append(Func(pinkSlip.wrtReparentTo, battle))
        propTrack.append(pinkSlip.posInterval(0.5, suit.getPos(battle)))
        propTrack.append(Func(MovieUtil.removeProp, pinkSlip))
        propTrack.append(Func(dust.reparentTo, battle))
        propTrack.append(ActorInterval(dust, 'dust'))
        propTrack.append(Func(MovieUtil.removeProp, dust))
        soundDelay = 2.35
        soundDuration = 1
        isCog = True
    else:
        button = globalPropPool.getProp('button')
        button2 = MovieUtil.copyProp(button)
        buttons = [button, button2]
        hands = toon.getLeftHands()

        toonTrack.append(Wait(delay))
        toonTrack.append(Func(toon.headsUp, battle, suitPos))
        toonTrack.append(ActorInterval(toon, 'pushbutton'))
        if atkHit:
            toonTrack.append(ActorInterval(toon, 'wave', duration=2.0))
            toonTrack.append(ActorInterval(toon, 'duck'))
        toonTrack.append(Func(toon.loop, 'neutral'))
        toonTrack.append(Func(toon.setHpr, battle, origHpr))

        propTrack.append(Wait(delay))
        propTrack.append(Func(MovieUtil.showProps, buttons, hands))
        propTrack.append(LerpScaleInterval(button, 1.0, button.getScale(), startScale=Point3(0.01, 0.01, 0.01)))
        propTrack.append(Wait(2.5))
        propTrack.append(LerpScaleInterval(button, 1.0, Point3(0.01, 0.01, 0.01), startScale=button.getScale()))
        propTrack.append(Func(MovieUtil.removeProps, buttons))
        soundDelay = 2.15
        soundDuration = 0.39
        isCog = False

    soundTrack = __getSoundTrack(level, soundDelay, soundDuration, toon, isCog)
    suitResponseTrack = Sequence()
    reactIval = Sequence()

    if showCannon:
        sival = []
        reactIval = getCannonIval(battle, suit, atkHit)
        if hitCount == 1:
            sival = Sequence(Parallel(reactIval, MovieUtil.createSuitStunInterval(suit, 0.3, 1.3)))
        else:
            sival = reactIval
        suitResponseTrack.append(Wait(delay + 3.0))
        if atkHit:
            suitResponseTrack.append(Func(suit.showHpText, -hp, openEnded=0))
            suitResponseTrack.append(Func(suit.updateHealthBar, hp))
        suitResponseTrack.append(sival)
        bonusTrack = Sequence(Wait(delay + 3.0))
        if kbbonus > 0:
            bonusTrack.append(Wait(0.75))
            bonusTrack.append(Func(suit.showHpText, -kbbonus, 2, openEnded=0))
            bonusTrack.append(Func(suit.updateHealthBar, kbbonus))
        if hpbonus > 0:
            bonusTrack.append(Wait(0.75))
            bonusTrack.append(Func(suit.showHpText, -hpbonus, 1, openEnded=0))
            bonusTrack.append(Func(suit.updateHealthBar, hpbonus))
        suitResponseTrack = Parallel(suitResponseTrack, bonusTrack)
    return [toonTrack, soundTrack, propTrack, suitResponseTrack]


def getCannonIval(battle, suit, atkHit: bool):
    cannon = loader.loadModel('phase_4/models/minigames/toon_cannon')
    barrel = cannon.find('**/cannon')
    barrel.setHpr(0, 90, 0)
    cannonHolder = render.attachNewNode('CannonHolder')
    cannon.reparentTo(cannonHolder)
    if not atkHit:
        y = -5
    else:
        y = 0
    cannon.setPos(0, y, -8.6)
    cannonHolder.setPos(suit.getPos(render))
    cannonHolder.setHpr(suit.getHpr(render))
    cannonAttachPoint = barrel.attachNewNode('CannonAttach')
    kapowAttachPoint = barrel.attachNewNode('kapowAttach')

    scaleFactor = 1.6
    iScale = 1 / scaleFactor
    barrel.setScale(scaleFactor, 1, scaleFactor)
    cannonAttachPoint.setScale(iScale, 1, iScale)
    cannonAttachPoint.setPos(0, 6.7, 0)
    kapowAttachPoint.setPos(0, -0.5, 1.9)

    if atkHit:
        suit.reparentTo(cannonAttachPoint)
        suit.setPos(0, 0, 0)
        suit.setHpr(0, -90, 0)
        suitLevel = suit.getActualLevel()

        if suitLevel > 12:
            suitLevel = 12
        deep = 2.5 + suitLevel * 0.2
        suitScale = 0.9
        suitScale = 0.9 - sqrt(suitLevel) * 0.1
        kapow = globalPropPool.getProp('kapow')
        kapow.reparentTo(kapowAttachPoint)
        kapow.hide()
        kapow.setScale(0.25)
        kapow.setBillboardPointEye()
        smoke = loader.loadModel('phase_4/models/props/test_clouds')
        smoke.reparentTo(cannonAttachPoint)
        smoke.setScale(0.5)
        smoke.hide()
        smoke.setBillboardPointEye()
        soundBomb = base.loader.loadSfx('phase_4/audio/sfx/MG_cannon_fire_alt.ogg')
        soundFly = base.loader.loadSfx('phase_4/audio/sfx/firework_whistle_01.ogg')
        soundCogPanic = base.loader.loadSfx('phase_5/audio/sfx/ENC_cogafssm.ogg')

    posInit = cannonHolder.getPos()
    posFinal = Point3(posInit[0] + 0.0, posInit[1] + 0.0, posInit[2] + 7.0)

    soundCannonAdjust = base.loader.loadSfx('phase_4/audio/sfx/MG_cannon_adjust.ogg')
    if atkHit:
        reactIval = Parallel(
            ActorInterval(suit, 'pie-small-react'), 
            Sequence(
                LerpPosInterval(cannonHolder, 2.0, posFinal, startPos=posInit, blendType='easeInOut'), 
                Parallel(
                    LerpHprInterval(barrel, 0.6, Point3(0, 45, 0), startHpr=Point3(0, 90, 0), blendType='easeIn'), 
                    SoundInterval(soundCannonAdjust, duration=0.6)
                ), 
                Wait(2.0), 
                Parallel(
                    LerpHprInterval(barrel, 0.6, Point3(0, 90, 0), startHpr=Point3(0, 45, 0), blendType='easeIn'), 
                    SoundInterval(soundCannonAdjust, duration=0.6)
                ), 
                LerpPosInterval(cannonHolder, 1.0, posInit, startPos=posFinal, blendType='easeInOut')
            ), 
            Sequence(
                Parallel(
                    ActorInterval(suit, 'flail'), 
                    suit.scaleInterval(1.0, suitScale), 
                    LerpPosInterval(suit, 0.25, Point3(0, -1.0, 0.0)), 
                    Sequence(
                        Wait(0.25), 
                        Parallel(
                            SoundInterval(soundCogPanic), 
                            LerpPosInterval(suit, 1.5, Point3(0, -deep, 0.0), blendType='easeIn')
                        )
                    )
                ), 
                Wait(2.5), 
                Parallel(
                    SoundInterval(soundBomb), 
                    SoundInterval(soundFly), 
                    Sequence(
                        Func(smoke.show), 
                        Parallel(
                            LerpScaleInterval(smoke, 0.5, 3), 
                            LerpColorScaleInterval(smoke, 0.5, Vec4(2, 2, 2, 0))
                        ), 
                        Func(smoke.hide)
                    ), 
                    Sequence(
                        Func(kapow.show),
                        ActorInterval(kapow, 'kapow'), 
                        Func(kapow.hide)
                    ), 
                    LerpPosInterval(suit, 3.0, Point3(0, 150.0, 0.0)), 
                    suit.scaleInterval(3.0, 0.01)
                ), 
                Func(suit.hide)
            ),
            Sequence(
                Wait(7.5),
                Func(cannonHolder.removeNode)
            )
        )
    else:
        reactIval = Parallel(
            SoundInterval(soundCannonAdjust, duration=0.6), 
            Sequence(
                LerpPosInterval(cannonHolder, 2.0, posFinal, startPos=posInit, blendType='easeInOut'),  
                Parallel(                
                    Wait(2.0),
                    MovieUtil.createSuitTeaseMultiTrack(battle, suit)
                ),
                LerpPosInterval(cannonHolder, 1.0, posInit, startPos=posFinal, blendType='easeInOut')
            ),
            Sequence(
                Wait(5.5),
                Func(cannonHolder.removeNode)
            )
        )
    return reactIval
