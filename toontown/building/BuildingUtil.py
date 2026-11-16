from toontown.toonbase import ToontownGlobals
from toontown.building import ToonInterior, KongdominiumInterior, PizzeriaInterior, MuseumInterior, GyrosLabInterior


def getInteriorPlaceFromZoneId(zoneId):
    """Allows custom Place classes to be defined for building interiors.
    This is mainly used for custom interior music."""
    if zoneId == ToontownGlobals.Kongdominium:
        placeClass = KongdominiumInterior.KongdominiumInterior
    elif zoneId == ToontownGlobals.Pizzeria:
        placeClass = PizzeriaInterior.PizzeriaInterior
    elif zoneId == ToontownGlobals.ToonMuseum:
        placeClass = MuseumInterior.MuseumInterior
    elif zoneId == ToontownGlobals.GyrosLab:
        placeClass = GyrosLabInterior.GyrosLabInterior
    else:
        placeClass = ToonInterior.ToonInterior
    return placeClass
