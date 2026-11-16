from direct.interval.IntervalGlobal import *
from .BattleBase import *
from .BattleProps import *
from .BattleSounds import *
from . import MovieCamera
from direct.directnotify import DirectNotifyGlobal
from . import MovieUtil
from . import MovieNPCSOS
from .MovieUtil import calcAvgSuitPos
from toontown.toonbase import ToontownIntervals
from otp.otpbase.PythonUtil import cmp_to_key

notify = DirectNotifyGlobal.directNotify.newCategory('MovieDrop')
hitSoundFiles = ('AA_drop_flowerpot.ogg', 'AA_drop_sandbag.ogg', 
                 'AA_drop_anvil.ogg', 'AA_drop_bigweight.ogg', 
                 'AA_drop_safe.ogg', 'AA_drop_piano.ogg', 
                 'AA_drop_boat.ogg'
                 )
missSoundFiles = ('AA_drop_flowerpot_miss.ogg', 'AA_drop_sandbag_miss.ogg', 
                  'AA_drop_anvil_miss.ogg', 'AA_drop_bigweight_miss.ogg', 
                  'AA_drop_safe_miss.ogg', 'AA_drop_piano_miss.ogg', 
                  'AA_drop_boat_miss.ogg'
                  )
tDropShadow = 1.3
tSuitDodges = 2.45 + tDropShadow
tObjectAppears = 3.0 + tDropShadow
tButtonPressed = 2.44
dShrink = 0.3
dShrinkOnMiss = 0.1
dPropFall = 0.6
objects = ('flowerpot', 'sandbag', 'anvil', 'weight', 'safe', 'piano', 'ship')
objZOffsets = (0.75, 0.75, 0.0, 0.0, 0.0, 0.0, 0.0)
objStartingScales = (1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0)
landFrames = (12, 4, 1, 11, 11, 11, 2)
shoulderHeights = {'a': 13.28 / 4.0,
 'b': 13.74 / 4.0,
 'c': 10.02 / 4.0}


def doDrops(drops):
    if len(drops) == 0:
        return (None, None)
    npcArrivals, npcDepartures, npcs = MovieNPCSOS.doNPCTeleports(drops)
    suitDropsDict = {}
    groupDrops = []
    for drop in drops:
        track = drop['track']
        level = drop['level']
        targets = drop['target']
        if len(targets) == 1:
            suitId = targets[0]['suit'].doId
            if suitId in suitDropsDict:
                suitDropsDict[suitId].append((drop, targets[0]))
            else:
                suitDropsDict[suitId] = [(drop, targets[0])]
        elif level <= MAX_LEVEL_INDEX and attackAffectsGroup(track, level):
            groupDrops.append(drop)
        else:
            for target in targets:
                suitId = target['suit'].doId
                if suitId in suitDropsDict:
                    otherDrops = suitDropsDict[suitId]
                    alreadyInList = 0
                    for oDrop in otherDrops:
                        if oDrop[0]['toon'] == drop['toon']:
                            alreadyInList = 1

                    if alreadyInList == 0:
                        suitDropsDict[suitId].append((drop, target))
                else:
                    suitDropsDict[suitId] = [(drop, target)]

    suitDrops = list(suitDropsDict.values())

    def compFunc(a, b):
        if len(a) > len(b):
            return 1
        elif len(a) < len(b):
            return -1
        return 0

    suitDrops.sort(key=cmp_to_key(compFunc))
    delay = 0.0
    mtrack = Parallel(name='toplevel-drop')
    npcDrops = {}
    for st in suitDrops:
        if len(st) > 0:
            ival = __doSuitDrops(st, npcs, npcDrops)
            if ival:
                mtrack.append(Sequence(Wait(delay), ival))
            delay = delay + TOON_DROP_SUIT_DELAY

    dropTrack = Sequence(npcArrivals, mtrack, npcDepartures)
    camDuration = mtrack.getDuration()
    if groupDrops:
        ival = __doGroupDrops(groupDrops)
        dropTrack.append(ival)
        camDuration += ival.getDuration()
    enterDuration = npcArrivals.getDuration()
    exitDuration = npcDepartures.getDuration()
    camTrack = MovieCamera.chooseDropShot(drops, suitDropsDict, camDuration, enterDuration, exitDuration)
    return (dropTrack, camTrack)


