from panda3d.core import *
from direct.interval.IntervalGlobal import *
from .BattleBase import *
from .BattleProps import *
from .BattleSounds import *
from toontown.toon.ToonDNA import *
from toontown.suit.SuitDNA import *
from direct.directnotify import DirectNotifyGlobal
import random
from . import MovieCamera
from . import MovieUtil
from .MovieUtil import calcAvgSuitPos
from otp.otpbase.PythonUtil import cmp_to_key
from . import MovieNPCSOS
notify = DirectNotifyGlobal.directNotify.newCategory('MovieThrow')
hitSoundFiles = ('AA_tart_only.ogg', 'AA_slice_only.ogg', 'AA_slice_only.ogg', 'AA_slice_only.ogg', 'AA_slice_only.ogg', 'AA_wholepie_only.ogg', 'AA_wholepie_only.ogg')
tPieLeavesHand = 2.7
tPieHitsSuit = 3.0
tSuitDodges = 2.45
ratioMissToHit = 1.5
tPieShrink = 0.7
pieFlyTaskName = 'MovieThrow-pieFly'


def addHit(dict, suitId, hitCount):
    if suitId in dict:
        dict[suitId] += hitCount
    else:
        dict[suitId] = hitCount


def doThrows(throws):
    if len(throws) == 0:
        return (None, None)

    npcArrivals, npcDepartures, npcs = MovieNPCSOS.doNPCTeleports(throws)
    suitThrowsDict = {}
    for throw in throws:
        if attackAffectsGroup(throw['track'], throw['level']):
            pass
        else:
            suitId = throw['target']['suit'].doId
            if suitId in suitThrowsDict:
                suitThrowsDict[suitId].append(throw)
            else:
                suitThrowsDict[suitId] = [throw]

    suitThrows = list(suitThrowsDict.values())

    def compFunc(a, b):
        if len(a) > len(b):
            return 1
        elif len(a) < len(b):
            return -1
        return 0

    suitThrows.sort(key=cmp_to_key(compFunc))
    totalHitDict = {}
    singleHitDict = {}
    groupHitDict = {}
    for throw in throws:
        if attackAffectsGroup(throw['track'], throw['level']):
            for i in range(len(throw['target'])):
                target = throw['target'][i]
                suitId = target['suit'].doId
                if target['hp'] > 0:
                    addHit(groupHitDict, suitId, 1)
                    addHit(totalHitDict, suitId, 1)
                else:
                    addHit(groupHitDict, suitId, 0)
                    addHit(totalHitDict, suitId, 0)

        else:
            suitId = throw['target']['suit'].doId
            if throw['target']['hp'] > 0:
                addHit(singleHitDict, suitId, 1)
                addHit(totalHitDict, suitId, 1)
            else:
                addHit(singleHitDict, suitId, 0)
                addHit(totalHitDict, suitId, 0)

    notify.debug('singleHitDict = %s' % singleHitDict)
    notify.debug('groupHitDict = %s' % groupHitDict)
    notify.debug('totalHitDict = %s' % totalHitDict)
    delay = 0.0
    mtrack = Parallel()
    for st in suitThrows:
        if len(st) > 0:
            ival = __doSuitThrows(st, npcs)
            if ival:
                mtrack.append(Sequence(Wait(delay), ival))
            delay = delay + TOON_THROW_SUIT_DELAY

    retTrack = Sequence()
    retTrack.append(mtrack)
    groupThrowIvals = Parallel()
    groupThrows = []
    for throw in throws:
        if attackAffectsGroup(throw['track'], throw['level']):
            groupThrows.append(throw)

    for throw in groupThrows:
        tracks = None
        tracks = __throwGroupPie(throw, 0, groupHitDict, npcs)
        if tracks:
            for track in tracks:
                groupThrowIvals.append(track)

    retTrack.append(groupThrowIvals)
    retTrack = Sequence(npcArrivals, retTrack, npcDepartures)
    camDuration = retTrack.getDuration()
    enterDuration = npcArrivals.getDuration()
    exitDuration = npcDepartures.getDuration()
    camTrack = MovieCamera.chooseThrowShot(throws, suitThrowsDict, camDuration, enterDuration, exitDuration)
    return (retTrack, camTrack)


