#! /usr/bin/env python3
"""Turn-by-turn simulation engine enforcing capacity and movement rules."""

from .pathfinding_algorithm import Map, Graph
from .drone_factory import Drone, DroneFactory, status_type
from .input_parsing import Config_Map, Connection, Zone, zone_types
from .route_planner import RoutePlanner

LinkKey = frozenset[str]


class SchedulerDeadlockError(Exception):
    """Raised when no drone can advance during a turn."""

    def __init__(
        self, turn: int, stuck: list[tuple[int, str | None, str | None]]
    ) -> None:
        """Create the error describing every stuck drone.

        Args:
            turn: The turn number at which the deadlock was detected.
            stuck: For each undelivered drone, its id, current zone
                and the zone it is waiting to enter.
        """
        self.turn = turn
        self.stuck = stuck
        super().__init__(self._format())

    def _format(self) -> str:
        """Build a human-readable multi-line deadlock report."""
        lines = [
            f"Deadlock detected at turn {self.turn}: "
            "no drone could advance."
        ]
        for drone_id, current_zone, waiting_for in self.stuck:
            lines.append(
                f"  Drone {drone_id}: at {current_zone}, "
                f"waiting to enter {waiting_for}"
            )
        return "\n".join(lines)


def build_scheduler(config: Config_Map) -> 'Scheduler':
    """Plan routes for ``config`` and return a fresh, unstarted scheduler.

    Args:
        config: The fully parsed map configuration.

    Returns:
        A new :class:`Scheduler` at turn 0.

    Raises:
        CustomException: If the map has no valid path from start to end.
    """
    assert config.start is not None
    assert config.end is not None
    assert config.nb_drones is not None
    map = Map.from_config(config)
    graph = Graph(map)
    planner = RoutePlanner(
        map=map, graph=graph, start=config.start, end=config.end
    )
    paths = planner.assign_paths(int(config.nb_drones))
    factory = DroneFactory(int(config.nb_drones))
    factory.get_drone_list(start_hub=config.start, paths=paths)
    return Scheduler(map, graph, factory.drone_list, config)


