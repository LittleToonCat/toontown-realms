"""
The holder of each movie maker scene,
includes basically everything
"""
from typing import Dict, Any, List

from direct.interval.FunctionInterval import Func
from direct.interval.Interval import Interval
from direct.interval.MetaInterval import Parallel
from panda3d.core import Vec3

from toontown.moviemaker.MovieMakerActor import MovieMakerActor

NODE_SET_POS = "ivNode_setPos"
NODE_LERP_POS = "ivNode_posInterval"

ACTOR_LOOP_ANIM = "ivNode__actor__loop"


class MovieMakerData:

    def __init__(self, movieMaker):
        self.hashToActors: Dict[str, MovieMakerActor] = {}
        self.movieMaker = movieMaker

    def addActor(self, actor: MovieMakerActor):
        self.hashToActors[actor.getHash()] = actor

    def removeActor(self, actor: MovieMakerActor):
        del self.hashToActors[actor.getHash()]

    def getActorFromHash(self, _hash: str):
        return self.hashToActors[_hash]

    # todo: change this from an Any to a union of movie maker object types (movieToon, movieProp, etc) once they get added
    def getObjectFromName(self, name: str) -> Any:
        if name == 'camera':
            return self.movieMaker.camera.sceneCamera

    def toJson(self) -> List[Dict]:

        __dict = []

        for actor in self.hashToActors.values():
            __dict.append(actor.toJson())

        #for timestamp, node in self.intervalNodes.items():
        #    __dict[timestamp] = node.toJson()

        return __dict
