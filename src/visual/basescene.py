#! /usr/bin/env python3
"""Abstract scene interface shared by every screen of the visualizer."""

from abc import ABC, abstractmethod
from .background import Background
from .particle import ParticleSystem
from ..simulation_engine import Scheduler
from ..input_parsing import Config_Map
import pygame as pg


class Scene(ABC):
    """A single screen of the visualizer's scene stack."""

    @abstractmethod
    def handle_event(self, event: pg.event.Event) -> None:
        """React to a single pygame input event."""
        ...

    @abstractmethod
    def update(self, dt: float) -> None:
        """Advance the scene's state by ``dt`` seconds."""
        pass

    @abstractmethod
    def draw(self, surface: pg.Surface) -> None:
        """Render the scene onto ``surface``."""
        pass

    def next_scene(self) -> str | tuple[str, Scheduler, Config_Map] | None:
        """Return the name of the scene to transition to, if any.

        Returns:
            None to stay on this scene, a scene name, or a
            ``(scene name, scheduler, config)`` tuple when the next
            scene needs a freshly-built simulation.
        """
        return None


class BaseScene(Scene):
    """A scene with a shared parallax background and particle system."""

    def __init__(
        self, background: Background, particles: ParticleSystem
    ) -> None:
        """Create a scene drawing ``background`` and ``particles`` first.

        Args:
            background: Parallax background to draw behind the scene.
            particles: Particle system to draw in front of the
                background.
        """
        self.background = background
        self.particles = particles

    def update(self, dt: float) -> None:
        """Update the background, particles and scene-specific content."""
        self.background.update(dt)
        self.particles.update(dt)
        self.update_content(dt)

    def draw(self, surface: pg.Surface) -> None:
        """Draw the background, particles and scene-specific content."""
        self.background.draw(surface)
        self.particles.draw(surface)
        self.draw_content(surface)

    @abstractmethod
    def update_content(self, dt: float) -> None:
        """Advance scene-specific state by ``dt`` seconds."""
        pass

    @abstractmethod
    def draw_content(self, surface: pg.Surface) -> None:
        """Draw scene-specific content onto ``surface``."""
        pass
