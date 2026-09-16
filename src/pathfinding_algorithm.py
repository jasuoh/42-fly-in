#! /usr/bin/env python3

from collections.abc import Callable
from .input_parsing import Zone, Connection, zone_types
from heapq import heapify, heappop, heappush

WeightFn = Callable[[str, 'Map.ZoneNode', 'Connection'], float]


class CustomException(Exception):
    def __str__(self):
        return super().__str__()


class Map():
    def __init__(self, dict_zoneNodes=None):
        self.dict_zoneNodes: dict = dict_zoneNodes or {}

    class ZoneNode():
        def __init__(self, zone: 'Zone'):
            self.zone: Zone = zone
            self.neighbor_zones: list[tuple['Map.ZoneNode', 'Connection']] = []

    @classmethod
    def from_config(cls, config):
        zoneNode_dict: dict = {}
        for zone in config.zones:
            if zone.zone == zone_types.blocked:
                continue
            zoneNode_dict[zone.name] = Map.ZoneNode(zone=zone)
        for connection in config.connections:
            node_a = zoneNode_dict.get(connection.zone_a)
            node_b = zoneNode_dict.get(connection.zone_b)
            if not node_a or not node_b:
                raise CustomException('Invalid Connection Node/Zone')
            node_a.neighbor_zones.append((node_b, connection))
            node_b.neighbor_zones.append((node_a, connection))
        return cls(dict_zoneNodes=zoneNode_dict)


class Graph():
    def __init__(self, map: Map):
        self.graph = map.dict_zoneNodes

    @staticmethod
    def _default_weight(
        current: str, neighbor: 'Map.ZoneNode', connection: 'Connection'
    ) -> float:
        """Default edge weight: the destination zone's movement cost."""
        return float(neighbor.zone.cost)

    def shortest_distance(
        self, source: str, weight_fn: WeightFn | None = None
    ) -> tuple[dict[str, float], dict[str, str]]:
        weight_fn = weight_fn or self._default_weight
        distances: dict[str, float] = {
            node: float('inf') for node in self.graph
        }
        predecessors: dict[str, str] = {node: node for node in self.graph}
        distances[source] = 0

        pq: list[tuple[float, str]] = [(0, source)]
        heapify(pq)
        visited: set[str] = set()
        while pq:
            current_distance, current_node = heappop(pq)
            if current_node in visited:
                continue
            visited.add(current_node)
            for neighbor_node, connection in (
                self.graph[current_node].neighbor_zones
            ):
                calc_val = current_distance + weight_fn(
                    current_node, neighbor_node, connection
                )
                if calc_val < distances[neighbor_node.zone.name]:
                    distances[neighbor_node.zone.name] = calc_val
                    predecessors[neighbor_node.zone.name] = current_node
                    heappush(pq, (calc_val, neighbor_node.zone.name))
        return distances, predecessors

    @staticmethod
    def shortest_path(
        start_hub: str, end_hub: str, predecessors: dict
    ) -> list[str]:
        path: list = []
        curr_zone = end_hub
        if end_hub not in predecessors.keys():
            raise CustomException(
                'Invalid config file: No valid path from start to endhub'
            )
        while curr_zone != start_hub:
            path.append(curr_zone)
            curr_zone = predecessors[curr_zone]
        return path[::-1]
