"""
Central place for event type names.

Using string constants keeps the event system robust when expanding gameplay logic.
"""

PLAYER_HIT = "PLAYER_HIT"
ENEMY_KILLED = "ENEMY_KILLED"
PROJECTILE_FIRED = "PROJECTILE_FIRED"

GAME_WIN_CONDITION = "GAME_WIN_CONDITION"
GAME_OVER_CONDITION = "GAME_OVER_CONDITION"

TIMER_TICK = "TIMER_TICK"
LIVES_ZERO = "LIVES_ZERO"
TIME_UP = "TIME_UP"

# Loot / item driven gameplay intents.
SYSTEM_PULSE_USED = "SYSTEM_PULSE_USED"

