import pygame
from sys import exit
import random


class Visualizer():
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self._screen = None

    def _draw_cons_zones(self):
        ...

    def _animated_background(self, b_l):
        screen = self._screen
        for layer in b_l:
            layer['scroll'] += layer['speed']
            w = layer['img'].get_width()
            if layer['scroll'] >= w:
                layer['scroll'] = 0
            screen.blit(layer['img'], (layer['scroll'], -200))
            screen.blit(layer['img'], (layer['scroll'] - w, -200))

    def _update(self, b_l):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    exit()
        # mouse = pygame.mouse.get_pos()
        # print(mouse)
        # self._animated_background(b_l)

    def run(self):
        pygame.init()
        screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption('Fly-In')
        self._screen = screen
        screen.fill('White')
        b_l = [
        {'img': self.load_img('assets/1.png', alpha=False), 'speed': 0.2, 'scroll': 0},
        {'img': self.load_img('assets/2.png'), 'speed': 0.2, 'scroll': 0},
        {'img': self.load_img('assets/3.png'), 'speed': 0.5, 'scroll': 0},
        {'img': self.load_img('assets/4.png'), 'speed': 0.8, 'scroll': 0}
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

def main() -> None:
    vis = Visualizer(1000, 1000)
    vis.run()

if __name__ == '__main__':
    main()
