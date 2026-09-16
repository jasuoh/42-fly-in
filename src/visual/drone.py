#! /usr/bin/env/python3
"""Animated drone sprite used by the simulation screen."""

import pygame as pg


class Drone_System():
    """Shared frame-animated drone sprite drawn for every drone."""

    def __init__(
            self,
            png_specs: list[str],
            height: int,
            frame_duration: float = 0.08
    ):
        """Load the animation frames and start the animation clock.

        Args:
            png_specs: Paths to the animation frame images, in order.
            height: Target screen height used to scale each frame.
            frame_duration: Seconds each animation frame is shown for.
        """
        self.drone_images = [
            self._load_img(path, height) for path in png_specs
        ]
        self.frame_duration = frame_duration
        self._frame_timer = 0.0
        self._frame_index = 0
        self.current_drone_image = self.drone_images[0]

    @staticmethod
    def _load_img(path: str, height: int) -> pg.Surface:
        """Load the image at ``path`` and scale it to fit ``height``."""
        scale = 0.07
        image = pg.image.load(path).convert_alpha()
        ratio = height / image.get_height()
        new_width = int(image.get_width() * ratio)
        new_size = (int(new_width * scale), int(height * scale))
        return pg.transform.scale(image, new_size)

    def update(self, dt: float) -> None:
        """Advance the animation clock by ``dt`` seconds."""
        self._frame_timer += dt
        if self._frame_timer < self.frame_duration:
            return
        self._frame_timer -= self.frame_duration
        self._frame_index = (self._frame_index + 1) % len(self.drone_images)
        self.current_drone_image = self.drone_images[self._frame_index]

    def print_drone_img(
        self, surface: pg.Surface, pos: tuple[float, float]
    ) -> None:
        """Draw the current animation frame centered on ``pos``.

        Args:
            surface: Surface to draw onto.
            pos: Screen-space center position of the sprite.
        """
        rect = self.current_drone_image.get_rect(center=pos)
        surface.blit(self.current_drone_image, rect)
