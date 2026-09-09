#! /usr/bin/env/python3

import pygame as pg


class Drone_System():
    def __init__(self):
        self.drone_image = self.get_drone_image()

    @staticmethod
    def _load_img(path: str, height):
        scale = 0.1
        image = pg.image.load(path).convert_alpha()
        ratio = height / image.get_height()
        new_width = int(image.get_width() * ratio)
        new_size = (int(new_width * scale), int(height * scale))
        return pg.transform.scale(image, new_size)

    def get_drone_image(self):
        return self._load_img('src/visual/assets/drone/drone.png', 1080)

    def print_drone_img(self,surface, pos):
        rect = self.drone_image.get_rect(center=pos)
        surface.blit(self.drone_image, rect)
