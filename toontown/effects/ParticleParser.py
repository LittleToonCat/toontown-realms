# ParticleParser
# Created by drewc Sep 16, 2024
"""
This is intended as a replacement to toontown/battle/Particles
Instead of manually defining each particle in the code, they can be defined (and customized)
in resource packs -- instead of using the .ptf file which is just python code (yikes), this is a secure and
more intuitive way to create particle effects
"""

import json
from direct.stdpy import file
from panda3d.core import Vec3, Vec2, Vec4, ColorBlendAttrib
from panda3d.physics import BaseParticleRenderer, BaseParticleEmitter, SparkleParticleRenderer
from typing import Optional

from direct.particles.ParticleEffect import ParticleEffect
from direct.particles.Particles import Particles
from direct.particles.SpriteParticleRendererExt import SpriteParticleRendererExt

from toontown.datapack.DataPackManager import DataPackManager


class InvalidParticleParamsError(Exception):
    pass


alphaModes = {
    'none': BaseParticleRenderer.PR_ALPHA_NONE,
    'alpha_in': BaseParticleRenderer.PR_ALPHA_IN,
    'alpha_out': BaseParticleRenderer.PR_ALPHA_OUT,
    'alpha_in_out': BaseParticleRenderer.PR_ALPHA_IN_OUT,
    'alpha_user': BaseParticleRenderer.PR_ALPHA_USER
}

alphaBlendModes = {
    'none': SpriteParticleRendererExt.PP_NO_BLEND,
    'linear': SpriteParticleRendererExt.PP_BLEND_LINEAR,
    'cubic': SpriteParticleRendererExt.PP_BLEND_CUBIC
}

colorBlendModes = {
    'none': ColorBlendAttrib.M_none,
    'add': ColorBlendAttrib.M_add,
    'subtract': ColorBlendAttrib.M_subtract,
    'inverse_subtract': ColorBlendAttrib.M_inv_subtract,
    'min': ColorBlendAttrib.M_min,
    'max': ColorBlendAttrib.M_max
}

colorBlendOperators = {
    "one": ColorBlendAttrib.O_one,
    "incoming_color": ColorBlendAttrib.O_incoming_color,
    "one_minus_incoming_color": ColorBlendAttrib.O_one_minus_incoming_color,
    "fbuffer_color": ColorBlendAttrib.O_fbuffer_color,
    "one_minus_fbuffer_color": ColorBlendAttrib.O_one_minus_fbuffer_color,
    "incoming_alpha": ColorBlendAttrib.O_incoming_alpha,
    "one_minus_incoming_alpha": ColorBlendAttrib.O_one_minus_incoming_alpha
    # ... the rest
}

