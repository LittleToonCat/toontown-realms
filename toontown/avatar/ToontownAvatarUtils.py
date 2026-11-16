from panda3d.core import CollisionTube, CollisionNode
from panda3d.toontown import NametagGroup
from toontown.char import Char, CharDNA
from toontown.pets import Pet
from toontown.suit import SuitDNA, Suit
from toontown.toon import NPCToons, Toon, ToonDNA
from toontown.toonbase import TTLocalizer
from toontown.toonbase import ToontownGlobals


def createToon(toonId, x=0, y=0, z=0, h=0, p=0, r=0, parent=render, anim='neutral', LOD=1000,
               isDisguised=False, suitType='f', coll=True):
    newToon = NPCToons.createLocalNPC(toonId)
    if not newToon:
        newToon = NPCToons.createLocalNPC(1)
    newToon.head = newToon.find('**/__Actor_head')
    if isDisguised:
        newToon.putOnSuit(suitType, False, False)
        if coll:
            collTube = CollisionTube(0, 0, 0.5, 0, 0, 4, 2)
            collNode = CollisionNode('suit')
            collNode.addSolid(collTube)
            newToon.attachNewNode(collNode)
    else:
        newToon.useLOD(LOD)
        if coll:
            newToon.initializeBodyCollisions('toon')
    newToon.setPosHpr(x, y, z, h, p, r)
    newToon.reparentTo(parent)
    newToon.loop(anim)
    return newToon


def createUniqueToon(name, dna, hat = (0, 0, 0), glasses = (0, 0, 0), backpack = (0, 0, 0), shoes = (0, 0, 0),
                     x=0, y=0, z=0, h=0, p=0, r=0,
                     parent=render, anim='neutral', LOD=1000, isDisguised=False, suitType='f', suitDept='c',
                     isWaiter=False, isRental=False, coll=True, colorType=NametagGroup.CCNonPlayer,
                     cogLevels=(0, 0, 0, 0, 0), cheesyEffect=ToontownGlobals.CENormal, nametagStyle=100) -> Toon:
    newToon = Toon.Toon()

    newToon.setPickable(0)
    newToon.setPlayerType(colorType)
    if nametagStyle == 100:
        font = loader.loadFont(TTLocalizer.InterfaceFont)
    else:
        font = loader.loadFont(TTLocalizer.NametagFonts[nametagStyle])
    newToon.setFont(font, False)
    newToon.setName(name)
    if isinstance(dna, ToonDNA.ToonDNA):
        newToon.setDNA(dna)
    else:
        newDNA = ToonDNA.ToonDNA()
        newDNA.newToonFromProperties(*dna)
        newToon.setDNAString(newDNA.makeNetString())
    newToon.applyCheesyEffect(cheesyEffect, 0)
    newToon.head = newToon.find('**/__Actor_head')
    newToon.setHat(*hat)
    newToon.setBackpack(*backpack)
    newToon.setGlasses(*glasses)
    newToon.setShoes(*shoes)
    if isDisguised:
        if isWaiter:
            cogType = 4
        else:
            cogType = 0
        newToon.cogLevels = []
        for l in cogLevels:
            newToon.cogLevels.append(l)
        if cogType in ToontownGlobals.PutOnSuitRental or isRental:
            index = ToontownGlobals.CogDepts.index(suitDept)
            newToon.putOnSuit(index, cogType=cogType, rental=True)
        else:
            newToon.putOnSuit(suitType, cogType=cogType, rental=isRental)
        if coll:
            collTube = CollisionTube(0, 0, 0.5, 0, 0, 4, 2)
            collNode = CollisionNode('suit')
            collNode.addSolid(collTube)
            newToon.attachNewNode(collNode)
    else:
        newToon.useLOD(LOD)
        if coll:
            newToon.initializeBodyCollisions('toon')
    newToon.setPosHpr(x, y, z, h, p, r)
    newToon.reparentTo(parent)
    newToon.loop(anim)
    return newToon


def createCog(cogType, x=0, y=0, z=0, h=0, p=0, r=0, isSkelecog=False, isWaiter=False,
              isVirtual=False, isSkeleRevive=False, colorType=NametagGroup.CCSuit, anim='neutral',
              parent=render, name=None, dept=None, level=None, coll=True, do=None, callback=None,
              extraArgs=None):
    suit = Suit.Suit()
    suit.dna = SuitDNA.SuitDNA()
    suit.dna.newSuit(cogType)
    suit.setDNA(suit.dna)
    suit.setPlayerType(colorType)
    suit.setPickable(0)
    level = level if level is not None else suit.getActualLevel()
    if isWaiter:
        suit.makeWaiter()
    if isSkelecog:
        suit.makeSkeleton()
        suit.setName(TTLocalizer.Skeleton)
    if isVirtual:
        suit.makeVirtual()
    if isSkeleRevive:
        level = '%s%s' % (level, TTLocalizer.SkeleRevivePostFix)
    if name is not None:
        suit.setName(name)
    if dept is False:
        nameInfo = TTLocalizer.SuitBaseNameWithoutDept % {'name': suit._name,
                                                          'level': level}
    else:
        nameInfo = TTLocalizer.SuitBaseNameWithLevel % {'name': suit._name,
                                                        'dept': dept if dept is not None else suit.getStyleDept(),
                                                        'level': level}

    suit.setPosHpr(x, y, z, h, p, r)
    suit.reparentTo(parent)
    suit.loop(anim)
    suit.setDisplayName(nameInfo)

    if coll and do:
        suit.initializeBodyCollisions(do.uniqueName('suit'))
    elif coll:
        collTube = CollisionTube(0, 0, 0.5, 0, 0, 4, 2)
        collNode = CollisionNode('suit')
        collNode.addSolid(collTube)
        suit.attachNewNode(collNode)

    if callback and do:
        if extraArgs:
            suit.enableBattleDetect(do.uniqueName('suit-callback' + str(x * y * z)), callback, *extraArgs)
        else:
            suit.enableBattleDetect(do.uniqueName('suit-callback' + str(x * y * z)), callback)
    return suit


def createDoodle(name, head, ears, nose, tail, body, color, colorScale, eyes, gender, x=0, y=0, z=0, h=0, p=0,
                 r=0, parent=render, coll=True):
    doodle = Pet.Pet()
    doodle.setDNA([head, ears, nose, tail, body, color, colorScale, eyes, gender])
    doodle.setName(name)
    doodle.setPickable(0)
    doodle.reparentTo(parent)
    doodle.setPosHpr(x, y, z, h, p, r)
    doodle.enterNeutralHappy()
    if coll:
        doodle.initializeBodyCollisions('pet')
    return doodle

def createChar(name):
    char = Char.Char()
    charDNA = CharDNA.CharDNA()
    charDNA.newChar(name)
    char.setDNA(charDNA)
    char.addActive()
    char.initializeDropShadow()
    char.startBlink()
    char.startEarTask()
    return char
