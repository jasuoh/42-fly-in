#! /usr/bin/env/python3
"""Horizontally-scrolling, layered parallax background."""

import pygame as pg


class Background():
    """A stack of independently-scrolling parallax image layers."""

    class _Layer():
        """A single scrolling image layer."""

        def __init__(self, image: pg.Surface, speed: float) -> None:
            """Create a layer scrolling ``image`` at ``speed`` pixels/frame.

            Args:
                image: The (already scaled) layer image.
                speed: Horizontal scroll speed multiplier.
            """
            self.image = image
            self.speed = speed
            self.scroll: float = 0.0

    def __init__(
        self,
        height: int,
        layer_specs: list[tuple[str, float, bool]],
    ) -> None:
        """Load and scale every layer described by ``layer_specs``.

        Args:
            height: Target screen height used to scale each layer.
            layer_specs: One (image path, scroll speed, has alpha)
                tuple per layer, ordered back to front.
        """
        self.layers = [
            self._Layer(self._load_img(path, height, has_alpha), speed)
            for path, speed, has_alpha in layer_specs
        ]

    @staticmethod
    def _load_img(
        path: str, height: int, has_alpha: bool
    ) -> pg.Surface:
        """Load the image at ``path`` and scale it to fit ``height``."""
        scale = 1.5
        image = (
            pg.image.load(path).convert_alpha() if has_alpha
            else pg.image.load(path).convert()
        )
        ratio = height / image.get_height()
        new_width = int(image.get_width() * ratio)
        new_size = (int(new_width * scale), int(height * scale))
        return pg.transform.scale(image, new_size)

    def update(self, dt: float) -> None:
        """Advance every layer's scroll position by ``dt`` seconds."""
        for layer in self.layers:
            layer.scroll += layer.speed * dt * 60
            if layer.scroll >= layer.image.get_width():
                layer.scroll = 0

    def draw(self, surface: pg.Surface) -> None:
        """Draw every layer onto ``surface``, tiled to cover the width."""
        for layer in self.layers:
            width = layer.image.get_width()
            surface.blit(layer.image, (layer.scroll, -200))
            surface.blit(layer.image, (layer.scroll - width, -200))
