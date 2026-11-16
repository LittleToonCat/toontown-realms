from typing import List


class StatusEffect:

    def __init__(self, identifier: str, rounds: int = -1, extraArgs = None):
        if extraArgs is None:
            extraArgs = []
        self.identifier: str = identifier
        self.rounds: int = rounds
        self.extraArgs: List[float] = extraArgs

    def getId(self) -> str:
        return self.identifier

    def setRounds(self, rounds: int):
        self.rounds = rounds

    def getRounds(self) -> int:
        return self.rounds

    def getArgs(self) -> List[float]:
        return self.extraArgs
