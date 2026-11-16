from direct.interval.IntervalGlobal import *
from .BattleProps import *
from .BattleSounds import *
from direct.directnotify import DirectNotifyGlobal
from . import MovieCamera
import random
from . import MovieUtil
from . import BattleParticles
from . import HealJokes
from toontown.toonbase import TTLocalizer
from toontown.toonbase import ToontownBattleGlobals
from toontown.pets import Pet, PetTricks
from panda3d.toontown import *
notify = DirectNotifyGlobal.directNotify.newCategory('MoviePetSOS')


def doPetSOSs(PetSOSs):
    if len(PetSOSs) == 0:
        return (None, None)
    track = Sequence()
    for p in PetSOSs:
        ival = __doPetSOS(p)
        if ival:
            track.append(ival)

    camDuration = track.getDuration()
    camTrack = MovieCamera.chooseHealShot(PetSOSs, camDuration)
    return (track, camTrack)


def __doPetSOS(sos):
    return __healJuggle(sos)


def __healToon(toon, hp, gender, callerToonId, ineffective = 0):
    notify.debug('healToon() - toon: %d hp: %d ineffective: %d' % (toon.doId, hp, ineffective))
    nolaughter = 0
    if ineffective == 1:
        if callerToonId == toon.doId:
            laughter = TTLocalizer.MoviePetSOSTrickFail
        else:
            nolaughter = 1
    else:
        maxDam = ToontownBattleGlobals.AvPropDamage[0][1][0][1]
        if callerToonId == toon.doId:
            if gender == 1:
                laughter = TTLocalizer.MoviePetSOSTrickSucceedBoy
            else:
                laughter = TTLocalizer.MoviePetSOSTrickSucceedGirl
        elif hp >= maxDam - 1:
            laughter = random.choice(TTLocalizer.MovieHealLaughterHits2)
        else:
            laughter = random.choice(TTLocalizer.MovieHealLaughterHits1)
    if nolaughter == 0:
        toon.setChatAbsolute(laughter, CFSpeech | CFTimeout)
    if hp > 0 and toon.hp != None:
        toon.toonUp(hp)
    else:
        notify.debug('__healToon() - toon: %d hp: %d' % (toon.doId, hp))
    return


def __teleportIn(attack, pet, pos=Point3(0, 0, 0), hpr=Vec3(180.0, 0.0, 0.0)):
    ival = Sequence()
    if hasattr(pet, 'leashMode') and pet.leashMode:
        ival.append(Func(pet.lookAt, attack['battle']))
        ival.append(Parallel(LerpPosInterval(pet, 1.5, pos + Point3(0, -1.5, 0), fluid=True, other=attack['battle']),
                             Func(pet.loop, 'run')))
        ival.append(Func(pet.setHpr, attack['battle'], hpr))
    else:
        ival.append(Func(pet.reparentTo, attack['battle']))
        ival.append(Func(pet.setPos, pos))
        ival.append(Func(pet.setHpr, hpr))
        ival.append(pet.getTeleportInTrack())
    ival.append(Func(pet.loop, 'neutral'))
    return ival


def __teleportOut(pet):
    ival = Sequence()
    if hasattr(pet, 'leashMode') and pet.leashMode:
        ival.append(Func(pet.lookAt, pet.getPos()))
        ival.append(Parallel(LerpPosInterval(pet, 1.5, pet.getPos(), fluid=True),
                             Func(pet.loop, 'run')))
        ival.append(Func(pet.setHpr, pet.getHpr()))
        ival.append(Func(pet.loop, 'neutral'))
    else:
        ival.append(pet.getTeleportOutTrack())
        ival.append(Func(pet.detachNode))
    return ival


def __healJuggle(heal):
    petProxyId = heal['petId']
    gender = 0
    if petProxyId in base.cr.doId2do:
        petProxy = base.cr.doId2do[petProxyId]
        if not petProxy:
            return
        if not isinstance(petProxy, Pet.Pet):
            pet = Pet.Pet()
            pet.setDNA(petProxy.style)
            pet.setName(petProxy.petName)
            pet.setPickable(0)
            pet.addActive()
        else:
            pet = petProxy
        gender = petProxy.gender
    else:
        pet = Pet.Pet()
        pet.setDNA([-1,
         0,
         0,
         -1,
         2,
         0,
         4,
         0,
         1])
        pet.setName('Smiley')
    targets = heal['target']
    ineffective = heal['sidestep']
    level = heal['level']
    track = Sequence(__teleportIn(heal, pet))
    if ineffective:
        trickTrack = Parallel(Wait(1.0), Func(pet.loop, 'neutralSad'), Func(pet.showMood, 'confusion'))
    else:
        if not hasattr(pet, 'leashMode'):
            playProjectileIval = True
        else:
            playProjectileIval = False
        trickTrack = PetTricks.getTrickIval(pet, level, playProjectileIval)
    track.append(trickTrack)
    first = 1
    targetTrack = Sequence()
    for target in targets:
        targetToon = target['toon']
        hp = target['hp']
        callerToonId = heal['toonId']
        reactIval = Func(__healToon, targetToon, hp, gender, callerToonId, ineffective)
        if first == 1:
            first = 0
        targetTrack.append(reactIval)

    mtrack = Parallel(Wait(2.0), targetTrack)
    track.append(mtrack)
    track.append(Sequence(Func(pet.clearMood)))
    if hasattr(pet, 'leashMode') and pet.leashMode:
        track.append(Func(pet.handleMoodChange))
    track.append(__teleportOut(pet))
    for target in targets:
        targetToon = target['toon']
        track.append(Func(targetToon.clearChat))
    if not hasattr(pet, 'leashMode'):
        track.append(Func(pet.removeActive))
        track.append(Func(pet.delete))
    return track
