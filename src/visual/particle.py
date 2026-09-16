#! /usr/bin/env python3
"""Falling background particle effects (e.g. snowflakes)."""

import random
from abc import ABC, abstractmethod
import pygame as pg


class Particle(ABC):
    """A single particle falling down the screen and wrapping around."""

    def __init__(self, screen_width: int, screen_height: int) -> None:
        """Spawn a particle at a random position above the screen.

        Args:
            screen_width: Width of the screen, used to bound the
                particle's horizontal position.
            screen_height: Height of the screen, used to bound the
                particle's vertical spawn position and wrap-around.
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.pos_x: float = random.uniform(0, screen_width)
        self.pos_y: float = random.uniform(-screen_height, 0)
        self.speed: float = random.uniform(20.0, 80.0)
        self.radius: int = random.randrange(2, 6)

    def update(self, dt: float) -> None:
        """Fall by ``dt`` seconds, wrapping back to the top when off-screen."""
        self.pos_y += self.speed * dt
        if self.pos_y >= self.screen_height:
            self.pos_y = 0
            self.pos_x = random.uniform(0, self.screen_width)

    @abstractmethod
    def draw(self, surface: pg.Surface) -> None:
        """Draw the particle onto ``surface``."""
        ...


class Snowflake(Particle):
    """A particle drawn as a small white circle."""

    def draw(self, surface: pg.Surface) -> None:
        """Draw the snowflake as a filled circle onto ``surface``."""
        pg.draw.circle(
            surface, 'White', (int(self.pos_x), int(self.pos_y)),
            self.radius
        )


class ParticleSystem():
    """A collection of particles updated and drawn together."""

    def __init__(self, particles: list[Particle]) -> None:
        """Create a system wrapping an existing list of particles."""
        self.particles = particles

    def update(self, dt: float) -> None:
        """Advance every particle by ``dt`` seconds."""
        for particle in self.particles:
            particle.update(dt)

    def draw(self, surface: pg.Surface) -> None:
        """Draw every particle onto ``surface``."""
        for particle in self.particles:
            particle.draw(surface)
