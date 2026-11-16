from typing import Optional
from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.particles.ParticleEffect import ParticleEffect
from panda3d.core import Fog, NodePath

class EnvironmentManager:
    notify = directNotify.newCategory('EnvironmentManager')

    defaultParticle = None
    defaultParticleRender = None
    defaultFog = None

    activeParticle = None
    activeParticleRender= None
    activeFog = None

def setDefaultParticle(defaultParticle: Optional[ParticleEffect]):
    if EnvironmentManager.defaultParticle is not None:
        EnvironmentManager.notify.error('Tried to set default particle, but it already exists!')

    EnvironmentManager.defaultParticle = defaultParticle

def setDefaultParticleRender(defaultParticleRender: Optional[NodePath]):
    if EnvironmentManager.defaultParticleRender is not None:
        EnvironmentManager.notify.error('Tried to set default particle render, but it already exists!')

    EnvironmentManager.defaultParticleRender = defaultParticleRender

def setDefaultFog(defaultFog: Optional[Fog]):
    if EnvironmentManager.defaultFog is not None:
        EnvironmentManager.notify.error('Tried to set default fog, but it already exists!')

    EnvironmentManager.defaultFog = defaultFog

def setActiveParticle(activeParticle: Optional[ParticleEffect]):
    if EnvironmentManager.activeParticle is not None:
        if EnvironmentManager.activeParticle != EnvironmentManager.defaultParticle:
            EnvironmentManager.activeParticle.cleanup()
        else:
            EnvironmentManager.activeParticle.disable()

    EnvironmentManager.activeParticle = activeParticle

def setActiveParticleRender(activeParticleRender: Optional[NodePath]):
    if EnvironmentManager.activeParticleRender is not None:
        if EnvironmentManager.activeParticleRender != EnvironmentManager.defaultParticle:
            EnvironmentManager.activeParticleRender.removeNode()

    EnvironmentManager.activeParticleRender = activeParticleRender

def setActiveFog(activeFog: Optional[Fog]):
    EnvironmentManager.activeFog = activeFog

def enableEnvironment():
    if EnvironmentManager.activeParticleRender is not None and EnvironmentManager.activeParticle is not None:
        EnvironmentManager.activeParticle.start(base.camera, EnvironmentManager.activeParticleRender)

    if base.wantFog:
        if EnvironmentManager.activeFog is not None:
            fog = EnvironmentManager.activeFog
        else:
            fog = EnvironmentManager.defaultFog
        if fog is not None:
            base.render.setFog(EnvironmentManager.activeFog)

            if hasattr(base.cr.playGame.hood, 'sky'):
                base.cr.playGame.hood.sky.setFog(EnvironmentManager.activeFog)

def disableEnvironment():
    if EnvironmentManager.activeParticleRender is not None:
        EnvironmentManager.activeParticle.disable()

    if base.wantFog and EnvironmentManager.activeFog is not None:
        base.render.clearFog()

        # should be EnvironmentManager.sky
        if hasattr(base.cr.playGame.hood, 'sky'):
            base.cr.playGame.hood.sky.clearFog()

def unloadActiveEnvironment():
    if EnvironmentManager.activeParticle == EnvironmentManager.defaultParticle and \
        EnvironmentManager.activeParticleRender == EnvironmentManager.defaultParticleRender and \
            EnvironmentManager.activeFog == EnvironmentManager.defaultFog:
        return

    setActiveParticle(EnvironmentManager.defaultParticle)
    setActiveParticleRender(EnvironmentManager.defaultParticleRender)
    setActiveFog(EnvironmentManager.defaultFog)
    base.render.clearFog()
    if hasattr(base.cr.playGame.hood, 'sky'):
        base.cr.playGame.hood.sky.clearFog()
    enableEnvironment()

def unloadEnvironment():
    setActiveParticle(None)
    setActiveParticleRender(None)
    if base.wantFog and EnvironmentManager.activeFog is not None:
        base.render.clearFog()

        # should be EnvironmentManager.sky
        if hasattr(base.cr.playGame.hood, 'sky'):
            base.cr.playGame.hood.sky.clearFog()
    setActiveFog(None)

    if EnvironmentManager.defaultParticle is not None:
        EnvironmentManager.defaultParticle.cleanup()
        EnvironmentManager.defaultParticle = None
    if EnvironmentManager.defaultParticleRender is not None:
        EnvironmentManager.defaultParticleRender.removeNode()
        EnvironmentManager.defaultParticleRender = None

    EnvironmentManager.defaultFog = None