#! /usr/bin/env python3

'''
Visual Representation of the drone network
'''


import random
import sys
import pygame as pg
from abc import ABC, abstractmethod


from ..drone_factory import status_type
from ..input_parsing import Connection, Zone
from ..simulation_engine import Scheduler



class Particle(ABC):
    def __init__(self, screen_width: int, screen_height: int) -> None:
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.pos_x: float = random.uniform(0, screen_width)
        self.pos_y: float = random.uniform(-screen_height, 0)
        self.speed: float = random.uniform(20.0, 80.0)
        self.radius: int = random.randrange(2, 6)

    def update(self, dt: float) -> None:
        self.pos_y += self.speed * dt
        if self.pos_y >= self.screen_height:
            self.pos_y = 0
            self.pos_x = random.uniform(0, self.screen_width)

    @abstractmethod
    def draw(self, surface: pg.Surface) -> None:
        ...


class Snowflake(Particle):
    def draw(self, surface: pg.Surface) -> None:
        pg.draw.circle(
            surface, 'White', (int(self.pos_x), int(self.pos_y)),
            self.radius
        )

class ParticleSystem():
    def __init__(self, particles: list[Particle]) -> None:
        self.particles = particles

    def update(self, dt: float) -> None:
        for particle in self.particles:
            particle.update(dt)

    def draw(self, surface: pg.Surface) -> None:
        for particle in self.particles:
            particle.draw(surface)


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
        scale = 1.2
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


class Scene(ABC):
    @abstractmethod
    def handle_event(self, event: pg.event.Event) -> None:
        ...

    @abstractmethod
    def update(self, dt: float) -> None:
        ...

    @abstractmethod
    def draw(self, surface: pg.Surface) -> None:
        ...

    def next_scene(self) -> str | None:
        return None


class BaseScene(Scene):
    def __init__(
        self, background: Background, particles: ParticleSystem
    ) -> None:
        self.background = background
        self.particles = particles

    def update(self, dt: float) -> None:
        self.background.update(dt)
        self.particles.update(dt)
        self.update_content(dt)

    def draw(self, surface: pg.Surface) -> None:
        self.background.draw(surface)
        self.particles.draw(surface)
        self.draw_content(surface)

    @abstractmethod
    def update_content(self, dt: float) -> None:
        ...

    @abstractmethod
    def draw_content(self, surface: pg.Surface) -> None:
        ...


