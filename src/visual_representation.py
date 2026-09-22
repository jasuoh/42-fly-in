#! /usr/bin/env python3
"""Pygame scenes: intro, menus, map selection and the live simulation view."""


import sys
import pygame as pg
from .drone_factory import Drone, status_type
from .input_parsing import Connection, Zone
from .simulation_engine import Scheduler, build_scheduler
from .input_parsing import input_parsing, Config_Map
from .pathfinding_algorithm import CustomException
from .visual import (
    BaseScene, ParticleSystem,
    Background, Snowflake, Scene, Drone_System
)


class IntroScreen(BaseScene):
    """The splash screen shown when the application starts."""

    def __init__(
        self,
        background: Background,
        particles: ParticleSystem,
        font: pg.font.Font,
        font_l: pg.font.Font,
        duration: float = 25,
    ) -> None:
        """Create the intro screen.

        Args:
            background: Parallax background to draw behind the scene.
            particles: Particle system to draw in front of the
                background.
            font: Font used for the title.
            font_l: Font used for the smaller labels.
            duration: Seconds to wait before auto-advancing to the menu.
        """
        super().__init__(background, particles)
        self.font = font
        self.font_l = font_l
        self.duration = duration
        self._elapsed = 0.0

    def handle_event(self, event: pg.event.Event) -> None:
        """Skip straight to the menu on any key press or click."""
        if event.type == pg.KEYDOWN:
            self._elapsed = self.duration
        elif event.type == pg.MOUSEBUTTONDOWN:
            self._elapsed = self.duration

    def update_content(self, dt: float) -> None:
        """Advance the auto-advance timer by ``dt`` seconds."""
        self._elapsed += dt

    def draw_content(self, surface: pg.Surface) -> None:
        """Draw the title, author and instructions onto ``surface``."""
        label = self.font.render('Fly-In', True, 'White')
        label_b = self.font.render('Fly-In', True, 'mediumpurple1')
        rect_b = label_b.get_rect(
            center=(
                surface.get_width() // 2 + 3, surface.get_height() // 3 + 3
            )
        )
        name = self.font_l.render('by jawosylu', True, 'White')
        name_b = self.font_l.render('by jawosylu', True, 'mediumpurple1')
        name_b_rect = name_b.get_rect(topleft=(3, 3))
        name_rect = name.get_rect(topleft=(0, 0))
        rect = label.get_rect(center=(
            surface.get_width() // 2, surface.get_height() // 3
        ))
        label_ins = self.font_l.render(
            'Press a key or the mouse to start!', True, 'White'
        )
        rect_ins = label_ins.get_rect(center=(
            surface.get_width() // 2, surface.get_height() - 100
        ))
        surface.blit(label_ins, rect_ins)
        surface.blit(name_b, name_b_rect)
        surface.blit(label_b, rect_b)
        surface.blit(label, rect)
        surface.blit(name, name_rect)

    def next_scene(self) -> str | None:
        """Move to the menu once the auto-advance duration has elapsed."""
        return 'menu' if self._elapsed >= self.duration else None


class MenuItem():
    """A single clickable entry of the main :class:`Menu`."""

    def __init__(self, label: str, pos: tuple[int, int], target: str) -> None:
        """Create a menu item.

        Args:
            label: Text displayed for this entry.
            pos: Top-left screen position of the label.
            target: Scene name to transition to when chosen.
        """
        self.label = label
        self.pos = pos
        self.target = target
        self.rect: pg.Rect | None = None


class Menu(BaseScene):
    """The main menu: start, back and quit."""

    def __init__(
        self,
        background: Background,
        particles: ParticleSystem,
        font: pg.font.Font,
        items: list[MenuItem],
    ) -> None:
        """Create the menu with the given entries.

        Args:
            background: Parallax background to draw behind the scene.
            particles: Particle system to draw in front of the
                background.
            font: Font used to render the entries.
            items: The selectable menu entries.
        """
        super().__init__(background, particles)
        self.font = font
        self.items = items
        self.selected = 0
        self._chosen: str | None = None

    def handle_event(self, event: pg.event.Event) -> None:
        """Handle keyboard/mouse navigation and selection."""
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
        """The menu has no time-based state to update."""
        ...

    def draw_content(self, surface: pg.Surface) -> None:
        """Draw every menu entry, highlighting the selected one."""
        for index, item in enumerate(self.items):
            color = 'Purple' if index == self.selected else 'White'
            label = self.font.render(item.label, True, color)
            item.rect = label.get_rect(topleft=item.pos)
            surface.blit(label, item.pos)

    def next_scene(self) -> str | None:
        """Return the target of the chosen entry, if any."""
        return self._chosen


