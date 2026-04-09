from __future__ import annotations

try:
    import pygame
except ModuleNotFoundError:  # pragma: no cover
    pygame = None  # type: ignore[assignment]


class ProjectileSprite(pygame.sprite.Sprite):  # type: ignore[misc]
    """Projectile sprite moving at constant velocity."""

    def __init__(self, pos: "pygame.Vector2", vel: "pygame.Vector2", image: "pygame.Surface") -> None:
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(center=(int(pos.x), int(pos.y)))
        self.pos = pygame.Vector2(pos.x, pos.y)
        self.vel = pygame.Vector2(vel.x, vel.y)

    def update(self, dt: float) -> None:
        self.pos += self.vel * dt
        self.rect.center = (int(self.pos.x), int(self.pos.y))

