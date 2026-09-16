#! /usr/bin/env python3

from .pathfinding_algorithm import Map, Graph
from .input_parsing import Zone, Connection, zone_types


CONGESTION_PENALTY_WEIGHT: float = 1.0
PRIORITY_BIAS: float = 0.01


class RoutePlanner():
    def __init__(self, map: Map, graph: Graph, start: str, end: str) -> None:
        self.graph = graph
        self.start = start
        self.end = end
        self._zone_load: dict[str, int] = {
            name: 0 for name in map.dict_zoneNodes
        }
        self._link_load: dict[frozenset[str], int] = {}

    def assign_paths(self, drone_count: int) -> list[list[str]]:
        paths: list[list[str]] = []
        for _ in range(drone_count):
            _, predecessors = self.graph.shortest_distance(
                self.start, self._weight
            )
            path = Graph.shortest_path(self.start, self.end, predecessors)
            self._reserve(path)
            paths.append(path)
        return paths

    def _weight(
        self, current: str, neighbor: 'Map.ZoneNode', connection: 'Connection'
    ) -> float:
        zone = neighbor.zone
        link_key: frozenset[str] = frozenset({current, zone.name})
        link_capacity = (
            connection.max_link_capacity
            if connection.max_link_capacity is not None else 1
        )
        cost = (
            float(zone.cost)
            + self._penalty(
                self._zone_load.get(zone.name, 0), self._zone_capacity(zone)
            )
            + self._penalty(
                self._link_load.get(link_key, 0), link_capacity
            )
        )
        if zone.zone == zone_types.priority:
            cost -= PRIORITY_BIAS
        return cost

    def _zone_capacity(self, zone: 'Zone') -> int | None:
        if zone.name in (self.start, self.end):
            return None
        return zone.max_drones if zone.max_drones is not None else 1

    @staticmethod
    def _penalty(load: int, capacity: int | None) -> float:
        if capacity is None or capacity <= 0:
            return 0.0
        return CONGESTION_PENALTY_WEIGHT * (load / capacity)

    def _reserve(self, path: list[str]) -> None:
        previous = self.start
        for zone_name in path:
            if zone_name not in (self.start, self.end):
                self._zone_load[zone_name] = (
                    self._zone_load.get(zone_name, 0) + 1
                )
            link_key: frozenset[str] = frozenset({previous, zone_name})
            self._link_load[link_key] = self._link_load.get(link_key, 0) + 1
            previous = zone_name