class DroneScreen(BaseScene):
    """The live simulation view: network layout, drones and turn log."""

    min_scalling = 5
    max_scalling = 35
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
        dronesystem: Drone_System,
        turn_interval: float = 2
    ) -> None:
        """Create the simulation view for a fully built scheduler.

        Args:
            background: Parallax background to draw behind the scene.
            particles: Particle system to draw in front of the
                background.
            font: Font used for all labels.
            list_zones: Every zone of the current map.
            list_connections: Every connection of the current map.
            scheduler: The simulation to advance and display.
            screen_width: Width of the drawing surface in pixels.
            screen_height: Height of the drawing surface in pixels.
            dronesystem: Shared animated drone sprite.
            turn_interval: Seconds of animation between two turns.
        """
        super().__init__(background, particles)
        self.font = font
        self.scheduler = scheduler
        self.turn_interval = turn_interval
        self._elapsed = 0.0
        self._finished = False
        self.margin_x: int | None = None
        self.margin_y: int | None = None
        self.pause = False
        self.end = False
        self.current_turn: str | None = None
        self._target_turn = 0
        self._turn_logs: list[str] = []
        self.width = screen_width
        self.height = screen_height
        self.dronesystem = dronesystem
        self._retry_label = 'Retry'
        self._retry_hover = False
        label_w, label_h = self.font.size(self._retry_label)
        self._retry_rect = pg.Rect(10, 35, label_w + 20, label_h + 10)
        self._screen_positions: dict[str, tuple[float, float]] | None = None
        self._zone_capacities: dict[str, int] = {
            zone.name: cap
            for zone in list_zones
            if (cap := self.scheduler.capacity(zone.name)) is not None
        }
        self._link_capacities: dict[tuple[str, str], int] = {
            (con.zone_a, con.zone_b): con.max_link_capacity
            for con in list_connections
            if con.max_link_capacity is not None
        }
        self.zone_positions = self._calculate_margin(list_zones)
        self._static_surface = self._draw_static_surface(
            list_zones, list_connections
        )
        assert self._screen_positions is not None
        self._connection_midpoints: dict[
            tuple[str, str], tuple[float, float]
        ] = {
            (zone_a, zone_b): (
                (
                    self._screen_positions[zone_a][0]
                    + self._screen_positions[zone_b][0]
                ) * 0.5,
                (
                    self._screen_positions[zone_a][1]
                    + self._screen_positions[zone_b][1]
                ) * 0.5,
            )
            for zone_a, zone_b in self._link_capacities
        }
        self._prev_positions: dict[int, tuple[float, float]] = (
            self._capture_positions()
        )
        self._target_positions: dict[int, tuple[float, float]] = (
            self._prev_positions
        )

    def _draw_static_surface(
        self, list_zones: list[Zone], list_connections: list[Connection]
    ) -> pg.Surface:
        """Pre-render the parts of the view that never change: network, log
        frame and legend."""
        surface = pg.Surface(
            (self.width, self.height), pg.SRCALPHA
        )
        self._draw_zones_and_connections(list_zones, list_connections, surface)
        self._draw_log(surface)
        self._draw_legend(surface)
        return surface

    def _draw_log(self, surface: pg.Surface) -> None:
        """Draw the empty frame the turn log is later printed into."""
        pg.draw.rect(
            surface, 'White',
            pg.Rect(
                self.width - 2 * self.padding_x,
                self.height - 5 * self.padding_y,
                2 * self.padding_x - 25, 5 * self.padding_y - 25
            ), 3, 3
        )

    def _draw_legend(self, surface: pg.Surface) -> None:
        """Draw the keyboard shortcut hint in the top-right corner."""
        label = self.font.render(
            'Space: Pause/unpause Right arrow: next turn '
            'Left arrow: previous turn R: retry',
            True, 'White'
        )
        label_rect = label.get_rect(topright=(self.width - 25, 0))
        surface.blit(label, label_rect)

    def _calculate_margin(
        self, list_zones: list[Zone]
    ) -> dict[str, tuple[int, int]]:
        """Compute screen margins from label sizes and return raw zone
        coordinates.

        Args:
            list_zones: Every zone of the current map.

        Returns:
            Each zone's raw (unscaled) coordinates, keyed by name.
        """
        max_name_w = max([self.font.size(zone.name)[0] for zone in list_zones])
        name_h = self.font.size(list_zones[0].name)[1]
        self.margin_x = max(
            self.max_scalling, max_name_w // 2
        ) + self.padding_x
        self.margin_y = self.max_scalling + name_h + self.padding_y
        return {
            zone.name: (zone.coordinates[0], zone.coordinates[1])
            for zone in list_zones
        }

    def _draw_zones_and_connections(
        self,
        list_zones: list[Zone],
        list_connections: list[Connection],
        surface: pg.Surface
    ) -> pg.Surface:
        """Draw every connection and zone, scaled to fit the screen.

        Also records the resulting screen-space positions in
        ``self._screen_positions`` for later use by drone drawing.
        """
        assert self.margin_x is not None
        assert self.margin_y is not None
        zone_png = pg.image.load(
            'src/visual/assets/zone/zone.png'
        ).convert_alpha()
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
        colors = {zone.name: zone.color for zone in list_zones}
        for connection in list_connections:
            start = screen_positions[connection.zone_a]
            end = screen_positions[connection.zone_b]
            pg.draw.line(surface, connection.color, start, end, 3)
        for name, pos in screen_positions.items():
            label = self.font.render(name, True, 'Black')
            label_rect = label.get_rect(center=(pos[0], pos[1] + 50))
            surface.blit(label, label_rect)
        for name, pos in screen_positions.items():
            s = self.tint(zone_png, colors[name])
            rect = s.get_rect(center=pos)
            surface.blit(s, rect)
        return surface

    def tint(self, surface: pg.Surface, color: str) -> pg.Surface:
        """Return a copy of ``surface`` multiplied by ``color``.

        An unknown color name does not abort the visualization: a warning
        is printed and the surface is left untinted.
        """
        try:
            parsed_color = pg.Color(color)
        except ValueError:
            print(
                f"Warning: unknown color '{color}', using the default",
                file=sys.stderr
            )
            parsed_color = pg.Color('White')
        s = surface.copy()
        s.fill(parsed_color, special_flags=pg.BLEND_RGBA_MULT)
        return s

    def handle_event(self, event: pg.event.Event) -> None:
        """Handle turn stepping, pause toggling and returning to the menu."""
        if event.type == pg.KEYDOWN and event.key == pg.K_RIGHT:
            if self.pause:
                self._step_forward()
                self._elapsed = self.turn_interval
        elif event.type == pg.KEYDOWN and event.key == pg.K_LEFT:
            if self.pause:
                self._step_backward()
                self._elapsed = self.turn_interval
        elif event.type == pg.KEYDOWN:
            if event.key == pg.K_SPACE:
                self.pause = not self.pause
            elif event.key == pg.K_e and self._finished:
                self.end = True
            elif event.key == pg.K_r:
                self._retry()
        elif event.type == pg.MOUSEMOTION:
            self._retry_hover = self._retry_rect.collidepoint(event.pos)
        elif event.type == pg.MOUSEBUTTONDOWN:
            if self._retry_rect.collidepoint(event.pos):
                self._retry()

    def _retry(self) -> None:
        """Restart the simulation from turn 0 with a fresh scheduler."""
        self._goto_turn(0)
        self._elapsed = 0.0
        self.pause = False
        self.end = False

    def _step_forward(self) -> None:
        """Advance the live simulation by exactly one turn.

        Reuses the current scheduler in place (cheap): every forward
        step, whether driven by the autoplay timer or by a manual
        ``Right arrow`` press, always starts from the turn the
        scheduler already sits at.
        """
        if self._finished:
            return
        self._prev_positions = self._capture_positions()
        self.current_turn = self.scheduler.gen_turn()
        self._turn_logs.append(self.current_turn)
        self._target_turn += 1
        self._target_positions = self._capture_positions()
        print(self.current_turn)
        self._finished = all(
            drone.current_status == status_type.delivered
            for drone in self.scheduler.drone_list
        )

    def _step_backward(self) -> None:
        """Step back to the previous turn, if any."""
        if self._target_turn <= 0:
            return
        self._goto_turn(self._target_turn - 1)

    def _goto_turn(self, turn: int) -> None:
        """Rebuild the scheduler and replay it up to ``turn``.

        The simulation is fully deterministic (no randomness in
        routing or scheduling), so re-planning from scratch and
        replaying ``turn`` turns always reproduces the exact state
        the live scheduler had at that point. Replaying is cheap
        enough for every map this project ships with (at most a few
        dozen turns), so this trades a little recomputation for not
        having to snapshot the full scheduler state after every turn.
        """
        self._prev_positions = self._capture_positions()
        self.scheduler = build_scheduler(self.scheduler.config)
        self._turn_logs = [self.scheduler.gen_turn() for _ in range(turn)]
        self._target_turn = turn
        self.current_turn = self._turn_logs[-1] if self._turn_logs else None
        self._target_positions = self._capture_positions()
        self._finished = all(
            drone.current_status == status_type.delivered
            for drone in self.scheduler.drone_list
        )

    def update_content(self, dt: float) -> None:
        """Advance drone animation and, once per interval, the simulation."""
        if self.end or self.pause:
            return
        self.dronesystem.update(dt)
        self._elapsed += dt
        if self._finished:
            return
        if self._elapsed < self.turn_interval:
            return
        self._elapsed = 0.0
        self._step_forward()

    def _final_zone_pos(self, drone: Drone) -> tuple[float, float] | None:
        """Return the screen position of the zone ``drone`` currently
        occupies or is transiting toward."""
        if self._screen_positions is None:
            return None
        if drone.current_zone is not None:
            return self._screen_positions[drone.current_zone]
        in_flight = self.scheduler.in_flight.get(drone.drone_id)
        if in_flight is None:
            return None
        _, destination, _ = in_flight
        return self._screen_positions[destination]

    def _capture_positions(self) -> dict[int, tuple[float, float]]:
        """Snapshot every drone's current target position, keyed by id."""
        if self._screen_positions is None:
            return {}
        positions = {}
        for drone in self.scheduler.drone_list:
            pos = self._final_zone_pos(drone)
            if pos is not None:
                positions[drone.drone_id] = pos
        return positions

    def _drone_screen_pos(self, drone: Drone) -> tuple[float, float] | None:
        """Return ``drone``'s interpolated screen position for this frame."""
        target = self._target_positions.get(drone.drone_id)
        if target is None:
            return self._final_zone_pos(drone)
        origin = self._prev_positions.get(drone.drone_id, target)
        progress = min(1.0, self._elapsed / self.turn_interval)
        return (
            origin[0] + (target[0] - origin[0]) * progress,
            origin[1] + (target[1] - origin[1]) * progress,
        )

    def draw_content(self, surface: pg.Surface) -> None:
        """Draw the network, every drone, the turn counter and the log."""
        surface.blit(self._static_surface, (0, 0))
        for drone in self.scheduler.drone_list:
            pos = self._drone_screen_pos(drone)
            if pos is None:
                continue
            self.dronesystem.print_drone_img(surface, pos)
        turn_count = self.font.render(
            f"Turn: {str(self.scheduler.current_turn)}", True, 'White'
        )
        turn_rect = turn_count.get_rect(topleft=(0, 0))
        surface.blit(turn_count, turn_rect)
        self._draw_retry_button(surface)
        x = 0
        label_surface = pg.Surface(
            (2 * self.padding_x - 25,
             5 * self.padding_y - 25), pg.SRCALPHA
        )
        if self.current_turn is not None:
            for turn in self.current_turn.split(' '):
                label = self.font.render(turn, True, 'White')
                label_rect = label.get_rect(topleft=(5, x))
                x += 25
                label_surface.blit(label, label_rect)
            surface.blit(
                label_surface, (
                    self.width - 2 * self.padding_x,
                    self.height - 5 * self.padding_y
                )
            )
        self._draw_capacities(surface)

    def _draw_retry_button(self, surface: pg.Surface) -> None:
        """Draw the retry button, highlighted while hovered."""
        color = 'Purple' if self._retry_hover else 'White'
        pg.draw.rect(surface, color, self._retry_rect, 2, 4)
        label = self.font.render(self._retry_label, True, color)
        surface.blit(label, label.get_rect(center=self._retry_rect.center))

    def _draw_capacities(self, surface: pg.Surface) -> None:
        """Draw zone occupancy and link usage labels over the network."""
        if self._screen_positions is None:
            return
        for name, cap in self._zone_capacities.items():
            pos = self._screen_positions[name]
            occupancy = self.scheduler.zone_occupancy.get(name, 0)
            label = self.font.render(
                f"{occupancy}/{cap}", True, 'White'
            )
            label_rect = label.get_rect(center=(pos[0], pos[1] + 75))
            surface.blit(label, label_rect)
        for (zone_a, zone_b), cap in self._link_capacities.items():
            (x, y) = self._connection_midpoints[(zone_a, zone_b)]
            usage = self.scheduler.link_usage_in_flight(zone_a, zone_b)
            label = self.font.render(
                f"{usage}/{cap}", True, 'White'
            )
            label_rect = label.get_rect(center=(x, y + 25))
            surface.blit(label, label_rect)

    def next_scene(self) -> str | None:
        """Return to the menu once the user ends the finished simulation."""
        if self.end and self.scheduler:
            return 'menu'
        else:
            return None


