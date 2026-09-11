#! /usr/bin/env/python3

import pygame as pg


class Background():
    class _Layer():
        def __init__(self, image: pg.Surface, speed: float) -> None:
            self.image = image
            self.speed = speed
            self.scroll: float = 0.0

    def __init__(
        self,
        height: int,
        layer_specs: list[tuple[str, float, bool]],
    ) -> None:
        self.layers = [
            self._Layer(self._load_img(path, height, has_alpha), speed)
            for path, speed, has_alpha in layer_specs
        ]

    @staticmethod
    def _load_img(
        path: str, height: int, has_alpha: bool
    ) -> pg.Surface:
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
        for layer in self.layers:
            layer.scroll += layer.speed * dt * 60
            if layer.scroll >= layer.image.get_width():
                layer.scroll = 0

    def draw(self, surface: pg.Surface) -> None:
        for layer in self.layers:
            width = layer.image.get_width()
            surface.blit(layer.image, (layer.scroll, -200))
            surface.blit(layer.image, (layer.scroll - width, -200))
