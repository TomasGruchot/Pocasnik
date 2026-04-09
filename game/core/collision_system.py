from __future__ import annotations

from typing import Callable, Iterable, Optional, Protocol, runtime_checkable


@runtime_checkable
class Intersectable(Protocol):
    alive: bool

    def intersects(self, other: "Intersectable") -> bool: ...


class CollisionSystem:
    """Collision helpers. Entities must implement `intersects(other)` + `alive`."""

    @staticmethod
    def intersects(a: Intersectable, b: Intersectable) -> bool:
        return a.intersects(b)

    @staticmethod
    def resolve_projectile_enemy(
        projectiles: Iterable[Intersectable],
        enemy: Optional[Intersectable],
        on_projectile_hit: Callable[[Intersectable, Intersectable], None],
    ) -> None:
        if enemy is None:
            return

        for p in projectiles:
            if not getattr(p, "alive", True):
                continue
            if CollisionSystem.intersects(p, enemy):
                on_projectile_hit(p, enemy)

    @staticmethod
    def resolve_enemy_player(
        enemy: Optional[Intersectable],
        player: Optional[Intersectable],
        on_enemy_hit_player: Callable[[Intersectable, Intersectable], None],
    ) -> None:
        if enemy is None or player is None:
            return
        if getattr(enemy, "alive", True) and CollisionSystem.intersects(enemy, player):
            on_enemy_hit_player(enemy, player)