class MapItem():
    """A single selectable entry of the :class:`MapSelection` screen."""

    def __init__(
        self, label: str,
        path: str, pos: tuple[int, int],
        target: str = 'drone'
    ):
        """Create a map selection entry.

        Args:
            label: Text displayed for this entry.
            path: Path to the map configuration file it loads.
            pos: Top-left screen position of the label.
            target: Scene name to transition to when chosen.
        """
        self.label = label
        self.path = path
        self.pos = pos
        self.target = target
        self.rect: pg.Rect | None = None


class MapSelection(BaseScene):
    """The screen listing every bundled map, ready to be simulated."""

    def __init__(
        self,
        background: Background,
        particles: ParticleSystem,
        avaiable_maps: list[MapItem],
        offset_x: int | None, offset_y: int | None,
        scale: float | None, font: pg.font.Font
    ):
        """Create the map selection screen.

        Args:
            background: Parallax background to draw behind the scene.
            particles: Particle system to draw in front of the
                background.
            avaiable_maps: The selectable map entries.
            offset_x: Unused horizontal layout offset, reserved for
                future layout tweaks.
            offset_y: Unused vertical layout offset, reserved for
                future layout tweaks.
            scale: Unused layout scale, reserved for future layout
                tweaks.
            font: Font used to render the entries.
        """
        self.target = 0
        self.maps = avaiable_maps
        self.offset_x = offset_x
        self.offset_y = offset_y
        self._chosen: MapItem | None = None
        self.scale = scale
        self.font = font
        super().__init__(background, particles)

    def handle_event(self, event: pg.event.Event) -> None:
        """Handle keyboard/mouse navigation and map selection."""
        if event.type == pg.MOUSEMOTION:
            for index, item in enumerate(self.maps):
                if item.rect and item.rect.collidepoint(event.pos):
                    self.target = index
        elif event.type == pg.MOUSEBUTTONDOWN:
            item = self.maps[self.target]
            if item.rect and item.rect.collidepoint(event.pos):
                self._chosen = self.maps[self.target]
        elif event.type == pg.KEYDOWN:
            if event.key == pg.K_DOWN:
                self.target = (self.target + 1) % len(self.maps)
            elif event.key == pg.K_UP:
                self.target = (self.target - 1) % len(self.maps)
            elif event.key == pg.K_RETURN:
                self._chosen = self.maps[self.target]

    def update_content(self, dt: float) -> None:
        """The map selection screen has no time-based state to update."""
        ...

    def draw_content(self, surface: pg.Surface) -> None:
        """Draw every map entry, highlighting the targeted one."""
        for index, item in enumerate(self.maps):
            color = 'Purple' if index == self.target else 'White'
            label = self.font.render(item.label, True, color)
            item.rect = label.get_rect(topleft=item.pos)
            surface.blit(label, item.pos)

    def next_scene(self) -> str | tuple[str, Scheduler, Config_Map] | None:
        """Parse and plan the chosen map, then hand off to the drone screen.

        Returns:
            None while no map has been chosen yet, otherwise a
            ``(scene name, scheduler, config)`` tuple ready for
            :class:`DroneScreen`.
        """
        if self._chosen is None:
            return None
        config = input_parsing(self._chosen.path)
        try:
            scheduler = build_scheduler(config)
        except CustomException as e:
            print(e, file=sys.stderr)
            sys.exit(1)
        return (self._chosen.target, scheduler, config)


