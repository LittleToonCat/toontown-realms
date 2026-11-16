from toontown.building.SuitPlannerInteriorAI import SuitPlannerInteriorAI

class SuitPlannerCogdoInteriorAI(SuitPlannerInteriorAI):

    def __init__(self, cogdoLayout, bldgLevel, bldgTracks, zone):
        self._cogdoLayout = cogdoLayout
        SuitPlannerInteriorAI.__init__(self, self._cogdoLayout.getNumGameFloors(), bldgLevel, bldgTracks, zone, respectInvasions = 0)

    def _genSuitInfos(self, numFloors, bldgLevel):
        SuitPlannerInteriorAI._genSuitInfos(self, self._cogdoLayout.getNumFloors(), bldgLevel)
