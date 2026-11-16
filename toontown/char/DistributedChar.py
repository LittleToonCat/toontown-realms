from otp.avatar import DistributedAvatar
from . import Char


class DistributedChar(DistributedAvatar.DistributedAvatar, Char.Char):

    def __init__(self, cr):
        try:
            self.DistributedChar_initialized
        except:
            self.DistributedChar_initialized = 1
            DistributedAvatar.DistributedAvatar.__init__(self, cr)
            Char.Char.__init__(self)

    def delete(self):
        try:
            self.DistributedChar_deleted
        except:
            self.DistributedChar_deleted = 1
            Char.Char.delete(self)
            DistributedAvatar.DistributedAvatar.delete(self)

    def setDNAString(self, dnaString):
        Char.Char.setDNAString(self, dnaString)

    def setDNA(self, dna):
        Char.Char.setDNA(self, dna)

    def setHp(self, hp):
        self.hp = hp

    def getDialogueArray(self):
        return Char.Char.getDialogueArray(self)
