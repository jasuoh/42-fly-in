#! /usr/bin/env python3

from abc import ABC, abstractmethod
from .background import Background
from .particle import ParticleSystem
import pygame as pg


class Scene(ABC):
    @abstractmethod
    def handle_event(self, event: pg.event.Event) -> None:
        ...

    @abstractmethod
    def update(self, dt: float) -> None:
        pass

    @abstractmethod
    def draw(self, surface: pg.Surface) -> None:
        pass

    def next_scene(self) -> str | None:
        return None


class BaseScene(Scene):
    def __init__(
        self, background: Background, particles: ParticleSystem
    ) -> None:
        self.background = background
        self.particles = particles

    def update(self, dt: float) -> None:
        self.background.update(dt)
        self.particles.update(dt)
        self.update_content(dt)

    def draw(self, surface: pg.Surface) -> None:
        self.background.draw(surface)
        self.particles.draw(surface)
        self.draw_content(surface)

    @abstractmethod
    def update_content(self, dt: float) -> None:
        pass

    @abstractmethod
    def draw_content(self, surface: pg.Surface) -> None:
        pass