def parseFile(filePath: str) -> ParticleEffect:
    if not file.exists(filePath):
        raise FileNotFoundError(f"Can not find {filePath}.")

    with file.open(filePath) as _ptcFile:
        ptc = json.load(_ptcFile)

        effect = ParticleEffect()

        # -- System --
        _system = ptc.get('system', None)

        if _system is None:
            raise InvalidParticleParamsError("System not defined in particle system.")

        effect.reset()

        effect.setPos(*_system.get('transform', {}).get('pos', [0.0, 0.0, 0.0]))
        effect.setHpr(*_system.get('transform', {}).get('hpr', [0.0, 0.0, 0.0]))
        effect.setScale(*_system.get('transform', {}).get('scale', [1.0, 1.0, 1.0]))

        p = Particles('ptc-1')

        p.setPoolSize(_system.get('pool_size', 1024))
        p.setBirthRate(_system.get('birth_rate', 0.02))
        p.setLitterSize(_system.get('litter_size', 10))
        p.setLitterSpread(_system.get('litter_spread', 0))
        p.setSystemLifespan(_system.get('lifespan', 0.0))

        velSpace = _system.get('velocity_space', 'render')
        if velSpace == 'render':
            p.setLocalVelocityFlag(False)
        elif velSpace == 'local':
            p.setLocalVelocityFlag(True)
        else:
            raise InvalidParticleParamsError(f"Invalid velocity space '{velSpace}'.")

        p.setSystemGrowsOlderFlag(_system.get("system_grows_older", False))

        # -- Factory --
        _fact = ptc.get('factory', None)
        if _fact is None:
            raise InvalidParticleParamsError("Factory not defined in particle system.")

        factType = _fact.get('factory_type', 'point')

        if factType == 'point':
            p.setFactory("PointParticleFactory")
        elif factType == 'zspin':
            p.setFactory("ZSpinParticleFactory")

        p.factory.setLifespanBase(_fact.get("lifespan_base", 1.0))
        p.factory.setLifespanSpread(_fact.get("lifespan_spread", 0.0))
        p.factory.setMassBase(_fact.get("mass_base", 1.0))
        p.factory.setMassSpread(_fact.get("mass_spread", 0.0))
        p.factory.setTerminalVelocityBase(_fact.get("terminal_velocity_base", 400.0))
        p.factory.setLifespanSpread(_fact.get('terminal_velocity_spread', 0.0))

        if factType == 'zspin':
            zs = _fact.get('zspin', {})
            #p.factory: ZSpinParticleFactory
            p.factory.setInitialAngle(zs.get('initial_angle', 0.0))
            p.factory.setInitialAngleSpread(zs.get('initial_angle_spread', 0.0))
            p.factory.setFinalAngle(zs.get('final_angle', 0.0))
            p.factory.setFinalAngleSpread(zs.get('final_angle_spread', 0.0))
            p.factory.enableAngularVelocity(zs.get('enable_angular_velocity', False))
            p.factory.setAngularVelocity(zs.get('angular_velocity_base', 0.0))
            p.factory.setAngularVelocity(zs.get('angular_velocity_spread', 0.0))

        # -- Emitter --
        _emit = ptc.get('emitter', None)
        if _emit is None:
            raise InvalidParticleParamsError("Emitter not defined in particle system.")

        emitType = _emit.get('emitter_type', 'point')
        if emitType == 'box':
            p.setEmitter("BoxEmitter")
            #p.emitter: BoxEmitter
            params = _emit.get('box', {})
            p.emitter.setMinBound(params.get('min_bounds', Vec3(-1.0)))
            p.emitter.setMaxBound(params.get('max_bounds', Vec3(1.0)))
        elif emitType == 'disc':
            p.setEmitter("DiscEmitter")
            #p.emitter: DiscEmitter
            params = _emit.get('disc', {})
            p.emitter.setRadius(params.get('radius', 1.0))
        elif emitType == 'line':
            p.setEmitter("LineEmitter")
            #p.emitter: LineEmitter
            params = _emit.get('box', {})
            p.emitter.setEndpoint1(params.get('point_1', Vec3(-1.0, 0.0, 0.0)))
            p.emitter.setEndpoint2(params.get('point_2', Vec3(1.0, 0.0, 0.0)))
        elif emitType == 'point':
            p.setEmitter("PointEmitter")
            #p.emitter: PointEmitter
            params = _emit.get('point', {})
            p.emitter.setLocation(params.get('position', Vec3(1.0)))
        elif emitType == 'rectangle':
            p.setEmitter("RectangleEmitter")
            #p.emitter: RectangleEmitter
            params = _emit.get('rectangle', {})
            p.emitter.setMinBound(params.get('min_bounds', Vec2(-1.0)))
            p.emitter.setMaxBound(params.get('max_bounds', Vec2(1.0)))
        elif emitType == 'ring':
            p.setEmitter("RingEmitter")
            #p.emitter: RingEmitter
            params = _emit.get('ring', {})
            p.emitter.setRadius(params.get('radius', 1.0))
            p.emitter.setRadiusSpread(params.get('radius_spread', 0.0))
        elif emitType == 'sphere_volume':
            p.setEmitter("SphereVolumeEmitter")
            #p.emitter: SphereVolumeEmitter
            params = _emit.get('sphere_volume', {})
            p.emitter.setRadius(params.get('radius', 1.0))
        elif emitType == 'sphere_surface':
            p.setEmitter("SphereSurfaceEmitter")
            #p.emitter: SphereSurfaceEmitter
            params = _emit.get('sphere_surface', {})
            p.emitter.setRadius(params.get('radius', 1.0))
        elif emitType == 'tangent_ring':
            p.setEmitter("TangentRingEmitter")
            #p.emitter: TangentRingEmitter
            params = _emit.get('ring', {})
            p.emitter.setRadius(params.get('radius', 1.0))
            p.emitter.setRadiusSpread(params.get('radius_spread', 0.0))
        elif emitType == 'arc':
            p.setEmitter("ArcEmitter")
            params = _emit.get('arc')
            p.emitter.setStartAngle(params.get('start_angle', -90))
            p.emitter.setEndAngle(params.get('end_angle', 90))

        p.emitter.setAmplitude(_emit.get('amplitude_base', 1.0))
        p.emitter.setAmplitudeSpread(_emit.get('amplitude_spread', 0.0))
        p.emitter.setOffsetForce(_emit.get('offset_force', Vec3(0)))

        emissionType = _emit.get('emission_type', 'radiate')
        if emissionType == 'radiate':
            p.emitter.setEmissionType(BaseParticleEmitter.ET_RADIATE)
            p.emitter.setRadiateOrigin(_emit.get('radiate_origin', Vec3(0)))
        elif emissionType == 'explicit':
            p.emitter.setEmissionType(BaseParticleEmitter.ET_EXPLICIT)
            p.emitter.setExplicitLaunchVector(_emit.get('explicit_velocity', Vec3(0)))
        else:
            raise InvalidParticleParamsError(f"Unsupported emission type '{emissionType}'")

        # -- Renderer --
        _rend = ptc.get('renderer', None)
        if _rend is None:
            raise InvalidParticleParamsError("Renderer not defined in particle system.")

        rendType = _rend.get('renderer_type', 'line')

        if rendType == 'line':
            p.setRenderer('LineParticleRenderer')
            #p.renderer: LineParticleRenderer
            params = _emit.get('line', {})
            p.renderer.setLineScaleFactor(params.get('line_scale', 1.0))
        elif rendType == 'sparkle':
            p.setRenderer('SparkleParticleRenderer')
            #p.renderer: SparkleParticleRenderer
            params = _emit.get('sparkle', {})
            p.renderer.setBirthRadius(params.get('birth_radius', 0.100))
            p.renderer.setDeathRadius(params.get('death_radius', 0.100))
            p.renderer.setCenterColor(params.get('center_color', Vec4(1.0)))
            p.renderer.setEdgeColor(params.get('edge_color', Vec4(1.0)))
            p.renderer.setLifeScale(SparkleParticleRenderer.SP_SCALE if params.get('life_scale', False) else SparkleParticleRenderer.SP_NO_SCALE)
        elif rendType == 'sprite':
            p.setRenderer('SpriteParticleRenderer')
            #p.renderer: SpriteParticleRendererExt
            params = _emit.get('sprite', {})
            _textures = params.get('textures', None)
            if not _textures:
                raise InvalidParticleParamsError("Texture not defined for sprite renderer")

            for _tex in _textures:
                if isinstance(_tex, str):
                    p.renderer.addTexture(DataPackManager.getTexture(_tex))
                elif isinstance(_tex, dict):
                    modelPath: Optional[str] = _tex.get('model_path', None)
                    if modelPath is None:
                        raise InvalidParticleParamsError("Model Path not defined for sprite renderer texture")
                    p.renderer.addTextureFromNode(DataPackManager.getModelNode(modelPath, _tex.get('node_path', None)))

            p.renderer.setXScaleFlag(params.get('animate_x_scale', False))
            p.renderer.setYScaleFlag(params.get('animate_y_scale', False))
            p.renderer.setAnimAngleFlag(params.get('animate_angle', False))
            p.renderer.setInitialXScale(params.get('initial_scale_x', 1.0))
            p.renderer.setInitialYScale(params.get('initial_scale_y', 1.0))
            p.renderer.setFinalXScale(params.get('final_scale_x', 1.0))
            p.renderer.setFinalYScale(params.get('final_scale_y', 1.0))
            p.renderer.setColor(params.get('color', Vec4(1.0)))

            p.renderer.setAlphaBlendMethod(alphaBlendModes.get(params.get('alpha_blend_mode', 'linear'),
                                                               SpriteParticleRendererExt.PP_BLEND_LINEAR))


        p.renderer.setColorBlendMode(
            colorBlendModes.get(_rend.get('color_blend_mode', 'none'), ColorBlendAttrib.M_none),
            colorBlendOperators.get(_rend.get('color_blend_incoming_operator', 'incoming_alpha'), ColorBlendAttrib.O_incoming_alpha),
            colorBlendOperators.get(_rend.get('color_blend_fbuffer_operator', 'one_minus_incoming_alpha'), ColorBlendAttrib.O_one_minus_incoming_alpha)
        )
        p.renderer.setAlphaMode(alphaModes.get(_rend.get('alpha_mode', BaseParticleRenderer.PR_ALPHA_NONE)))
        p.renderer.setUserAlpha(alphaModes.get(_rend.get('alpha_base', 1.0)))

        # todo: forces
        effect.addParticles(p)
        return effect