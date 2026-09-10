#! /usr/bin/env/python3

import pygame as pg


class Drone_System():
    def __init__(
            self,
            png_specs,
            height
        ):
        self.current_drone_image = None
        self.drone_images = [
            self._load_img(path, height) for path in png_specs
        ]

    @staticmethod
    def _load_img(path: str, height):
        scale = 0.1
        image = pg.image.load(path).convert_alpha()
        ratio = height / image.get_height()
        new_width = int(image.get_width() * ratio)
        new_size = (int(new_width * scale), int(height * scale))
        return pg.transform.scale(image, new_size)


    def print_drone_img(self,surface, pos):
        rect = self.current_drone_image.get_rect(center=pos)
        surface.blit(self.current_drone_image, rect)


    def animate_drone_img(self, surface, pos, drone):
        ...