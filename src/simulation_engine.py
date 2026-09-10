#! /usr/bin/env python3

from .pathfinding_algorithm import Map, Graph
from .drone_factory import Drone, status_type
from .input_parsing import Config_Map, Connection, Zone, zone_types

LinkKey = frozenset[str]


class Scheduler():
    def __init__(
            self, map: Map,
            graph: Graph, drone_list: list[Drone],
            config: Config_Map
    ):
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

    def _connection(self, zone_a: str, zone_b: str) -> Connection:
        return self.connection_dict[frozenset({zone_a, zone_b})]

    def _capacity(self, zone_name: str) -> int | None:
        if zone_name in (self.start, self.end):
            return None
        max_drones = self.zone_dict[zone_name].max_drones
        return max_drones if max_drones is not None else 1

    def _can_enter(self, zone_name: str) -> bool:
        capacity = self._capacity(zone_name)
        if capacity is None:
            return True
        occupied = self.zone_occupancy.get(zone_name, 0)
        reserved = self.zone_reserved.get(zone_name, 0)
        return occupied + reserved < capacity

    def gen_turn(self) -> str:
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
            link_usage[link] = link_usage.get(link, 0) + 1
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
            key=lambda d: len(d.current_path),
        )
        for drone in movable:
            assert drone.current_zone is not None
            source = drone.current_zone
            next_zone_name = drone.current_path[0]
            connection = self._connection(source, next_zone_name)
            link = frozenset({source, next_zone_name})
            link_capacity = connection.max_link_capacity or 1
            if link_usage.get(link, 0) >= link_capacity:
                continue
            next_zone = self.zone_dict[next_zone_name]
            if next_zone.zone == zone_types.restricted:
                if not self._can_enter(next_zone_name):
                    continue
                self.zone_occupancy[source] -= 1
                self.zone_reserved[next_zone_name] += 1
                self.in_flight[drone.drone_id] = (
                    link, next_zone_name, self.current_turn + 1
                )
                drone.last_zones.append(drone.start_transit())
                print(drone.last_zones)
                link_usage[link] = link_usage.get(link, 0) + 1
                moves.append(f"D{drone.drone_id}-{source}-{next_zone_name}")
            else:
                if not self._can_enter(next_zone_name):
                    continue
                self.zone_occupancy[source] -= 1
                self.zone_occupancy[next_zone_name] = (
                    self.zone_occupancy.get(next_zone_name, 0) + 1
                )
                drone.move(next_zone_name)
                link_usage[link] = link_usage.get(link, 0) + 1
                moves.append(f"D{drone.drone_id}-{next_zone_name}")
        return " ".join(moves)

    def run(self) -> list[str]:
        turn_log: list[str] = []
        while not all(
            drone.current_status == status_type.delivered
            for drone in self.drone_list
        ):
            turn_log.append(self.gen_turn())
        return turn_log