def __getSoundTrack(level, hitSuit, node = None, cogDisguise = False):
    buttonDur = tButtonPressed
    if hitSuit:
        soundEffect = globalBattleSoundCache.getSound(hitSoundFiles[level])
    else:
        soundEffect = globalBattleSoundCache.getSound(missSoundFiles[level])
    soundTrack = Sequence()
    if soundEffect:
        buttonSound = globalBattleSoundCache.getSound('AA_drop_trigger_box.ogg')
        fallingSound = None
        if cogDisguise:
            buttonDelay = 1.0
            uberDelayHit = 1.2
            uberDelayMiss = 1.1
        else:
            buttonDelay = buttonDur - 0.3
            uberDelayHit = buttonDur
            uberDelayMiss = buttonDur - 0.1
        fallingDuration = 1.5
        if not level == UBER_GAG_LEVEL_INDEX:
            fallingSound = globalBattleSoundCache.getSound('incoming_whistleALT.ogg')
        soundTrack.append(Wait(buttonDelay))
        soundTrack.append(SoundInterval(buttonSound, duration=0.67, node=node))
        if fallingSound:
            soundTrack.append(SoundInterval(fallingSound, duration=fallingDuration, node=node))
        if not level == UBER_GAG_LEVEL_INDEX:
            soundTrack.append(SoundInterval(soundEffect, node=node))
        if level == UBER_GAG_LEVEL_INDEX:
            if hitSuit:
                uberDelay = uberDelayHit
            else:
                uberDelay = uberDelayMiss
            oldSoundTrack = soundTrack
            soundTrack = Parallel()
            soundTrack.append(oldSoundTrack)
            uberTrack = Sequence()
            uberTrack.append(Wait(uberDelay))
            uberTrack.append(SoundInterval(soundEffect, node=node))
            soundTrack.append(uberTrack)
    else:
        soundTrack.append(Wait(0.1))
    return soundTrack


def __doSuitDrops(dropTargetPairs, npcs, npcDrops):
    toonTracks = Parallel()
    delay = 0.0
    alreadyDodged = 0
    alreadyTeased = 0
    for dropTargetPair in dropTargetPairs:
        drop = dropTargetPair[0]
        level = drop['level']
        objName = objects[level]
        target = dropTargetPair[1]
        track = __dropObjectForSingle(drop, delay, objName, level, alreadyDodged, alreadyTeased, npcs, target, npcDrops)
        if track:
            toonTracks.append(track)
            delay += TOON_DROP_DELAY
        hp = target['hp']
        if hp <= 0:
            if level >= 3:
                alreadyTeased = 1
            else:
                alreadyDodged = 1

    return toonTracks


def __doGroupDrops(groupDrops):
    toonTracks = Parallel()
    delay = 0.0
    alreadyDodged = 0
    alreadyTeased = 0
    for drop in groupDrops:
        battle = drop['battle']
        level = drop['level']
        centerPos = calcAvgSuitPos(drop)
        targets = drop['target']
        numTargets = len(targets)
        closestTarget = -1
        nearestDistance = 100000.0
        for i in range(numTargets):
            suit = drop['target'][i]['suit']
            suitPos = suit.getPos(battle)
            displacement = Vec3(centerPos)
            displacement -= suitPos
            distance = displacement.lengthSquared()
            if distance < nearestDistance:
                closestTarget = i
                nearestDistance = distance

        track = __dropGroupObject(drop, delay, closestTarget, alreadyDodged, alreadyTeased)
        if track:
            toonTracks.append(track)
            delay = delay + TOON_DROP_SUIT_DELAY
        hp = drop['target'][closestTarget]['hp']
        if hp <= 0:
            if level >= 3:
                alreadyTeased = 1
            else:
                alreadyDodged = 1

    return toonTracks