def __doSuitThrows(throws, npcs):
    toonTracks = Parallel()
    delay = 0.0
    hitCount = 0
    for throw in throws:
        if throw['target']['hp'] > 0:
            hitCount += 1
        else:
            break

    for throw in throws:
        tracks = throwPie(throw, delay, hitCount, npcs)
        if tracks:
            for track in tracks:
                toonTracks.append(track)

        delay = delay + TOON_THROW_DELAY

    return toonTracks


def __showProp(prop, parent, pos):
    prop.reparentTo(parent)
    prop.setPos(pos)


def __animProp(prop, propName, propType):
    if 'actor' == propType:
        prop.play(propName)
    elif 'model' == propType:
        pass
    else:
        notify.error(f'No such propType as: {propType}')


def __billboardProp(prop):
    scale = prop.getScale()
    prop.setBillboardPointWorld()
    prop.setScale(scale)


def __suitMissPoint(suit, other = render):
    pnt = suit.getPos(other)
    pnt.setZ(pnt[2] + suit.getHeight() * 1.3)
    return pnt


def __propPreflight(prop, suit, toon, battle):
    gag = prop
    toon.update(0)
    gag.wrtReparentTo(battle)
    for ci in range(gag.getNumChildren()):
        gag.getChild(ci).setHpr(0, -90, 0)

    targetPnt = MovieUtil.avatarFacePoint(suit, other=battle)
    gag.lookAt(targetPnt)


def __propPreflightGroup(prop, suits, toon, battle):
    gag = prop
    toon.update(0)
    prop.wrtReparentTo(battle)
    for ci in range(gag.getNumChildren()):
        gag.getChild(ci).setHpr(0, -90, 0)

    avgTargetPt = Point3(0, 0, 0)
    for suit in suits:
        avgTargetPt += MovieUtil.avatarFacePoint(suit, other=battle)

    avgTargetPt /= len(suits)
    gag.lookAt(avgTargetPt)


def __piePreMiss(missDict, pie, suitPoint, other = render):
    missDict['pie'] = pie
    missDict['startScale'] = pie.getScale()
    missDict['startPos'] = pie.getPos(other)
    v = Vec3(suitPoint - missDict['startPos'])
    endPos = missDict['startPos'] + v * ratioMissToHit
    missDict['endPos'] = endPos


def __pieMissLerpCallback(t, missDict):
    pie = missDict['pie']
    newPos = missDict['startPos'] * (1.0 - t) + missDict['endPos'] * t
    if t < tPieShrink:
        tScale = 0.0001
    else:
        tScale = (t - tPieShrink) / (1.0 - tPieShrink)
    newScale = missDict['startScale'] * max(1.0 - tScale, 0.01)
    pie.setPos(newPos)
    pie.setScale(newScale)


def __piePreMissGroup(missDict, pies, suitPoint, other = render):
    missDict['pies'] = pies
    missDict['startScale'] = pies[0].getScale()
    missDict['startPos'] = pies[0].getPos(other)
    v = Vec3(suitPoint - missDict['startPos'])
    endPos = missDict['startPos'] + v * ratioMissToHit
    missDict['endPos'] = endPos
    notify.debug('startPos=%s' % missDict['startPos'])
    notify.debug(f'v={v}')
    notify.debug('endPos=%s' % missDict['endPos'])


def __pieMissGroupLerpCallback(t, missDict):
    pies = missDict['pies']
    newPos = missDict['startPos'] * (1.0 - t) + missDict['endPos'] * t
    if t < tPieShrink:
        tScale = 0.0001
    else:
        tScale = (t - tPieShrink) / (1.0 - tPieShrink)
    newScale = missDict['startScale'] * max(1.0 - tScale, 0.01)
    for pie in pies:
        if not pie.isEmpty():
            pie.setPos(newPos)
            pie.setScale(newScale)


