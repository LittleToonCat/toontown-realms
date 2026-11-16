
def getAccBonus(i):
    if i > 3:
        i = 3
    return i * 20

def getDmgBonus(i):
    if i == 0:
        return 0
    return 20

def getAttackExpPerTrack(i):
    return i * 10

TOONS_TAKE_NO_DAMAGE = 0
APPLY_HEALTH_ADJUSTMENTS = 1

BATTLE_MSG_INIT_ROUND = 'init-round-%(battleId)s'
BATTLE_MSG_PROCESS_BONUS = 'process-bonuses-%(battleId)s'
BATTLE_MSG_GEN_COG_ATTACK = 'generate-cog-attack-%(battleId)s'
BATTLE_MSG_GEN_COG_ATTACK_FIRST = 'generate-cog-attack-first-%(battleId)s'
BATTLE_MSG_REMOVE_ACTIVE_TOON_INDEX = 'remove-active-toon-index-%(battleId)s'
BATTLE_MSG_RESET_NEXT_ATTACK = 'reset-next-attack-%(battleId)s'
BATTLE_MSG_COG_DIED = 'cog-died-%(battleId)s'
BATTLE_MSG_TRACK_USED = 'track-used-%(battleId)s'
BATTLE_MSG_PASS_USED = 'pass-used-%(battleId)s'