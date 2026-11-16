from direct.distributed.PyDatagram import PyDatagram


class AvatarDNA:
    def __str__(self):
        return 'AvatarDNA parent class: type undefined'

    def makeNetString(self):
        raise NotImplementedError('Must be overriden by subclass!')

    def printNetString(self):
        string = self.makeNetString()
        dg = PyDatagram(string)
        dg.dumpHex(__builtins__['ostream'])

    def makeFromNetString(self, string):
        raise NotImplementedError('Must be overriden by subclass!')

    def getType(self):
        raise NotImplementedError('Must be overriden by subclass!')