class IntroScreen(BaseScene):
    def __init__(
        self,
        background: Background,
        particles: ParticleSystem,
        font: pg.font.Font,
        duration: float = 25,
    ) -> None:
        super().__init__(background, particles)
        self.font = font
        self.duration = duration
        self._elapsed = 0.0

    def handle_event(self, event: pg.event.Event) -> None:
        if event.type == pg.KEYDOWN:
            self._elapsed = self.duration
        elif event.type == pg.MOUSEBUTTONDOWN:
            self._elapsed = self.duration

    def update_content(self, dt: float) -> None:
        self._elapsed += dt

    def draw_content(self, surface: pg.Surface) -> None:
        label = self.font.render('Fly-In', True, 'White')
        name = self.font.render('by jawosylu', True, 'White')
        name_rect = name.get_rect(topleft=(0,0))
        rect = label.get_rect(
            center=(surface.get_width() // 2, surface.get_height() // 3)
        )
        surface.blit(label, rect)
        surface.blit(name, name_rect)

    def next_scene(self) -> str | None:
        return 'menu' if self._elapsed >= self.duration else None


class MenuItem():
    def __init__(self, label: str, pos, target: str) -> None:
        self.label = label
        self.pos = pos
        self.target = target
        self.rect: pg.Rect | None = None


class Menu(BaseScene):
    def __init__(
        self,
        background: Background,
        particles: ParticleSystem,
        font: pg.font.Font,
        items: list[MenuItem],
    ) -> None:
        super().__init__(background, particles)
        self.font = font
        self.items = items
        self.selected = 0
        self._chosen: str | None = None

    def handle_event(self, event: pg.event.Event) -> None:
        if event.type == pg.MOUSEMOTION:
            for index, item in enumerate(self.items):
                if item.rect and item.rect.collidepoint(event.pos):
                    self.selected = index
        elif event.type == pg.MOUSEBUTTONDOWN:
            item = self.items[self.selected]
            if item.rect and item.rect.collidepoint(event.pos):
                self._chosen = item.target
        elif event.type == pg.KEYDOWN:
            if event.key == pg.K_DOWN:
                self.selected = (self.selected + 1) % len(self.items)
            elif event.key == pg.K_UP:
                self.selected = (self.selected - 1) % len(self.items)
            elif event.key == pg.K_RETURN:
                self._chosen = self.items[self.selected].target

    def update_content(self, dt: float) -> None:
        ...

    def draw_content(self, surface: pg.Surface) -> None:
        for index, item in enumerate(self.items):
            color = 'Purple' if index == self.selected else 'White'
            label = self.font.render(item.label, True, color)
            item.rect = label.get_rect(topleft=item.pos)
            surface.blit(label, item.pos)

    def next_scene(self) -> str | None:
        return self._chosen


class DroneScreen(BaseScene):
    def __init__(
        self,
        background: Background,
        particles: ParticleSystem,
        font: pg.font.Font,
        list_zones: list[Zone],
        list_connections: list[Connection],
        scheduler: Scheduler,
        turn_interval: float = 2,
    ) -> None:
        super().__init__(background, particles)
        self.font = font
        self.scheduler = scheduler
        self.turn_interval = turn_interval
        self._elapsed = 0.0
        self._finished = False
        self.zone_positions = self._compute_positions(list_zones)
        self._static_surface = self._draw_zones_and_connections(
            list_zones, list_connections
        )

    def _compute_positions(
        self, list_zones: list[Zone]
    ) -> dict:
        return {
            zone.name: (
                zone.coordinates[0] * (25 * len(list_zones)) + 100,
                zone.coordinates[1] * (25 * len(list_zones)) + 100,
            )
            for zone in list_zones
        }

    def _draw_zones_and_connections(
        self,
        list_zones: list[Zone],
        list_connections: list[Connection],
    ) -> pg.Surface:
        max_x = max(pos[0] for pos in self.zone_positions.values())
        max_y = max(pos[1] for pos in self.zone_positions.values())
        surface = pg.Surface(
            (max_x + 100, max_y + 100), pg.SRCALPHA
        )
        colors = {zone.name: zone.color or 'Red' for zone in list_zones}
        for connection in list_connections:
            start = self.zone_positions[connection.zone_a]
            end = self.zone_positions[connection.zone_b]
            pg.draw.line(surface, connection.color, start, end, 5)
        for name, pos in self.zone_positions.items():
            label = self.font.render(name, True, 'Black')
            label_rect = label.get_rect(center=(pos[0], pos[1] + 35))
            surface.blit(label, label_rect)
        for name, pos in self.zone_positions.items():
            pg.draw.circle(surface, colors[name], pos, 25)
        win_size = surface.get_size() if len(list_zones) < 10 else (0.5 * max_x + 100, 0.5 * max_y + 100)
        return pg.transform.smoothscale(surface, win_size) # TODO: richtig scalen auf die res

    def handle_event(self, event: pg.event.Event) -> None:
        if event.type == pg.KEYDOWN:
            ...
        

    def update_content(self, dt: float) -> None:
        if self._finished:
            return
        self._elapsed += dt
        if self._elapsed < self.turn_interval:
            return
        self._elapsed = 0.0
        self.scheduler.gen_turn()
        self._finished = all(
            drone.current_status == status_type.delivered
            for drone in self.scheduler.drone_list
        )

    def draw_content(self, surface: pg.Surface) -> None:
        surface.blit(self._static_surface, (200, 200))
        for drone in self.scheduler.drone_list:
            if drone.current_zone is None:
                continue
            pos = self.zone_positions[drone.current_zone]
            pg.draw.circle(surface, 'Black', (pos[0] + 200, pos[1] + 200), 8)
        turn_count = self.font.render(str(self.scheduler.current_turn), True, 'White')
        turn_rect = turn_count.get_rect(topleft=(0,0))
        surface.blit(turn_count, turn_rect)

    def next_scene(self) -> str | None:
        return 'menu' if self._finished else None


class Visualizer():
    _BACKGROUND_LAYERS: list[tuple[str, float, bool]] = [
        ('src/visual/assets/1.png', 0.2, False),
        ('src/visual/assets/2.png', 0.35, True),
        ('src/visual/assets/3.png', 0.5, True),
        ('src/visual/assets/4.png', 0.8, True),
    ]
    def __init__(
        
        self,
        width: int,
        height: int,
        list_zones: list[Zone],
        list_connections: list[Connection],
        scheduler: Scheduler,
    ) -> None:
        self.width = width
        self.height = height
        self.list_zones = list_zones
        self.list_connections = list_connections
        self.scheduler = scheduler
        self.scenes: list[Scene] = []
        self._font: pg.font.Font | None = None
        self._font_intro: pg.font.Font | None = None


    def _make_scene(self, name: str) -> Scene:
        background = Background(self.height, self._BACKGROUND_LAYERS)
        particles = ParticleSystem([Snowflake(self.width, self.height) for _ in range(35)])
        if name == 'intro':
            return IntroScreen(background, particles, self._font_intro)
        if name == 'menu':
            items = [
                MenuItem('start', (self.height // 4, 150), 'drone'),
                MenuItem('back', (self.height // 4, 200), 'intro'),
                MenuItem('quit', (self.height // 4, 250), 'quit')
            ]
            return Menu(background, particles, self._font_intro, items)
        if name == 'drone':
            return DroneScreen(
                background,
                particles,
                self._font,
                self.list_zones,
                self.list_connections,
                self.scheduler,
            )
        raise ValueError(f'Unknown scene: {name}')

    def run(self) -> None:
        pg.init()
        screen = pg.display.set_mode((self.width, self.height))
        icon_surface = pg.image.load('src/visual/assets/icon_128.png').convert()
        pg.display.set_icon(icon_surface)
        pg.display.set_caption('Fly-In')
        clock = pg.time.Clock()
        self._font_intro = pg.font.SysFont('consolas', 25)
        self._font = pg.font.SysFont('consolas', 18)

        self.scenes = [self._make_scene('intro')]
        while True:
            dt = clock.tick(60) / 1000
            current = self.scenes[-1]
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    sys.exit()
                if (
                    event.type == pg.KEYDOWN
                    and event.key == pg.K_ESCAPE
                ):
                    pg.quit()
                    sys.exit()
                current.handle_event(event)

            current.update(dt)
            current.draw(screen)
            pg.display.update()

            target = current.next_scene()
            if target == 'quit':
                pg.quit()
                sys.exit()
            elif target:
                self.scenes.append(self._make_scene(target))
