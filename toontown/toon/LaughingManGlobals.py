from panda3d.core import *


def makeCard(index, book=False):
    cardMaker = CardMaker('laughing-man-cm')
    cardMaker.setHasUvs(1)
    cardMaker.setFrame(-0.5, 0.5, -0.5, 0.5)

    nodePath = NodePath('laughing-man-{}'.format(index))
    nodePath.setBillboardPointEye()

    lmBase = nodePath.attachNewNode(cardMaker.generate())
    lmBase.setTexture(loader.loadTexture('phase_14.5/maps/magicCat-base.png'))
    lmBase.setY(-0.3)
    lmBase.setTransparency(True)

    lmText = nodePath.attachNewNode(cardMaker.generate())
    lmText.setTexture(loader.loadTexture('phase_14.5/maps/magicCat-text.png'))
    lmText.setY(-0.301)
    lmText.setTransparency(True)
    lmText.hprInterval(10, (0, 0, -360)).loop()

    lmFace = nodePath.attachNewNode(cardMaker.generate())
    lmFace.setTexture(loader.loadTexture('phase_14.5/maps/magicCat-face.png'))
    lmFace.setY(-0.302)
    lmFace.setTransparency(True)

    return nodePath


def addHeadEffect(head, index, book=False):
    card = makeCard(index, book=book)
    card.setScale(1.45 if book else 2.5)
    card.setZ(0.05 if book else 0.5)
    for nodePath in head.getChildren():
        nodePath.hide()
    card.instanceTo(head)


def addToonEffect(toon):
    lods = toon.getLODNames()
    for lod in lods:
        index = lods.index(lod)
        addHeadEffect(toon.getPart('head', lod), index)