class Visualizer():
    """Owns the pygame window and drives the scene stack."""

    _BACKGROUND_LAYERS: list[tuple[str, float, bool]] = [
        ('src/visual/assets/background/1.png', 0.2, False),
        ('src/visual/assets/background/2.png', 0.35, True),
        ('src/visual/assets/background/3.png', 0.5, True),
        ('src/visual/assets/background/4.png', 0.8, True),
    ]

    _Drone_layers: list[str] = [
        f'src/visual/assets/drone/drone_move_{i}.png' for i in range(6)
    ]

    def __init__(
        self,
        list_zones: list[Zone] | None,
        list_connections: list[Connection] | None,
        scheduler: Scheduler | None = None
    ) -> None:
        """Create the visualizer.

        Args:
            list_zones: Zones of a map already chosen on the command
                line, or None to let the user pick one from the menu.
            list_connections: Connections of a map already chosen on
                the command line, or None to let the user pick one
                from the menu.
            scheduler: Simulation for a map already chosen on the
                command line, or None to let the user pick one from
                the menu.
        """
        self.width = 1920
        self.height = 1080
        self.list_zones = list_zones
        self.list_connections = list_connections
        self.scheduler = scheduler
        self.scenes: list[Scene] = []
        self._font: pg.font.Font | None = None
        self._font_intro: pg.font.Font | None = None

    def _make_scene(
        self,
        name: str,
        scheduler: Scheduler | None = None,
        config: Config_Map | None = None
    ) -> Scene:
        """Build the scene named ``name``.

        Args:
            name: One of ``intro``, ``menu``, ``drone`` or ``map``.
            scheduler: Simulation to display, used by the ``drone``
                scene when none was given on the command line.
            config: Map configuration matching ``scheduler``, used by
                the ``drone`` scene when none was given on the command
                line.

        Returns:
            The newly built scene.

        Raises:
            ValueError: If ``name`` is not a known scene.
        """
        assert self._font is not None
        assert self._font_intro is not None
        background = Background(self.height, self._BACKGROUND_LAYERS)
        particles = ParticleSystem(
            [Snowflake(self.width, self.height) for _ in range(35)]
        )
        drone_system = Drone_System(self._Drone_layers, self.height)
        if name == 'intro':
            return IntroScreen(
                background, particles, self._font_intro, self._font
            )
        if name == 'menu':
            items = [
                MenuItem('start', (
                    self.width // 5, 150
                ), 'map' if self.scheduler is None else 'drone'),
                MenuItem('back', (self.width // 5, 200), 'intro'),
                MenuItem('quit', (self.width // 5, 250), 'quit')
            ]
            return Menu(background, particles, self._font_intro, items)
        if name == 'drone':
            zones = (
                self.list_zones if self.list_zones is not None
                else (config.zones if config is not None else None)
            )
            connections = (
                self.list_connections if self.list_connections is not None
                else (config.connections if config is not None else None)
            )
            active_scheduler = (
                build_scheduler(self.scheduler.config)
                if self.scheduler is not None else scheduler
            )
            assert zones is not None
            assert connections is not None
            assert active_scheduler is not None
            return DroneScreen(
                background,
                particles,
                self._font,
                zones,
                connections,
                active_scheduler,
                self.width,
                self.height,
                drone_system
            )
        if name == 'map':
            map_items = [
                MapItem(
                    'Map 01: Linear Path',
                    './maps/easy/01_linear_path.txt', (
                        self.width // 8, 50
                    ), 'drone'
                ),
                MapItem(
                    'Map 02: Simple Fork',
                    './maps/easy/02_simple_fork.txt', (
                        self.width // 8, 100
                    ), 'drone'
                ),
                MapItem(
                    'Map 03: Basic Capacity',
                    './maps/easy/03_basic_capacity.txt', (
                        self.width // 8, 150
                    ), 'drone'
                ),
                MapItem(
                    'Map 04: Dead End Trap',
                    './maps/medium/01_dead_end_trap.txt', (
                        self.width // 8, 200
                    ), 'drone'
                ),
                MapItem(
                    'Map 05: Circular Loop',
                    './maps/medium/02_circular_loop.txt', (
                        self.width // 8, 250
                    ), 'drone'
                ),
                MapItem(
                    'Map 06: Priority Puzzle',
                    './maps/medium/03_priority_puzzle.txt', (
                        self.width // 8, 300
                    ), 'drone'
                ),
                MapItem(
                    'Map 07: Maze Nightmare',
                    './maps/hard/01_maze_nightmare.txt', (
                        self.width // 8, 350
                    ), 'drone'
                ),
                MapItem(
                    'Map 08: Capacity Hell',
                    './maps/hard/02_capacity_hell.txt', (
                        self.width // 8, 400
                    ), 'drone'
                ),
                MapItem(
                    'Map 09: Ultimate Challenge',
                    './maps/hard/03_ultimate_challenge.txt', (
                        self.width // 8, 450
                    ), 'drone'
                )
            ]
            return MapSelection(
                background, particles, map_items, None, None, None,
                self._font
            )
        raise ValueError(f'Unknown scene: {name}')

    def _initial_window_size(self) -> tuple[int, int]:
        """Pick a startup window size that fits the user's screen.

        Keeps the 16:9 aspect ratio every layout constant in this
        module assumes (backgrounds, padding, font scaling), just
        sized to fit the desktop instead of hardcoded to 1920x1080,
        which can be larger than the actual screen.
        """
        try:
            desktop_width, desktop_height = pg.display.get_desktop_sizes()[0]
        except (pg.error, IndexError):
            return self.width, self.height
        margin = 0.85
        width = int(desktop_width * margin)
        height = width * 9 // 16
        if height > desktop_height * margin:
            height = int(desktop_height * margin)
            width = height * 16 // 9
        return width, height

    def run(self) -> None:
        """Open the window and run the main loop until the user quits."""
        pg.init()
        self.width, self.height = self._initial_window_size()
        screen = pg.display.set_mode(
            (self.width, self.height), pg.RESIZABLE | pg.SCALED
        )
        screen.fill('White')
        icon_surface = pg.image.load(
            'src/visual/assets/icon_128.png'
        ).convert()
        pg.display.set_icon(icon_surface)
        pg.display.set_caption('Fly-In')
        clock = pg.time.Clock()
        if self._font is None or self._font_intro is None:
            self._font_intro = pg.font.Font(
                'src/visual/assets/font.ttf', int(
                    24 * self.width / self.height
                )
            )
            self._font = pg.font.Font(
                'src/visual/assets/font.ttf', int(
                    12 * self.width / self.height
                )
            )
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
                if isinstance(target, tuple):
                    self.scenes.append(self._make_scene(
                        target[0], target[1], target[2]
                    ))
                else:
                    self.scenes.append(self._make_scene(target))
