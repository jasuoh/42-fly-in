import pygame
from sys import exit
import random


scale = 1.2
HEIGHT = 1000
WIDTH = 1000

class Visualizer():
    def __init__(self):
        pass

    @staticmethod
    def load_img(path: str, alpha=True):
        img = pygame.image.load(path).convert() if alpha is False else pygame.image.load(path).convert_alpha()
        ratio = HEIGHT / img.get_height()
        new_w = int(img.get_width() * ratio)
        return pygame.transform.scale(img, (int(new_w * scale), int(HEIGHT) * scale))

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

def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    screen.fill(('White'))
    b_l = [
    {'img': Visualizer.load_img('assets/1.png', alpha=False), 'speed': 0.2, 'scroll': 0},
    {'img': Visualizer.load_img('assets/2.png'), 'speed': 0.2, 'scroll': 0},
    {'img': Visualizer.load_img('assets/3.png'), 'speed': 0.5, 'scroll': 0},
    {'img': Visualizer.load_img('assets/4.png'), 'speed': 0.8, 'scroll': 0}
    ]
    pygame.display.set_caption('Fly-In')
    blatt = Visualizer.Blatt(screen)
    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    exit()

        for layer in b_l:
            layer['scroll'] += layer['speed']
            w = layer['img'].get_width()
            if layer['scroll'] >= w:
                layer['scroll'] = 0
            screen.blit(layer['img'], (layer['scroll'], -200))
            screen.blit(layer['img'], (layer['scroll'] - w, -200))
        blatt._calculate_new_pos()
        blatt._draw_circle()
        pygame.display.update()
        clock.tick(60)


if __name__ == '__main__':
    main()
