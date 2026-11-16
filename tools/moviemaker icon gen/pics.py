import os.path
import sys
import string
from typing import Dict, Union

from direct.directtools.DirectUtil import getFileData
from direct.distributed.PyDatagram import PyDatagram
from math import tan
from toontown.sandbox.PropGlobals import *
from pandac.PandaModules import *

loadPrcFileData('', 'win-size 256 256')
loadPrcFileData('', 'framebuffer-float 1')
loadPrcFileData('', 'model-path ../../resources')


loadPrcFileData('','vfs-mount ../../resources/phase_3 /phase_3')
loadPrcFileData('','vfs-mount ../../resources/phase_3.5 /phase_3.5')
loadPrcFileData('','vfs-mount ../../resources/phase_4 /phase_4')
loadPrcFileData('','vfs-mount ../../resources/phase_5 /phase_5')
loadPrcFileData('','vfs-mount ../../resources/phase_5.5 /phase_5.5')
loadPrcFileData('','vfs-mount ../../resources/phase_6 /phase_6')
loadPrcFileData('','vfs-mount ../../resources/phase_7 /phase_7')
loadPrcFileData('','vfs-mount ../../resources/phase_8 /phase_8')
loadPrcFileData('','vfs-mount ../../resources/phase_9 /phase_9')
loadPrcFileData('','vfs-mount ../../resources/phase_10 /phase_10')
loadPrcFileData('','vfs-mount ../../resources/phase_11 /phase_11')
loadPrcFileData('','vfs-mount ../../resources/phase_12 /phase_12')
loadPrcFileData('','vfs-mount ../../resources/phase_13 /phase_13')
loadPrcFileData('','vfs-mount ../../resources/phase_14 /phase_14')
loadPrcFileData('','vfs-mount ../../resources/phase_14.5 /phase_14.5 ')
loadPrcFileData('','default-model-extension .bam')
loadPrcFileData('','allow-incomplete-render false')

from direct.directbase.DirectStart import *
base.setBackgroundColor(VBase4(0, 0, 0, 0.0))

gear = loader.loadModel('phase_3/models/gui/ttrm_m_gui_chat_emojis').find('**/gear')
gear.setScale(0.4)
gear.setPos(0.2, 0.2, 0.2)
gear.reparentTo(hidden)

base.disableMouse()
base.camLens.setFov(40,40)

if not os.path.exists('export'):
    os.mkdir('export')

overrides: Dict[str, Dict[str, Union[float, Dict[str, str]]]] = {
    'Large Rug': {'p': 90},
    'Leaf Mat': {'p': 90},
    'Round Rug': {'p': 90},
    'Cog Papers': {'p': 90},
    'Small Rug': {'p': 90},
    'Quicksand': {'p': 90},
    'Trapdoor': {'p': 90},
    'Green Rug': {'p': 90},
    'Pink Slip': {'p': -90, 'h': 180},
    'Boiler 2': {'p': 180},
    'Gear': {'p': 90},
    'Factory Gear': {'p': 90},
    'Ice Tire': {'p': 25},
    'Money': {'p': 25},
    'Pencil': {'p': 45},
    'Glass of Water': {'p': -90},
    'Market Crash Newspaper': {'p': -90},
    'Magnet': {'p': -90},
    'Fidget Spinner': {'p': -90},
    'Piano': {'p': -45},
    'Ropes': {'s': 2},
    'Witness Stand': {'s': 2},
    'Red Tape': {'p': 90},
    'Lawbot Highrise 2': {'h': 190},
    'Lawbot Highrise 6': {'h': 190},
    'Lawbot Highrise 8': {'h': 190},
    'Lawbot Highrise 10': {'h': 195},
    'Lawbot Highrise 11': {'h': 195},
    'Lawbot Highrise 12': {'h': 195},
    'Lawbot Highrise 17': {'h': 195},
    'Lawbot Highrise 18': {'h': 195},
    'Lawbot Highrise 19': {'h': 195},
    'Street Incline': {'p': 0, 'h': 70, 'r': -20},
    'Cashbot Highrise 2': {'h': 190},
    'Cashbot Highrise 4': {'h': 190},
    'Cashbot Highrise 6': {'h': 190},
    'Cashbot Highrise 8': {'h': 190},
    'Cashbot Highrise 10': {'h': 190},
    'Cashbot Highrise 11': {'h': 190},
    'Cashbot Highrise 12': {'h': 190},
    'Cashbot Highrise 14': {'h': 190},
    'Primitive Cylinder': {'p': 20, 'h': -20, 's': 0.8},
    'Switchboard': {'h': 160},
    'Safe': {'h': 180},
    'Small Trampoline': {'h': -20, 'p': 10, 's': 1.7},
    'Cane Hat': {'h': 0, 'r': -90},
    'Cannon': {'h': 180},
    'Simple Sombrero': {'p': -85},
    'Teeth': {'s': .9, 'h': 90},
    'Toontown Central Gag Shop': {'h': 180},
    'Donald\'s Dock Gag Shop': {'h': 180},
    'Daisy Gardens Gag Shop': {'h': 180},
    'Minnie\'s Melodyland Gag Shop': {'h': 180},
    'The Brrrgh Gag Shop': {'h': 180},
    'Donald\'s Dreamland Gag Shop': {'h': 180},
    'Toon House 1': {'h': -90},
    'Toon House 2': {'h': -90},
    'Tiki House': {'h': -90},
    'Castle House': {'h': -90},
    'Tepee House': {'h': -90},
    'Cupcake House': {'h': -90},
    'Toon Tunnel': {'h': 180},
    'Roll-o-dex': {'h': 180},
    'Signpost': {'z': 0},
    'Ice Cube - Boot 1': {'s': 1.8},
    'Ice Cube - Boot 2': {'s': 1.8},
    'Ice Cube - Ear Muffs': {'s': 1.8},
    'Ice Cube - Glove': {'s': 1.8},
    'Ice Cube - Sunglasses': {'s': 1.8},
    'Street Sharp Corner': {'t': {'street_full_corner_curb': 'phase_3.5/maps/curb_brown_even.png',
                                  'street_full_corner_sidewalk': 'phase_3.5/maps/sidewalk_4cont_brown.png'}},
}


