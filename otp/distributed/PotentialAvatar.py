from typing import Tuple

from toontown.toonbase.ToontownTypes import TAccessory


class PotentialAvatar:

    def __init__(self, _id, names, dna, position, allowedName,
                 hat: TAccessory = (0, 0, 0), glasses: TAccessory = (0, 0, 0),
                 backpack: TAccessory = (0, 0, 0), shoes: TAccessory = (0, 0, 0),
                 lastZone: int = 0, nametagStyle: int = 100, nametagType: int = 0,
                 hp: int = 0, maxHp: int = 0,
                 creator = 1, shared = 1, online = 0, wishState = 'CLOSED', wishName = '',
                 defaultShard = 0, lastLogout = 0):
        self.id: int = _id
        self.name: str = names[0]
        self.dna = dna
        self.hat: TAccessory = hat
        self.glasses: TAccessory = glasses
        self.backpack: TAccessory = backpack
        self.shoes: TAccessory = shoes
        self.lastZone: int = lastZone
        self.nametagStyle: int = nametagStyle
        self.nametagType: int = nametagType
        self.health: Tuple[int, int] = (hp, maxHp)
        self.avatarType = None
        self.position = position
        self.wantName = names[1]
        self.approvedName = names[2]
        self.rejectedName = names[3]
        self.allowedName = allowedName
        self.wishState = wishState
        self.wishName = wishName
        self.creator = creator
        self.shared = shared
        self.online = online
        self.defaultShard = defaultShard
        self.lastLogout = lastLogout
        return