class Scheduler():
    """Advances all drones turn by turn, enforcing zone and link capacity."""

    def __init__(
            self, map: Map,
            graph: Graph, drone_list: list[Drone],
            config: Config_Map
    ):
        """Create a scheduler for a fully parsed configuration.

        Args:
            map: The drone network.
            graph: Shortest-path search bound to ``map``.
            drone_list: The drones to simulate, each with a precomputed
                path.
            config: The parsed map configuration (zones, connections,
                start and end zone must be populated).
        """
        assert config.zones is not None
        assert config.connections is not None
        assert config.start is not None
        assert config.end is not None
        self.config = config
        self.map = map
        self.graph = graph
        self.drone_list: list[Drone] = drone_list
        self.drone_by_id: dict[int, Drone] = {
            d.drone_id: d for d in drone_list
        }
        self.zone_dict: dict[str, Zone] = {
            zone.name: zone for zone in config.zones
        }
        self.connection_dict: dict[LinkKey, Connection] = {
            frozenset({c.zone_a, c.zone_b}): c for c in config.connections
        }
        self.start: str = config.start
        self.end: str = config.end
        self.current_turn: int = 0
        self.zone_occupancy: dict[str, int] = {
            name: 0 for name in self.zone_dict
        }
        self.zone_occupancy[self.start] = len(drone_list)
        self.zone_reserved: dict[str, int] = {
            name: 0 for name in self.zone_dict
        }
        self.in_flight: dict[int, tuple[LinkKey, str, int]] = {}
        self.last_link_usage: dict[LinkKey, int] = {}
        self._turn_cap: int = self._compute_turn_cap()
        self._fairness_threshold: int = max(1, len(self.drone_list))

    def _compute_turn_cap(self) -> int:
        """Return an upper bound on turns, used to detect deadlocks."""
        longest_path = max(
            (len(d.current_path) for d in self.drone_list), default=0
        )
        slack = len(self.zone_dict) * len(self.drone_list)
        return longest_path + slack + 1

    def _connection(self, zone_a: str, zone_b: str) -> Connection:
        """Return the connection linking ``zone_a`` and ``zone_b``."""
        return self.connection_dict[frozenset({zone_a, zone_b})]

    def capacity(self, zone_name: str) -> int | None:
        """Return the drone capacity of a zone, or None if unlimited.

        The start and end zones have unlimited capacity.
        """
        if zone_name in (self.start, self.end):
            return None
        max_drones = self.zone_dict[zone_name].max_drones
        return max_drones if max_drones is not None else 1

    def _can_enter(self, zone_name: str) -> bool:
        """Return whether one more drone can enter ``zone_name`` now."""
        capacity = self.capacity(zone_name)
        if capacity is None:
            return True
        occupied = self.zone_occupancy.get(zone_name, 0)
        reserved = self.zone_reserved.get(zone_name, 0)
        return occupied + reserved < capacity

    def link_usage(self, zone_a: str, zone_b: str) -> int:
        """Return how many drones used this link during the last turn.

        Counts both drones that crossed the link this turn and drones
        still in transit on it towards a restricted zone.
        """
        return self.last_link_usage.get(frozenset({zone_a, zone_b}), 0)

    def gen_turn(self) -> str:
        """Advance the simulation by one turn.

        Completes any arriving transits, then greedily moves every
        drone that can legally advance, respecting zone and link
        capacity and prioritizing drones that have been blocked the
        longest.

        Returns:
            The space-separated move log for this turn, in the
            ``D<id>-<zone>`` / ``D<id>-<connection>`` output format.
        """
        self.current_turn += 1
        moves: list[str] = []
        link_usage: dict[LinkKey, int] = {}
        arriving_ids = [
            drone_id for drone_id, (_, _, turn) in self.in_flight.items()
            if turn == self.current_turn
        ]
        for drone_id in arriving_ids:
            link, destination, _ = self.in_flight.pop(drone_id)
            self.zone_reserved[destination] -= 1
            self.zone_occupancy[destination] += 1
            drone = self.drone_by_id[drone_id]
            drone.complete_transit(destination)
            moves.append(f"D{drone.drone_id}-{destination}")
        for link, _, arrival_turn in self.in_flight.values():
            if arrival_turn > self.current_turn:
                link_usage[link] = link_usage.get(link, 0) + 1
        just_landed = set(arriving_ids)
        movable = sorted(
            (
                d for d in self.drone_list
                if d.current_status == status_type.can_move
                and d.drone_id not in just_landed
            ),
            key=lambda d: (
                0 if d.blocked_turns >= self._fairness_threshold else 1,
                len(d.current_path),
            ),
        )
        pending = movable
        progress = True
        while progress and pending:
            progress = False
            blocked: list[Drone] = []
            for drone in pending:
                if self._try_move(drone, link_usage, moves):
                    progress = True
                else:
                    blocked.append(drone)
            pending = blocked
        for drone in pending:
            drone.mark_blocked()
        self.last_link_usage = link_usage
        return " ".join(moves)

    def _try_move(
        self, drone: Drone, link_usage: dict[LinkKey, int], moves: list[str]
    ) -> bool:
        """Move ``drone`` one step along its path if the rules allow it.

        Args:
            drone: The drone to advance.
            link_usage: Per-link usage of the current turn, updated on
                success.
            moves: The current turn's move log, appended to on success.

        Returns:
            True if the drone moved (or entered a transit), False if
            it is blocked by link or zone capacity.
        """
        assert drone.current_zone is not None
        source = drone.current_zone
        next_zone_name = drone.current_path[0]
        connection = self._connection(source, next_zone_name)
        link = frozenset({source, next_zone_name})
        link_capacity = connection.max_link_capacity or 1
        if link_usage.get(link, 0) >= link_capacity:
            return False
        if not self._can_enter(next_zone_name):
            return False
        self.zone_occupancy[source] -= 1
        if self.zone_dict[next_zone_name].zone == zone_types.restricted:
            self.zone_reserved[next_zone_name] += 1
            self.in_flight[drone.drone_id] = (
                link, next_zone_name, self.current_turn + 1
            )
            drone.last_zones.append(drone.start_transit())
            moves.append(f"D{drone.drone_id}-{source}-{next_zone_name}")
        else:
            self.zone_occupancy[next_zone_name] = (
                self.zone_occupancy.get(next_zone_name, 0) + 1
            )
            drone.move(next_zone_name)
            moves.append(f"D{drone.drone_id}-{next_zone_name}")
        link_usage[link] = link_usage.get(link, 0) + 1
        return True

    def _stuck_drones(self) -> list[tuple[int, str | None, str | None]]:
        """Return (id, current zone, awaited zone) for undelivered drones."""
        return [
            (d.drone_id, d.current_zone, d.peek_next())
            for d in self.drone_list
            if d.current_status != status_type.delivered
        ]

    def run(self) -> list[str]:
        """Run the simulation until every drone reaches the end zone.

        Returns:
            The per-turn move log, one entry per turn.

        Raises:
            SchedulerDeadlockError: If a turn produces no moves, or the
                turn cap is exceeded, before all drones are delivered.
        """
        turn_log: list[str] = []
        while not all(
            drone.current_status == status_type.delivered
            for drone in self.drone_list
        ):
            moves = self.gen_turn()
            turn_log.append(moves)
            if not moves or self.current_turn >= self._turn_cap:
                raise SchedulerDeadlockError(
                    self.current_turn, self._stuck_drones()
                )
        return turn_log
