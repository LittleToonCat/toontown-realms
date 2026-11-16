from otp.level import EntityCreator
from . import FactoryLevelMgr
from . import PlatformEntity
from . import ConveyorBelt
from . import GearEntity
from . import PaintMixer
from . import GoonClipPlane
from . import MintProduct
from . import MintProductPallet
from . import MintShelf
from . import PathMasterEntity
from . import RenderingEntity

class FactoryEntityCreator(EntityCreator.EntityCreator):

    def __init__(self, level):
        EntityCreator.EntityCreator.__init__(self, level)
        self.privRegisterTypes({'activeCell': 'nonlocal',
         'crusherCell': 'nonlocal',
         'battleBlocker': 'nonlocal',
         'beanBarrel': 'nonlocal',
         'button': 'nonlocal',
         'conveyorBelt': ConveyorBelt.ConveyorBelt,
         'crate': 'nonlocal',
         'door': 'nonlocal',
         'directionalCell': 'nonlocal',
         'gagBarrel': 'nonlocal',
         'gear': GearEntity.GearEntity,
         'goon': 'nonlocal',
         'gridGoon': 'nonlocal',
         'golfGreenGame': 'nonlocal',
         'goonClipPlane': GoonClipPlane.GoonClipPlane,
         'grid': 'nonlocal',
         'healBarrel': 'nonlocal',
         'levelMgr': FactoryLevelMgr.FactoryLevelMgr,
         'lift': 'nonlocal',
         'mintProduct': MintProduct.MintProduct,
         'mintProductPallet': MintProductPallet.MintProductPallet,
         'mintShelf': MintShelf.MintShelf,
         'mover': 'nonlocal',
         'paintMixer': PaintMixer.PaintMixer,
         'pathMaster': PathMasterEntity.PathMasterEntity,
         'rendering': RenderingEntity.RenderingEntity,
         'platform': PlatformEntity.PlatformEntity,
         'sinkingPlatform': 'nonlocal',
         'stomper': 'nonlocal',
         'stomperPair': 'nonlocal',
         'laserField': 'nonlocal',
         'securityCamera': 'nonlocal',
         'elevatorMarker': 'nonlocal',
         'trigger': 'nonlocal',
         'moleField': 'nonlocal',
         'maze': 'nonlocal'})