def __dropGroupObject(drop, delay, closestTarget, alreadyDodged, alreadyTeased):
    level = drop['level']
    objName = objects[level]
    target = drop['target'][closestTarget]
    suit = drop['target'][closestTarget]['suit']
    npcDrops = {}
    npcs = []
    returnedParallel = __dropObject(drop, delay, objName, level, alreadyDodged, alreadyTeased, npcs, target, npcDrops)
    for i in range(len(drop['target'])):
        target = drop['target'][i]
        suitTrack = __createSuitTrack(drop, delay, level, alreadyDodged, alreadyTeased, target, npcs)
        if suitTrack:
            returnedParallel.append(suitTrack)

    return returnedParallel


def __dropObjectForSingle(drop, delay, objName, level, alreadyDodged, alreadyTeased, npcs, target, npcDrops):
    singleDropParallel = __dropObject(drop, delay, objName, level, alreadyDodged, alreadyTeased, npcs, target, npcDrops)
    suitTrack = __createSuitTrack(drop, delay, level, alreadyDodged, alreadyTeased, target, npcs)
    if suitTrack:
        singleDropParallel.append(suitTrack)
    return singleDropParallel


def __dropObject(drop, delay, objName, level, alreadyDodged, alreadyTeased, npcs, target, npcDrops):
    toon = drop['toon']
    repeatNPC = 0
    battle = drop['battle']
    if 'npc' in drop:
        toon = drop['npc']
        if toon in npcDrops:
            repeatNPC = 1
        else:
            npcDrops[toon] = 1
        origHpr = Vec3(0, 0, 0)
    else:
        origHpr = toon.getHpr(battle)
    hpbonus = drop['hpbonus']
    suit = target['suit']
    hp = target['hp']
    hitSuit = hp > 0
    died = target['died']
    leftSuits = target['leftSuits']
    rightSuits = target['rightSuits']
    kbbonus = target['kbbonus']
    suitPos = suit.getPos(battle)
    majorObject = level >= 3
    obj = globalPropPool.getProp(objName)
    objectType = globalPropPool.getPropType(objName)
    if objName == 'weight':
        obj.setScale(obj.getScale() * 0.75)
    elif objName == 'safe':
        obj.setScale(obj.getScale() * 0.85)
    node = obj.node()
    node.setBounds(OmniBoundingVolume())
    node.setFinal(1)
    if toon.getTransformationsIndex(0):
        buttonAnimTrack = MovieUtil.getSuitButtonAnimTrack(toon.suit)
        objDelay = 3.0
        shadowDelay = 1.2
        cogDisguise = True
    else:
        buttonAnimTrack = MovieUtil.getToonButtonAnimTrack(toon)
        objDelay = delay + tObjectAppears
        shadowDelay = delay + tButtonPressed
        cogDisguise = False
    soundTrack = __getSoundTrack(level, hitSuit, toon, cogDisguise=cogDisguise)
    toonTrack = Sequence()
    if repeatNPC == 0:
        toonTrack.append(Wait(delay))
        toonTrack.append(Func(toon.headsUp, battle, suitPos))
        toonTrack.append(buttonAnimTrack)
        toonTrack.append(Func(toon.setHpr, battle, origHpr))
    objectTrack = Sequence()

    def posObject(obj, suit, level, majorObject, miss, battle = battle):
        obj.reparentTo(battle)
        if battle.isSuitLured(suit):
            suitPos, suitHpr = battle.getActorPosHpr(suit)
            obj.setPos(suitPos)
            obj.setHpr(suitHpr)
            if level >= 3:
                obj.setY(obj.getY() + 2)
        else:
            obj.setPos(suit.getPos(battle))
            obj.setHpr(suit.getHpr(battle))
            if miss and level >= 3:
                obj.setY(obj.getY(battle) + 5)
        if not majorObject:
            if not miss:
                shoulderHeight = shoulderHeights[suit.getBodyType()] * suit.scale
                obj.setZ(obj.getPos(battle)[2] + shoulderHeight)
        obj.setZ(obj.getPos(battle)[2] + objZOffsets[level])

    objectTrack.append(Func(battle.movie.needRestoreRenderProp, obj))
    objInit = Func(posObject, obj, suit, level, majorObject, hp <= 0)
    objectTrack.append(Wait(objDelay))
    objectTrack.append(objInit)
    if hp > 0 or level == 1 or level == 2:
        if hasattr(obj, 'getAnimControls'):
            animProp = ActorInterval(obj, objName)
            shrinkProp = LerpScaleInterval(obj, dShrink, Point3(0.01, 0.01, 0.01), startScale=obj.getScale())
            objAnimShrink = ParallelEndTogether(animProp, shrinkProp)
            objectTrack.append(objAnimShrink)
        else:
            startingScale = objStartingScales[level]
            if objName == 'ship':
                targetLen = len(drop['target'])
                if targetLen >= 5:
                    scale = obj.getScale()
                    startingScale = LVector3f(scale[0], scale[1] + ((targetLen - 4) * 0.25), scale[2])
            object2 = MovieUtil.copyProp(obj)
            posObject(object2, suit, level, majorObject, hp <= 0)
            endingPos = object2.getPos()
            startPos = Point3(endingPos[0], endingPos[1], endingPos[2] + 5)
            startHpr = object2.getHpr()
            endHpr = Point3(startHpr[0] + 90, startHpr[1], startHpr[2])
            animProp = LerpPosInterval(obj, landFrames[level] / 24.0, endingPos, startPos=startPos)
            shrinkProp = LerpScaleInterval(obj, dShrink, Point3(0.01, 0.01, 0.01), startScale=startingScale)
            bounceProp = ToontownIntervals.createZBounce(obj, 2, endingPos, 0.5, 1.5)
            objAnimShrink = Sequence(Func(obj.setScale, startingScale), Func(obj.setH, endHpr[0]), animProp, bounceProp, Wait(1.5), shrinkProp)
            objectTrack.append(objAnimShrink)
            MovieUtil.removeProp(object2)
    elif hasattr(obj, 'getAnimControls'):
        animProp = ActorInterval(obj, objName, duration=landFrames[level] / 24.0)

        def poseProp(prop, animName, level):
            prop.pose(animName, landFrames[level])

        poseProp = Func(poseProp, obj, objName, level)
        wait = Wait(1.0)
        shrinkProp = LerpScaleInterval(obj, dShrinkOnMiss, Point3(0.01, 0.01, 0.01), startScale=obj.getScale())
        objectTrack.append(animProp)
        objectTrack.append(poseProp)
        objectTrack.append(wait)
        objectTrack.append(shrinkProp)
    else:
        startingScale = objStartingScales[level]
        if objName == 'ship':
            targetLen = len(drop['target'])
            if targetLen >= 5:
                scale = obj.getScale()
                startingScale = LVector3f(scale[0], scale[1] + ((targetLen - 4) * 0.25), scale[2])
        obj2 = MovieUtil.copyProp(obj)
        posObject(obj2, suit, level, majorObject, hp <= 0)
        endingPos = obj2.getPos()
        startPos = Point3(endingPos[0], endingPos[1], endingPos[2] + 5)
        startHpr = obj2.getHpr()
        endHpr = Point3(startHpr[0] + 90, startHpr[1], startHpr[2])
        animProp = LerpPosInterval(obj, landFrames[level] / 24.0, endingPos, startPos=startPos)
        shrinkProp = LerpScaleInterval(obj, dShrinkOnMiss, Point3(0.01, 0.01, 0.01), startScale=startingScale)
        bounceProp = ToontownIntervals.createZBounce(obj, 2, endingPos, 0.5, 1.5)
        objAnimShrink = Sequence(Func(obj.setScale, startingScale), Func(obj.setH, endHpr[0]), animProp, bounceProp, Wait(1.5), shrinkProp)
        objectTrack.append(objAnimShrink)
        MovieUtil.removeProp(obj2)
    objectTrack.append(Func(MovieUtil.removeProp, obj))
    objectTrack.append(Func(battle.movie.clearRenderProp, obj))
    dropShadow = MovieUtil.copyProp(suit.getShadowJoint())
    if level == 0:
        dropShadow.setScale(0.5)
    elif level <= 2:
        dropShadow.setScale(0.8)
    elif level == 3:
        dropShadow.setScale(2.0)
    elif level == 4:
        dropShadow.setScale(2.3)
    else:
        dropShadow.setScale(3.6)

    def posShadow(dropShadow = dropShadow, suit = suit, battle = battle, hp = hp, level = level):
        dropShadow.reparentTo(battle)
        if battle.isSuitLured(suit):
            suitPos, suitHpr = battle.getActorPosHpr(suit)
            dropShadow.setPos(suitPos)
            dropShadow.setHpr(suitHpr)
            if level >= 3:
                dropShadow.setY(dropShadow.getY() + 2)
        else:
            dropShadow.setPos(suit.getPos(battle))
            dropShadow.setHpr(suit.getHpr(battle))
            if hp <= 0 and level >= 3:
                dropShadow.setY(dropShadow.getY(battle) + 5)
        dropShadow.setZ(dropShadow.getZ() + 0.5)

    shadowTrack = Sequence(
        Wait(shadowDelay), 
        Func(battle.movie.needRestoreRenderProp, dropShadow), 
        Func(posShadow), 
        LerpScaleInterval(dropShadow, tObjectAppears - tButtonPressed, dropShadow.getScale(), startScale=Point3(0.01, 0.01, 0.01)), 
        Wait(0.3), 
        Func(MovieUtil.removeProp, dropShadow), 
        Func(battle.movie.clearRenderProp, dropShadow)
        )
    return Parallel(toonTrack, soundTrack, objectTrack, shadowTrack)


