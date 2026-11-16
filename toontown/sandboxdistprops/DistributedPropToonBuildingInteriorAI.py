# Distributed TestBuildingInterior == AI Side
# Created by drewc Oct 11 2023

from direct.distributed.DistributedObjectAI import DistributedObjectAI

from toontown.toonbase.ToontownTypes import TColoredTexture


class DistributedPropToonBuildingInteriorAI(DistributedObjectAI):

    def __init__(self, air, buildingDoId: int, zoneId: int, building):
        DistributedObjectAI.__init__(self, air)

        self.buildingDoId: int = buildingDoId
        self.zoneId: int = zoneId
        self.building = building

        # Styling
        self.interiorModel: str = ''
        self.wallpaper: TColoredTexture = ('', (1.0, 1.0, 1.0, 1.0))
        self.floor: TColoredTexture = ('', (1.0, 1.0, 1.0, 1.0))
        self.molding: TColoredTexture = ('', (1.0, 1.0, 1.0, 1.0))
        self.wainscoting: TColoredTexture = ('', (1.0, 1.0, 1.0, 1.0))
        self.wallpaperBorder: TColoredTexture = ('', (1.0, 1.0, 1.0, 1.0))

    def getBuildingId(self) -> int:
        return self.buildingDoId

    def requestDelete(self):
        # gracefully kick out all users
        DistributedObjectAI.requestDelete(self)

    def b_setInteriorStyle(self,
                           interiorModel: str,
                           wallpaper: TColoredTexture,
                           floor: TColoredTexture,
                           molding: TColoredTexture,
                           wainscoting: TColoredTexture,
                           wallpaperBorder: TColoredTexture):
        ...

    def d_setInteriorStyle(self,
                           interiorModel: str,
                           wallpaper: TColoredTexture,
                           floor: TColoredTexture,
                           molding: TColoredTexture,
                           wainscoting: TColoredTexture,
                           wallpaperBorder: TColoredTexture):
        self.sendUpdate('setInteriorStyle', (interiorModel, wallpaper, floor, molding, wainscoting, wallpaperBorder))

    def setInteriorStyle(self,
                         interiorModel: str,
                         wallpaper: TColoredTexture,
                         floor: TColoredTexture,
                         molding: TColoredTexture,
                         wainscoting: TColoredTexture,
                         wallpaperBorder: TColoredTexture):
        ...

    def getInteriorStyle(self) -> (str, TColoredTexture, TColoredTexture, TColoredTexture, TColoredTexture, TColoredTexture):
        return self.interiorModel, self.wallpaper, self.floor, self.molding, self.wainscoting, self.wallpaperBorder

