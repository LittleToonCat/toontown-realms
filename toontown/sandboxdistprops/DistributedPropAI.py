# Distributed Prop == AI Side
# Created by drewc Oct 14 2023
import json
from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedNodeAI import DistributedNodeAI
from typing import Optional, Dict, Any, List, Union

from panda3d.core import Vec3F, Vec3

from toontown.sandbox import PropGlobals
from toontown.sandbox.PropGlobals import LIST_ATTRIBUTES


class DistributedPropAI(DistributedNodeAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistPropAI')
    notify.setDebug(True)

    def __init__(self,
                 air,
                 generator,
                 name: str,
                 uuid: str,
                 data: Optional[Dict[str, Any]] = None):
        DistributedNodeAI.__init__(self, air, name = f'{name}:{uuid}')

        if data is None:
            data = {}
        self.data = data

        self.uuid = uuid

        self.generator = generator

        self._name = name

        if name not in PropGlobals.PropList:
            self.notify.warning(f"Prop {name} does not exist in PropList! Skipping ({uuid})")

        # These are non-editable attributes of a prop
        self.attributes = PropGlobals.PropList[self._name][LIST_ATTRIBUTES]

    def getUUID(self) -> str:
        return self.uuid

    def getGeneratorDoId(self) -> int:
        return self.generator.doId

    def getPropName(self) -> str:
        return self._name

    def requestDataChange(self, key: str, valueType: int, values: List[str]):
        newVals: Optional[Union[
            Union[List[int], int],
            Union[List[str], str],
            Union[List[float], float],
        ]] = None
        if valueType == 0:  # INT
            newVals = self.dataParseInt(values)
        elif valueType == 1:  # STR
            newVals = values if len(values) > 1 else values[0]
        elif valueType == 2:  # FLOAT
            newVals = self.dataParseFloat(values)
        self.data[key] = newVals

        self.generator.requestUpdateProp(
            self.getUUID(),
            [*self.getPos()],
            [*self.getHpr()],
            [*self.getScale()],
            json.dumps(self.data)  # todo: make a meth on generator to do this without dumping and then loading json!
        )

    @staticmethod
    def dataParseInt(raw: List[str]) -> Union[List[int], int]:
        new: List[int] = []
        for string in raw:
            try:
                x = int(string)
            except:
                x = 0
            new.append(x)
        if len(new) == 1:
            return new[0]
        return new

    @staticmethod
    def dataParseFloat(raw: List[str]) -> Union[List[float], float]:
        new: List[float] = []
        for string in raw:
            try:
                x = float(string)
            except:
                x = 0
            new.append(x)
        if len(new) == 1:
            return new[0]
        return new


