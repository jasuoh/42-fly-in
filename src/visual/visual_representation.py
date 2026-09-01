import pygame
from sys import exit
import random


class Visualizer():
    def __init__(self, width, height, list_zones, list_connections):
        self.width = width
        self.height = height
        self._screen = None
        self.list_zones = list_zones
        self.list_connections = list_connections
        self._static_surface = None
        self._font = None

    def _draw_cons_zones(self):
        w = self.width 
        h = self.height
        surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        zones = {}
        connections = []
        for zone in self.list_zones:
            zones[zone.name] = ((zone.coordinates[0] * 100, zone.coordinates[1] + 1* 100 ), zone.color)
        for c in self.list_connections:
            connections.append(((c.zone_a, c.zone_b), c.color))
        for ((a, b), c) in connections:
            pygame.draw.line(surface, c, zones[a][0], zones[b][0], 5)
        for name, pos in zones.items():
            label = self._font.render(name, True, 'Black')
            label_rect = label.get_rect(center=(pos[0][0], pos[0][1] + 35))
            surface.blit(label, label_rect)
        for _, pos in zones.items():
            pygame.draw.circle(surface, pos[1], pos[0], 25)
        self._static_surface = surface

    def _animated_background(self, b_l):
        screen = self._screen
        for layer in b_l:
            layer['scroll'] += layer['speed']
            w = layer['img'].get_width()
            if layer['scroll'] >= w:
                layer['scroll'] = 0
            screen.blit(layer['img'], (layer['scroll'], -100))
            screen.blit(layer['img'], (layer['scroll'] - w, -100))

    def _update(self, b_l):
        screen = self._screen
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    exit()
        self._animated_background(b_l)
        screen.blit(self._static_surface,(0, 0))

    def run(self):
        pygame.init()
        screen = pygame.display.set_mode((self.width, self.height))
        self._font = pygame.font.SysFont('arial', 16)
        self._draw_cons_zones()
        pygame.display.set_caption('Fly-In')
        self._screen = screen
        screen.fill('White')
        b_l = [
        {'img': self.load_img('src/visual/assets/1.png', alpha=False), 'speed': 0.2, 'scroll': 0},
        {'img': self.load_img('src/visual/assets/2.png'), 'speed': 0.2, 'scroll': 0},
        {'img': self.load_img('src/visual/assets/3.png'), 'speed': 0.5, 'scroll': 0},
        {'img': self.load_img('src/visual/assets/4.png'), 'speed': 0.8, 'scroll': 0}
        ]
        clock = pygame.time.Clock()
        while True:
            self._update(b_l)
            pygame.display.update()
            clock.tick(60)

    
    def load_img(self, path: str, alpha=True, scale= 1):
        img = pygame.image.load(path).convert() if alpha is False \
            else pygame.image.load(path).convert_alpha()
        ratio = self.height / img.get_height()
        new_w = int(img.get_width() * ratio)
        return pygame.transform.scale(
            img, (int(new_w * scale), int(self.height) * scale)
        )

    class Blatt():
        def __init__(self, screen):
            self.screen = screen
            self.pos_x = random.randrange(0, screen.get_width())
            self.pos_y = 0
            self.v = random.randrange(1, 12)
            self.r = random.randrange(10, 30)

        def _calculate_new_pos(self):
            self.pos_y += self.v
            if self.pos_y >= self.screen.get_height():
                self.pos_y = 0
                self.pos_x = random.randrange(1, self.screen.get_width())

        def _draw_circle(self):
            pygame.draw.circle(self.screen, 'White', (self.pos_x, self.pos_y), self.r)
