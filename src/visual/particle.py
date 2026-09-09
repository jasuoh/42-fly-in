#! /usr/bin/env python3

import random
from abc import ABC, abstractmethod
import pygame as pg

class Particle(ABC):
    def __init__(self, screen_width: int, screen_height: int) -> None:
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.pos_x: float = random.uniform(0, screen_width)
        self.pos_y: float = random.uniform(-screen_height, 0)
        self.speed: float = random.uniform(20.0, 80.0)
        self.radius: int = random.randrange(2, 6)

    def update(self, dt: float) -> None:
        self.pos_y += self.speed * dt
        if self.pos_y >= self.screen_height:
            self.pos_y = 0
            self.pos_x = random.uniform(0, self.screen_width)

    @abstractmethod
    def draw(self, surface: pg.Surface) -> None:
        ...


class Snowflake(Particle):
    def draw(self, surface: pg.Surface) -> None:
        pg.draw.circle(
            surface, 'White', (int(self.pos_x), int(self.pos_y)),
            self.radius
        )

class ParticleSystem():
    def __init__(self, particles: list[Particle]) -> None:
        self.particles = particles

    def update(self, dt: float) -> None:
        for particle in self.particles:
            particle.update(dt)

    def draw(self, surface: pg.Surface) -> None:
        for particle in self.particles:
            particle.draw(surface)