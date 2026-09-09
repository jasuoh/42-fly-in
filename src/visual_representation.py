#! /usr/bin/env python3


import sys
import pygame as pg
from .drone_factory import status_type
from .input_parsing import Connection, Zone
from .simulation_engine import Scheduler
from .input_parsing import input_parsing
from .pathfinding_algorithm import Map, Graph
from .drone_factory import DroneFactory
from .visual import BaseScene, ParticleSystem, Background, Snowflake, Scene


class IntroScreen(BaseScene):
    def __init__(
        self,
        background: Background,
        particles: ParticleSystem,
        font: pg.font.Font,
        font_l: pg.font.Font,
        duration: float = 25,
    ) -> None:
        super().__init__(background, particles)
        self.font = font
        self.font_l = font_l
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
        label_b = self.font.render('Fly-In', True, 'mediumpurple1')
        rect_b = label_b.get_rect(center=(surface.get_width() // 2 + 3, surface.get_height() // 3 + 3))
        name = self.font_l.render('by jawosylu', True, 'White')
        name_b = self.font_l.render('by jawosylu', True, 'mediumpurple1')
        name_b_rect = name_b.get_rect(topleft=(3, 3))
        name_rect = name.get_rect(topleft=(0, 0))
        rect = label.get_rect(center=(surface.get_width() // 2, surface.get_height() // 3))
        label_ins = self.font_l.render('Press a key or the mouse to start!', True, 'White')
        rect_ins = label_ins.get_rect(center=(surface.get_width() // 2, surface.get_height() - 100))
        surface.blit(label_ins, rect_ins)
        surface.blit(name_b, name_b_rect)
        surface.blit(label_b, rect_b)
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
    min_radius = 5
    max_radius = 25
    padding_x = 150
    padding_y = 50
    def __init__(
        self,
        background: Background,
        particles: ParticleSystem,
        font: pg.font.Font,
        list_zones: list[Zone],
        list_connections: list[Connection],
        scheduler: Scheduler,
        screen_width: int,
        screen_height: int,
        turn_interval: float = 2
    ) -> None:
        super().__init__(background, particles)
        self.font = font
        self.scheduler = scheduler
        self.turn_interval = turn_interval
        self._elapsed = 0.0
        self._finished = False
        self.margin_x = None
        self.margin_y = None
        self.pause = False
        self.width = screen_width
        self.height = screen_height
        self._screen_positions = None
        self.zone_positions = self._calculate_margin(list_zones)
        self._static_surface = self._draw_static_surface(
            list_zones, list_connections
        )

    def _draw_static_surface(self, list_zones, list_connections):
        surface = pg.Surface(
            (self.width, self.height), pg.SRCALPHA
        )
        self._draw_zones_and_connections(list_zones, list_connections, surface)
        self._draw_log(surface)
        self._draw_legend(surface)
        return surface

    def _draw_log(self, surface: pg.Surface):
        pg.draw.rect(surface, 'White', pg.Rect(self.width - 2 * self.padding_x, self.height - 4 * self.padding_y, 2 * self.padding_x - 25, 4 * self.padding_y - 25), 2, 3) # TODO: White rect is there, but now i need to think about how to implement text, like animated or idk

    def _draw_infos(self):
        ... # TODO: draw infos for each drone on hover

    def _draw_legend(self, surface: pg.Surface) -> None:
        label = self.font.render('Space: Pause/unpause Right arrow: next turn', True, 'White')
        label_rect = label.get_rect(topright=(self.width - 25, 0))
        surface.blit(label, label_rect)

    def _calculate_margin(self, list_zones: list[Zone]):
        max_name_w = max([self.font.size(zone.name)[0] for zone in list_zones])
        name_h = self.font.size(list_zones[0].name)[1]
        self.margin_x = max(self.max_radius, max_name_w // 2) + self.padding_x
        self.margin_y = self.max_radius + name_h + self.padding_y
        return {
            zone.name: (zone.coordinates[0], zone.coordinates[1])
            for zone in list_zones
        }

    def _draw_zones_and_connections(
        self,
        list_zones: list[Zone],
        list_connections: list[Connection],
        surface
    ) -> pg.Surface:
        max_x = max(pos[0] for pos in self.zone_positions.values())
        max_y = max(pos[1] for pos in self.zone_positions.values())
        min_x = min(pos[0] for pos in self.zone_positions.values())
        min_y = min(pos[1] for pos in self.zone_positions.values())
        used_width = self.width - 2 * self.margin_x
        used_height = self.height - 2 * self.margin_y
        bbox_width = max_x - min_x
        bbox_height = max_y - min_y
        if bbox_height == 0:
            bbox_height = 1
        if bbox_width == 0:
            bbox_width = 1
        scale = min(used_width / bbox_width, used_height / bbox_height)
        offset_x = self.margin_x + (
            used_width - bbox_width * scale
        ) / 2 - min_x * scale
        offset_y = self.margin_y + (
            used_height - bbox_height * scale
        ) / 2 - min_y * scale
        screen_positions = {
            zone.name: (
                zone.coordinates[0] * scale + offset_x,
                zone.coordinates[1] * scale + offset_y
            )
            for zone in list_zones
        }
        self._screen_positions = screen_positions
        radius = max(self.min_radius, min(scale * 2, self.max_radius))
        colors = {zone.name: zone.color for zone in list_zones}
        for connection in list_connections:
            start = screen_positions[connection.zone_a]
            end = screen_positions[connection.zone_b]
            pg.draw.line(surface, connection.color, start, end, 5)
        for name, pos in screen_positions.items():
            label = self.font.render(name, True, 'Black')
            label_rect = label.get_rect(center=(pos[0], pos[1] + 35))
            surface.blit(label, label_rect)
        for name, pos in screen_positions.items():
            pg.draw.circle(surface, colors[name] if colors[name] in pg.color.THECOLORS else 'Red', pos, radius)
        return surface

    def handle_event(self, event: pg.event.Event) -> None:
        if event.type == pg.KEYDOWN and event.key == pg.K_RIGHT:
            self._elapsed = self.turn_interval
        elif event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
            self.pause = not self.pause # TODO: Pause Button implementieren
        elif event.type == pg.MOUSEBUTTONDOWN:
            ...
        

    def update_content(self, dt: float) -> None:
        if self._finished or self.pause:
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
        surface.blit(self._static_surface, (0, 0))
        for drone in self.scheduler.drone_list:
            if drone.current_zone is None:
                continue
            pg.draw.circle(surface, 'Black', (self._screen_positions[drone.current_zone]), 8)  # TODO: Drone animation
        turn_count = self.font.render(f"Turn: {str(self.scheduler.current_turn)}", True, 'White')
        turn_rect = turn_count.get_rect(topleft=(0,0))
        surface.blit(turn_count, turn_rect)

    def next_scene(self) -> str | None:
        if self._finished and self.scheduler:
            return 'menu'
        elif self._finished and not self.scheduler:
            return 'map'
        else:
            return None

class MapItem():
    def __init__(self, label: str, path: str, pos: tuple, target: str = 'drone'):
        self.label = label
        self.path = path
        self.pos = pos
        self.target = target

class MapSelection(BaseScene):
        def __init__(self, background, particles, avaiable_maps: list[MapItem], offset_x, offset_y, scale, font):
            self.target = 0
            self.maps = avaiable_maps
            self.offset_x = offset_x
            self.offset_y = offset_y
            self._chosen = None
            self.scale = scale
            self.font = font
            super().__init__(background, particles)

        def handle_event(self, event: pg.event.Event) -> None:
            if event.type == pg.MOUSEMOTION:
                for index, item in enumerate(self.maps):
                    if item.rect and item.rect.collidepoint(event.pos):
                        self.target = index
            elif event.type == pg.MOUSEBUTTONDOWN:
                item = self.maps[self.target]
                if item.rect and item.rect.collidepoint(event.pos):
                    self._chosen = item.target
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_DOWN:
                    self.target = (self.target + 1) % len(self.maps)
                elif event.key == pg.K_UP:
                    self.target = (self.target - 1) % len(self.maps)
                elif event.key == pg.K_RETURN:
                    self._chosen = self.maps[self.target]

        def update_content(self, dt):
            ...

        def draw_content(self, surface):
            for index, item in enumerate(self.maps):
                color = 'Purple' if index == self.target else 'White'
                label = self.font.render(item.label, True, color)
                item.rect = label.get_rect(topleft=item.pos)
                surface.blit(label, item.pos) # TODO: Box um das label

        def next_scene(self):
            if self._chosen is None:
                return None
            config = input_parsing(self._chosen.path)
            map = Map.from_config(config)
            graph = Graph(map)
            F = DroneFactory(int(config.nb_drones))
            _, predecessors = graph.shortest_distance(config.start)
            F.get_drone_list(start_hub=config.start, path=graph.shortest_path(config.start, config.end, predecessors))
            return (self._chosen.target, Scheduler(map, graph, F.drone_list, config), config)


class Visualizer():
    _BACKGROUND_LAYERS: list[tuple[str, float, bool]] = [
        ('src/visual/assets/1.png', 0.2, False),
        ('src/visual/assets/2.png', 0.35, True),
        ('src/visual/assets/3.png', 0.5, True),
        ('src/visual/assets/4.png', 0.8, True),
    ]

    def __init__(
        self,
        list_zones: list[Zone],
        list_connections: list[Connection],
        scheduler: Scheduler | None = None
    ) -> None:
        self.width = 1200
        self.height = 800
        self.list_zones = list_zones
        self.list_connections = list_connections
        self.scheduler = scheduler
        self.scenes: list[tuple[Scene, Scheduler]] = []
        self._font: pg.font.Font | None = None
        self._font_intro: pg.font.Font | None = None


    def _make_scene(self, name: str, scheduler=None, config=None) -> Scene:
        background = Background(self.height, self._BACKGROUND_LAYERS)
        particles = ParticleSystem(
            [Snowflake(self.width, self.height) for _ in range(35)]
        )
        if name == 'intro':
            return IntroScreen(background, particles, self._font_intro, self._font)
        if name == 'menu':
            items = [
                MenuItem('start', (self.width // 5, 150), 'map' if self.scheduler is None else 'drone'),
                MenuItem('back', (self.width // 5, 200), 'intro'),
                MenuItem('quit', (self.width // 5, 250), 'quit')
            ]
            return Menu(background, particles, self._font_intro, items)
        if name == 'drone':
            return DroneScreen(
                background,
                particles,
                self._font,
                self.list_zones if self.list_zones is not None else config.zones,
                self.list_connections if self.list_connections is not None else config.connections,
                self.scheduler if self.scheduler is not None else scheduler,
                self.width,
                self.height
            )
        if name == 'map':
            items = [
                MapItem('Map 01: Linear Path', './maps/easy/01_linear_path.txt', (self.width // 3, 50), 'drone'),
                MapItem('Map 02: Simple Fork', './maps/easy/02_simple_fork.txt', (self.width // 3, 100), 'drone'),
                MapItem('Map 03: Basic Capacity', './maps/easy/03_basic_capacity.txt', (self.width // 3, 150), 'drone')
            ]
            return MapSelection(background, particles, items, None, None, None, self._font)
        raise ValueError(f'Unknown scene: {name}')

    def run(self) -> None:
        pg.init()
        screen = pg.display.set_mode((self.width, self.height), pg.RESIZABLE | pg.SCALED)
        screen.fill('White')
        icon_surface = pg.image.load('src/visual/assets/icon_128.png').convert()
        pg.display.set_icon(icon_surface)
        pg.display.set_caption('Fly-In')
        clock = pg.time.Clock()
        if self._font == None or self._font_intro == None:
            self._font_intro = pg.font.SysFont('consolas', int(45 * self.height / self.width))
            self._font = pg.font.SysFont('consolas', int(30 * self.height / self.width))
        self.scenes = [self._make_scene('intro')]
        while True:
            dt = clock.tick(60) / 1000
            if isinstance(self.scenes[-1], tuple):
                current,_,_ = self.scenes[-1]
            else:
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
                if isinstance(target, tuple):
                    self.scenes.append(self._make_scene(target[0], target[1], target[2]))
                else:
                    self.scenes.append(self._make_scene(target))