def __getWeddingCakeSoundTrack(level, hitSuit, node = None):
    throwTrack = Sequence()
    if hitSuit:
        throwSound = globalBattleSoundCache.getSound('AA_throw_wedding_cake.ogg')
        songTrack = Sequence()
        songTrack.append(Wait(1.0))
        songTrack.append(SoundInterval(throwSound, node=node))
        splatSound = globalBattleSoundCache.getSound('AA_throw_wedding_cake_cog.ogg')
        splatTrack = Sequence()
        splatTrack.append(Wait(tPieHitsSuit))
        splatTrack.append(SoundInterval(splatSound, node=node))
        throwTrack.append(Parallel(songTrack, splatTrack))
    else:
        throwSound = globalBattleSoundCache.getSound('AA_throw_wedding_cake_miss.ogg')
        throwTrack.append(Wait(tSuitDodges))
        throwTrack.append(SoundInterval(throwSound, node=node))
    return throwTrack


def __getSoundTrack(level, hitSuit, node = None):
    if level == UBER_GAG_LEVEL_INDEX:
        return __getWeddingCakeSoundTrack(level, hitSuit, node)
    throwSound = globalBattleSoundCache.getSound('AA_pie_throw_only.ogg')
    throwTrack = Sequence(Wait(2.6), SoundInterval(throwSound, node=node))
    if hitSuit:
        hitSound = globalBattleSoundCache.getSound(hitSoundFiles[level])
        hitTrack = Sequence(Wait(tPieLeavesHand), SoundInterval(hitSound, node=node))
        return Parallel(throwTrack, hitTrack)
    else:
        return throwTrack


