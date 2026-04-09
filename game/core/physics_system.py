from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Velocity:
    vx: float = 0.0
    vy: float = 0.0


class PhysicsSystem:
    """Small physics placeholder (movement, acceleration)."""

    @staticmethod
    def move(entity: object, vx: float, vy: float, dt: float) -> None:
        """Moves objects that expose `x` and `y` float attributes."""
        if not hasattr(entity, "x") or not hasattr(entity, "y"):
            return
        # Entities in this project use `x/y` as their position.
        entity.x += vx * dt  # type: ignore[attr-defined]
        entity.y += vy * dt  # type: ignore[attr-defined]