def getProp(name: str) -> NodePath:
    mdl = loader.loadModel(PropList[name][LIST_MODEL])
    attribs = PropList[name][LIST_ATTRIBUTES]
    # If the prop is a node inside of a model instead of the full model itself
    if 'sub_node' in attribs:
        model = mdl.find('**/' + attribs['sub_node'])
        mdl.removeNode()
    else:
        model = mdl
    if 'texture' in attribs:
        texture = loader.loadTexture(attribs["texture"])
        model.setTexture(texture, 1)

    if 'hide_nodes' in attribs:
        if isinstance(attribs['hide_nodes'], str):
            model.find('**/' + attribs['hide_nodes']).removeNode()
        else:
            for node in attribs['hide_nodes']:
                model.find('**/' + node).removeNode()

    if 'models/char/suit' in PropList[name][LIST_MODEL]:
        model.setH(180)

    # todo easier way of overriding rotations for certian models
    if 'Sidewalk ' in name:
        model.setP(90)
        model.setH(-20)
    if 'Street ' in name:
        model.setP(90)
        model.setH(-20)
    return model


base.graphicsEngine.renderFrame()
for prop in PropList:
    #print(prop)
    lower_name = prop.lower().replace(' ', '_').replace('/', '_')
    propType = PropList[prop][LIST_TYPE]
    if propType == PropDistributed:
        gear.reparentTo(base.a2dBottomLeft)
    model = getProp(prop)
    model.setDepthTest(1)
    model.setDepthWrite(1)
    # Small hack to fix billboards on the UI
    for np in model.findAllMatches('**/*'):
        if isinstance(np, NodePath):
            if np.hasBillboard():
                np.setBillboardPointEye()
    model.setTransparency(TransparencyAttrib.MDual)
    pitch = render.attachNewNode('pitch')
    rotate = pitch.attachNewNode('rotate')
    scale = rotate.attachNewNode('scale')

    if prop in overrides:
        _override = overrides[prop]
        if 'p' in _override:
            model.setP(_override['p'])
        if 'h' in _override:
            model.setH(_override['h'])
        if 'r' in _override:
            model.setR(_override['r'])

    model.reparentTo(scale)    
    pitch.setH(20)
    bMin, bMax = model.getTightBounds()
    center = (bMin + bMax) / 2.0
    model.setPos(-center[0], -center[1], -center[2])

    bMin, bMax = pitch.getTightBounds()
    center = (bMin + bMax) / 2.0
    corner = Vec3(bMax - center)
    scale.setScale(1.0 / max(corner[0], corner[1], corner[2]))
    pitch.setY(3)
    if PropList[prop][0] == PropSpecialSign:
        model.setZ(.05)

    if prop in overrides:
        _override = overrides[prop]

        if 's' in _override:
            scale.setScale(scale, _override['s'])
        if 'z' in _override:
            pitch.setZ(_override['z'])
        if 't' in _override:
            for subNode, texturePath in list(_override['t'].items()):
                subNP = model.find('**/' + subNode)
                if isinstance(subNP, NodePath):
                    texture = loader.loadTexture(texturePath)
                    subNP.setTexture(texture, 1)

    base.graphicsEngine.renderFrame()
    imageName = f'export/bsr_ico_{lower_name}.png'#.exr'
    base.screenshot(namePrefix=Filename.fromOsSpecific(imageName), defaultFilename=False)

    if propType == PropDistributed:
        gear.reparentTo(hidden)

    model.removeNode()
    pitch.removeNode()