def throwPie(throw, delay, hitCount, npcs=None):
    toon = throw['toon']
    if 'npc' in throw:
        toon = throw['npc']
    hpbonus = throw['hpbonus']
    target = throw['target']
    suit = target['suit']
    if not hasattr(suit, 'updateHealthBar'):
        suitGeom = target['suitGeom']
    else:
        suitGeom = suit
    hp = target['hp']
    kbbonus = target['kbbonus']
    sidestep = throw['sidestep']
    died = target['died']
    revived = target['revived']
    leftSuits = target['leftSuits']
    rightSuits = target['rightSuits']
    level = throw['level']
    battle = throw['battle']
    origHpr = toon.getHpr(battle)
    suitPos = suit.getPos(battle)

    if hasattr(suit, 'doId'):
        notify.debug(f'toon: {toon.getName()} throws tart at suit: {suit.doId} for hp: {hp} died: {died}')

    pieName = pieNames[level]
    hitSuit = hp > 0
    pie = globalPropPool.getProp(pieName)
    pieType = globalPropPool.getPropType(pieName)
    splatName = f'splat-{pieName}'
    splat = globalPropPool.getProp(splatName)
    splatType = globalPropPool.getPropType(splatName)

    pieShow, throwAnim, neutralAnim = playThrowTransformedAnim(toon, pie)
    toonTrack = Sequence()
    toonFace = Func(toon.headsUp, battle, suitPos)
    toonTrack.append(Wait(delay))
    toonTrack.append(toonFace)
    toonTrack.append(throwAnim)
    toonTrack.append(neutralAnim)

    if 'npc' not in throw:
        toonTrack.append(Func(toon.setHpr, battle, origHpr))

    pieAnim = Func(__animProp, pie, pieName, pieType)
    pieScale = LerpScaleInterval(pie, 1.0, pie.getScale(), startScale=MovieUtil.PNT3_NEARZERO)

    node = battle
    if not hasattr(suit, 'updateHealthBar'):
        node = render

    piePreflight = Func(__propPreflight, pie, suit, toon, node)
    pieTrack = Sequence(
        Wait(delay), 
        pieShow, 
        pieAnim, 
        pieScale, 
        Func(battle.movie.needRestoreRenderProp, pie), 
        Wait(tPieLeavesHand - 1.0), 
        piePreflight
    )

    soundTrack = __getSoundTrack(level, hitSuit, toon)
    if hitSuit:
        position = MovieUtil.avatarFacePoint(suit, other=battle)
        if not hasattr(suit, 'updateHealthBar'):
            position = (25.481, 16.850, 2.057)
        pieFly = LerpPosInterval(pie, tPieHitsSuit - tPieLeavesHand, pos=position, name=pieFlyTaskName, other=battle)
        pieHide = Func(MovieUtil.removeProp, pie)
        splatShow = Func(__showProp, splat, suit, Point3(0, 0, suit.getHeight()))
        splatBillboard = Func(__billboardProp, splat)
        splatAnim = ActorInterval(splat, splatName)
        splatHide = Func(MovieUtil.removeProp, splat)
        pieTrack.append(pieFly)
        pieTrack.append(pieHide)
        pieTrack.append(Func(battle.movie.clearRenderProp, pie))
        pieTrack.append(splatShow)
        pieTrack.append(splatBillboard)
        pieTrack.append(splatAnim)
        pieTrack.append(splatHide)
    else:
        missDict = {}
        if sidestep:
            suitPoint = MovieUtil.avatarFacePoint(suit, other=battle)
        else:
            suitPoint = __suitMissPoint(suit, other=battle)
        piePreMiss = Func(__piePreMiss, missDict, pie, suitPoint, battle)
        pieMiss = LerpFunctionInterval(__pieMissLerpCallback, extraArgs=[missDict], duration=(tPieHitsSuit - tPieLeavesHand) * ratioMissToHit)
        pieHide = Func(MovieUtil.removeProp, pie)
        pieTrack.append(piePreMiss)
        pieTrack.append(pieMiss)
        pieTrack.append(pieHide)
        pieTrack.append(Func(battle.movie.clearRenderProp, pie))
    if hitSuit:
        suitResponseTrack = Sequence()
        showDamage = Func(suitGeom.showHpText, -hp, openEnded=0, attackTrack=THROW_TRACK)
        sival = []
        if kbbonus > 0:
            suitPos, suitHpr = battle.getActorPosHpr(suit)
            suitType = getSuitBodyType(suitGeom.getStyleName())
            animTrack = Sequence()
            animTrack.append(ActorInterval(suitGeom, 'pie-small-react', duration=0.2))
            if suitType == 'a':
                animTrack.append(ActorInterval(suitGeom, 'slip-forward', startTime=2.43))
            elif suitType == 'b':
                animTrack.append(ActorInterval(suitGeom, 'slip-forward', startTime=1.94))
            elif suitType == 'c':
                animTrack.append(ActorInterval(suitGeom, 'slip-forward', startTime=2.58))
            animTrack.append(Func(battle.unlureSuit, suit))
            moveTrack = Sequence(Wait(0.2), LerpPosInterval(suit, 0.6, pos=suitPos, other=battle))
            sival = Parallel(animTrack, moveTrack)
        elif hitCount == 1:
            sival = Parallel(ActorInterval(suitGeom, 'pie-small-react'), MovieUtil.createSuitStunInterval(suitGeom, 0.3, 1.3))
        else:
            sival = ActorInterval(suitGeom, 'pie-small-react')
        suitResponseTrack.append(Wait(delay + tPieHitsSuit))
        suitResponseTrack.append(showDamage)
        suitResponseTrack.append(Func(suitGeom.updateHealthBar, hp))
        suitResponseTrack.append(sival)
        bonusTrack = Sequence(Wait(delay + tPieHitsSuit))
        if kbbonus > 0:
            bonusTrack.append(Wait(0.75))
            bonusTrack.append(Func(suitGeom.showHpText, -kbbonus, 2, openEnded=0, attackTrack=THROW_TRACK))
            bonusTrack.append(Func(suitGeom.updateHealthBar, kbbonus))
        if hpbonus > 0:
            bonusTrack.append(Wait(0.75))
            bonusTrack.append(Func(suitGeom.showHpText, -hpbonus, 1, openEnded=0, attackTrack=THROW_TRACK))
            bonusTrack.append(Func(suitGeom.updateHealthBar, hpbonus))
        if revived != 0:
            suitResponseTrack.append(MovieUtil.createSuitReviveTrack(suitGeom, battle, npcs))
        elif died != 0:
            suitResponseTrack.append(MovieUtil.createSuitDeathTrack(suitGeom, toon, battle, npcs))
        else:
            suitResponseTrack.append(Func(suit.loop, 'neutral'))
        suitResponseTrack = Parallel(suitResponseTrack, bonusTrack)
    else:
        suitResponseTrack = MovieUtil.createSuitDodgeMultitrack(delay + tSuitDodges, suitGeom, leftSuits, rightSuits)
    if not hitSuit and delay > 0:
        return [toonTrack, soundTrack, pieTrack]
    else:
        return [toonTrack,
         soundTrack,
         pieTrack,
         suitResponseTrack]


