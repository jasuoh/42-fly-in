#! /usr/bin/env/python3

import pygame as pg


class Drone_System():
    def __init__(
            self,
            png_specs,
            height,
            frame_duration: float = 0.08
    ):
        self.drone_images = [
            self._load_img(path, height) for path in png_specs
        ]
        self.frame_duration = frame_duration
        self._frame_timer = 0.0
        self._frame_index = 0
        self.current_drone_image = self.drone_images[0]

    @staticmethod
    def _load_img(path: str, height):
        scale = 0.07
        image = pg.image.load(path).convert_alpha()
        ratio = height / image.get_height()
        new_width = int(image.get_width() * ratio)
        new_size = (int(new_width * scale), int(height * scale))
        return pg.transform.scale(image, new_size)

    def update(self, dt: float) -> None:
        self._frame_timer += dt
        if self._frame_timer < self.frame_duration:
            return
        self._frame_timer -= self.frame_duration
        self._frame_index = (self._frame_index + 1) % len(self.drone_images)
        self.current_drone_image = self.drone_images[self._frame_index]

    def print_drone_img(self, surface, pos):
        rect = self.current_drone_image.get_rect(center=pos)
        surface.blit(self.current_drone_image, rect)