def __createSuitTrack(drop, delay, level, alreadyDodged, alreadyTeased, target, npcs):
    toon = drop['toon']
    if 'npc' in drop:
        toon = drop['npc']
    battle = drop['battle']
    majorObject = level >= 3
    suit = target['suit']
    hp = target['hp']
    hitSuit = hp > 0
    died = target['died']
    revived = target['revived']
    leftSuits = target['leftSuits']
    rightSuits = target['rightSuits']
    kbbonus = target['kbbonus']
    hpbonus = drop['hpbonus']
    if toon.getTransformationsIndex(0):
        reactionDelay = 3.0
        dodgeDelay = 2.0
    else:
        reactionDelay = delay + tObjectAppears
        dodgeDelay = delay + tSuitDodges
    if hp > 0:
        suitTrack = Sequence()
        showDamage = Func(suit.showHpText, -hp, openEnded=0)
        if majorObject:
            anim = 'flatten'
        else:
            anim = 'drop-react'
        suitReact = ActorInterval(suit, anim)
        suitTrack.append(Wait(reactionDelay))
        suitTrack.append(showDamage)
        suitTrack.append(Func(suit.updateHealthBar, hp))
        suitGettingHit = Parallel(suitReact)
        if level == UBER_GAG_LEVEL_INDEX:
            gotHitSound = globalBattleSoundCache.getSound('AA_drop_boat_cog.ogg')
            suitGettingHit.append(SoundInterval(gotHitSound, node=toon))
        suitTrack.append(suitGettingHit)
        bonusTrack = None
        if hpbonus > 0:
            bonusTrack = Sequence(
                Wait(reactionDelay + 0.75), 
                Func(suit.showHpText, -hpbonus, 1, openEnded=0),
                Func(suit.updateHealthBar, hpbonus)
                )
        if revived != 0:
            suitTrack.append(MovieUtil.createSuitReviveTrack(suit, battle, npcs))
        elif died != 0:
            suitTrack.append(MovieUtil.createSuitDeathTrack(suit, toon, battle, npcs))
        else:
            suitTrack.append(Func(suit.loop, 'neutral'))
        if bonusTrack != None:
            suitTrack = Parallel(suitTrack, bonusTrack)
    elif kbbonus == 0:
        if battle.isSuitLured(suit):
            anim = 'lured'
        else:
            anim = 'neutral'
        suitTrack = Sequence(
            Wait(reactionDelay), 
            Func(MovieUtil.indicateMissed, suit, 0.6), 
            Func(suit.loop, anim)
            )
    else:
        if alreadyDodged > 0:
            return
        if level >= 3:
            if alreadyTeased > 0:
                return
            else:
                suitTrack = MovieUtil.createSuitTeaseMultiTrack(battle, suit, delay=reactionDelay)
        else:
            suitTrack = MovieUtil.createSuitDodgeMultitrack(dodgeDelay, suit, leftSuits, rightSuits)
    return suitTrack