def __createWeddingCakeFlight(throw, groupHitDict, pie):
    toon = throw['toon']
    battle = throw['battle']
    level = throw['level']
    sidestep = throw['sidestep']
    hpbonus = throw['hpbonus']
    numTargets = len(throw['target'])
    pieName = pieNames[level]
    splatName = f'splat-{pieName}'
    if pieName == 'wedding-cake':
        splatName = 'splat-birthday-cake'
    splat = globalPropPool.getProp(splatName)
    splats = [splat]
    for i in range(numTargets - 1):
        splats.append(MovieUtil.copyProp(splat))

    splatType = globalPropPool.getPropType(splatName)
    cakePartStrs = ['cake1',
     'cake2',
     'cake3',
     'caketop']
    cakeParts = []
    for part in cakePartStrs:
        cakeParts.append(pie.find(f'**/{part}'))

    cakePartDivisions = {}
    cakePartDivisions[1] = [[cakeParts[0], cakeParts[1], cakeParts[2], cakeParts[3]]]
    cakePartDivisions[2] = [[cakeParts[0], cakeParts[1]], [cakeParts[2], cakeParts[3]]]
    cakePartDivisions[3] = [[cakeParts[0], cakeParts[1]], [cakeParts[2]], [cakeParts[3]]]
    cakePartDivisions[4] = [[cakeParts[0]], [cakeParts[1]], [cakeParts[2]], [cakeParts[3]]]
    cakePartDivisions[5] = [[cakeParts[0]], [cakeParts[1]], [cakeParts[2]], [cakeParts[3]], [cakeParts[0]]]
    cakePartDivisions[6] = [[cakeParts[0]], [cakeParts[1]], [cakeParts[2]], [cakeParts[3]], [cakeParts[0]], [cakeParts[1]]]
    cakePartDivisions[7] = [[cakeParts[0]], [cakeParts[1]], [cakeParts[2]], [cakeParts[3]], [cakeParts[0]], [cakeParts[1]], [cakeParts[2]]]
    cakePartDivisions[8] = [[cakeParts[0]], [cakeParts[1]], [cakeParts[2]], [cakeParts[3]], [cakeParts[0]], [cakeParts[1]], [cakeParts[2]], [cakeParts[3]]]
    cakePartDivToUse = cakePartDivisions[len(throw['target'])]
    groupPieTracks = Parallel()
    for i in range(numTargets):
        target = throw['target'][i]
        suit = target['suit']
        hitSuit = target['hp'] > 0
        singlePieTrack = Sequence()
        if hitSuit:
            piePartReparent = Func(reparentCakePart, pie, cakePartDivToUse[i])
            singlePieTrack.append(piePartReparent)
            cakePartTrack = Parallel()
            for cakePart in cakePartDivToUse[i]:
                pieFly = LerpPosInterval(cakePart, tPieHitsSuit - tPieLeavesHand, pos=MovieUtil.avatarFacePoint(suit, other=battle), name=pieFlyTaskName, other=battle)
                cakePartTrack.append(pieFly)

            singlePieTrack.append(cakePartTrack)
            pieRemoveCakeParts = Func(MovieUtil.removeProps, cakePartDivToUse[i])
            pieHide = Func(MovieUtil.removeProp, pie)
            splatShow = Func(__showProp, splats[i], suit, Point3(0, 0, suit.getHeight()))
            splatBillboard = Func(__billboardProp, splats[i])
            splatAnim = ActorInterval(splats[i], splatName)
            splatHide = Func(MovieUtil.removeProp, splats[i])
            singlePieTrack.append(pieRemoveCakeParts)
            singlePieTrack.append(pieHide)
            singlePieTrack.append(Func(battle.movie.clearRenderProp, pie))
            singlePieTrack.append(splatShow)
            singlePieTrack.append(splatBillboard)
            singlePieTrack.append(splatAnim)
            singlePieTrack.append(splatHide)
        else:
            missDict = {}
            if sidestep:
                suitPoint = MovieUtil.avatarFacePoint(suit, other=battle)
            else:
                suitPoint = __suitMissPoint(suit, other=battle)
            piePartReparent = Func(reparentCakePart, pie, cakePartDivToUse[i])
            piePreMiss = Func(__piePreMissGroup, missDict, cakePartDivToUse[i], suitPoint, battle)
            pieMiss = LerpFunctionInterval(__pieMissGroupLerpCallback, extraArgs=[missDict], duration=(tPieHitsSuit - tPieLeavesHand) * ratioMissToHit)
            pieHide = Func(MovieUtil.removeProp, pie)
            pieRemoveCakeParts = Func(MovieUtil.removeProps, cakePartDivToUse[i])
            singlePieTrack.append(piePartReparent)
            singlePieTrack.append(piePreMiss)
            singlePieTrack.append(pieMiss)
            singlePieTrack.append(pieRemoveCakeParts)
            singlePieTrack.append(pieHide)
            singlePieTrack.append(Func(battle.movie.clearRenderProp, pie))
        groupPieTracks.append(singlePieTrack)

    return groupPieTracks


