EndlessGame = config.GetBool('endless-catch-game', 0)
GameDuration = 55.0

class DropObject:

    def __init__(self, name, good, onscreenDurMult, modelPath):
        self.name = name
        self.good = good
        self.onscreenDurMult = onscreenDurMult
        self.modelPath = modelPath

    def isBaseline(self):
        return self.onscreenDurMult == 1.0


DropObjectTypes = [DropObject('apple', 1, 1.0, 'phase_4/models/minigames/apple'),
 DropObject('orange', 1, 1.0, 'phase_4/models/minigames/orange'),
 DropObject('pear', 1, 1.0, 'phase_4/models/minigames/pear'),
 DropObject('coconut', 1, 1.0, 'phase_4/models/minigames/coconut'),
 DropObject('watermelon', 1, 1.0, 'phase_4/models/minigames/watermelon'),
 DropObject('pineapple', 1, 1.0, 'phase_4/models/minigames/pineapple'),
 DropObject('anvil', 0, 0.4, 'phase_4/models/props/anvil-mod')]
Name2DropObjectType = {}
for type in DropObjectTypes:
    Name2DropObjectType[type.name] = type

Name2DOTypeId = {}
names = list(Name2DropObjectType.keys())
names.sort()
for i in range(len(names)):
    Name2DOTypeId[names[i]] = i

DOTypeId2Name = names
NumFruits = [{2000: 18,
  1000: 19,
  5000: 22,
  4000: 24,
  3000: 27,
  9000: 28,
  21000: 18,
  22000: 22,
  23000: 24,
  24000: 28,
  25000: 27,
  26000: 19,
  19000: 48},
 {2000: 30,
  1000: 33,
  5000: 38,
  4000: 42,
  3000: 46,
  9000: 50,
  21000: 30,
  22000: 38,
  23000: 42,
  24000: 50,
  25000: 46,
  26000: 33,
  19000: 100},
 {2000: 42,
  1000: 48,
  5000: 54,
  4000: 60,
  3000: 66,
  9000: 71,
  21000: 42,
  22000: 54,
  23000: 60,
  24000: 71,
  25000: 66,
  26000: 48,
  19000: 142},
 {2000: 56,
  1000: 63,
  5000: 70,
  4000: 78,
  3000: 85,
  9000: 92,
  21000: 56,
  22000: 70,
  23000: 78,
  24000: 92,
  25000: 85,
  26000: 63,
  19000: 184}]
