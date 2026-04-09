from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.effect_base import BaseEffect


@dataclass
class EffectManager:
    """Orchestrates all active effects."""

    effects: list[BaseEffect] = field(default_factory=list)

    def add(self, effect: BaseEffect) -> None:
        self.effects.append(effect)

    def update(self, dt: float) -> None:
        for e in self.effects[:]:
            e.update(dt)
            if e.finished:
                self.effects.remove(e)

    def render(self, screen: Any) -> None:
        for e in self.effects:
            e.render(screen)