def __throwGroupPie(throw, delay, groupHitDict, npcs):
    toon = throw['toon']
    if 'npc' in throw:
        toon = throw['npc']
    level = throw['level']
    sidestep = throw['sidestep']
    hpbonus = throw['hpbonus']
    numTargets = len(throw['target'])
    avgSuitPos = calcAvgSuitPos(throw)
    battle = throw['battle']
    origHpr = toon.getHpr(battle)
    pieName = pieNames[level]
    pie = globalPropPool.getProp(pieName)
    pieType = globalPropPool.getPropType(pieName)
    pieShow, throwAnim, neutralAnim = playThrowTransformedAnim(toon, pie)
    toonTrack = Sequence()
    toonFace = Func(toon.headsUp, battle, avgSuitPos)
    toonTrack.append(Wait(delay))
    toonTrack.append(toonFace)
    toonTrack.append(throwAnim)
    toonTrack.append(neutralAnim)

    if 'npc' not in throw:
        toonTrack.append(Func(toon.setHpr, battle, origHpr))
    suits = []
    for i in range(numTargets):
        suits.append(throw['target'][i]['suit'])

    pieAnim = Func(__animProp, pie, pieName, pieType)
    pieScale = LerpScaleInterval(pie, 1.0, pie.getScale() * 1.5, startScale=MovieUtil.PNT3_NEARZERO)
    piePreflight = Func(__propPreflightGroup, pie, suits, toon, battle)
    pieTrack = Sequence(
        Wait(delay), 
        pieShow, 
        pieAnim, 
        pieScale, 
        Func(battle.movie.needRestoreRenderProp, pie), 
        Wait(tPieLeavesHand - 1.0), 
        piePreflight
    )
    if level == UBER_GAG_LEVEL_INDEX:
        groupPieTracks = __createWeddingCakeFlight(throw, groupHitDict, pie)
    else:
        notify.error(f'unhandled throw level {level}')
    pieTrack.append(groupPieTracks)
    didThrowHitAnyone = False
    for i in range(numTargets):
        target = throw['target'][i]
        hitSuit = target['hp'] > 0
        if hitSuit:
            didThrowHitAnyone = True

    soundTrack = __getSoundTrack(level, didThrowHitAnyone, toon)
    groupSuitResponseTrack = Parallel()
    for i in range(numTargets):
        target = throw['target'][i]
        suit = target['suit']
        hitSuit = target['hp'] > 0
        leftSuits = target['leftSuits']
        rightSuits = target['rightSuits']
        hp = target['hp']
        kbbonus = target['kbbonus']
        died = target['died']
        revived = target['revived']
        if hitSuit:
            singleSuitResponseTrack = Sequence()
            showDamage = Func(suit.showHpText, -hp, openEnded=0, attackTrack=THROW_TRACK)
            sival = []
            if kbbonus > 0:
                suitPos, suitHpr = battle.getActorPosHpr(suit)
                suitType = getSuitBodyType(suit.getStyleName())
                animTrack = Sequence()
                animTrack.append(ActorInterval(suit, 'pie-small-react', duration=0.2))
                if suitType == 'a':
                    animTrack.append(ActorInterval(suit, 'slip-forward', startTime=2.43))
                elif suitType == 'b':
                    animTrack.append(ActorInterval(suit, 'slip-forward', startTime=1.94))
                elif suitType == 'c':
                    animTrack.append(ActorInterval(suit, 'slip-forward', startTime=2.58))
                animTrack.append(Func(battle.unlureSuit, suit))
                moveTrack = Sequence(Wait(0.2), LerpPosInterval(suit, 0.6, pos=suitPos, other=battle))
                sival = Parallel(animTrack, moveTrack)
            elif groupHitDict[suit.doId] == 1:
                sival = Parallel(ActorInterval(suit, 'pie-small-react'), MovieUtil.createSuitStunInterval(suit, 0.3, 1.3))
            else:
                sival = ActorInterval(suit, 'pie-small-react')
            singleSuitResponseTrack.append(Wait(delay + tPieHitsSuit))
            singleSuitResponseTrack.append(showDamage)
            singleSuitResponseTrack.append(Func(suit.updateHealthBar, hp))
            singleSuitResponseTrack.append(sival)
            bonusTrack = Sequence(Wait(delay + tPieHitsSuit))
            if kbbonus > 0:
                bonusTrack.append(Wait(0.75))
                bonusTrack.append(Func(suit.showHpText, -kbbonus, 2, openEnded=0, attackTrack=THROW_TRACK))
                bonusTrack.append(Func(suit.updateHealthBar, kbbonus))
            if hpbonus > 0:
                bonusTrack.append(Wait(0.75))
                bonusTrack.append(Func(suit.showHpText, -hpbonus, 1, openEnded=0, attackTrack=THROW_TRACK))
                bonusTrack.append(Func(suit.updateHealthBar, hpbonus))
            if revived != 0:
                singleSuitResponseTrack.append(MovieUtil.createSuitReviveTrack(suit, battle, npcs))
            elif died != 0:
                singleSuitResponseTrack.append(MovieUtil.createSuitDeathTrack(suit, toon, battle, npcs))
            else:
                singleSuitResponseTrack.append(Func(suit.loop, 'neutral'))
            singleSuitResponseTrack = Parallel(singleSuitResponseTrack, bonusTrack)
        else:
            groupHitValues = list(groupHitDict.values())
            if groupHitValues.count(0) == len(groupHitValues):
                singleSuitResponseTrack = MovieUtil.createSuitDodgeMultitrack(delay + tSuitDodges, suit, leftSuits, rightSuits)
            else:
                singleSuitResponseTrack = Sequence(Wait(tPieHitsSuit - 0.1), Func(MovieUtil.indicateMissed, suit, 1.0))
        groupSuitResponseTrack.append(singleSuitResponseTrack)

    return [toonTrack,
     pieTrack,
     soundTrack,
     groupSuitResponseTrack]


def playThrowTransformedAnim(toon, pie):
    if toon.getTransformationsIndex(0):
        pieShow = Func(MovieUtil.showProp, pie, toon.suit.rightHand)
        pie.setPosHpr(0, 0, 0, 0, 180, 0)
        if toon.suit.getBodyType() == 'c':
            throwAnim = ActorInterval(toon.suit, 'throw-paper', playRate=0.9)
        else:
            throwAnim = ActorInterval(toon.suit, 'throw-object', playRate=1.15)
        neutralAnim = Func(toon.suit.loop, 'neutral')
    else:
        pieShow = Func(MovieUtil.showProp, pie, toon.rightHand)
        throwAnim = ActorInterval(toon, 'throw')
        neutralAnim = Func(toon.loop, 'neutral')
    return pieShow, throwAnim, neutralAnim


def reparentCakePart(pie, cakeParts):
    pieParent = pie.getParent()
    notify.debug(f'pieParent = {pieParent}')
    for cakePart in cakeParts:
        cakePart.wrtReparentTo(pieParent)
