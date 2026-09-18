#! /usr/bin/env python3
"""Graph representation and shortest-path search over the drone network."""

from collections.abc import Callable
from .input_parsing import Zone, Connection, zone_types, Config_Map
from heapq import heapify, heappop, heappush

WeightFn = Callable[[str, 'Map.ZoneNode', 'Connection'], float]


class CustomException(Exception):
    """Raised for structural errors in the map graph."""

    def __str__(self) -> str:
        """Return the underlying exception message."""
        return super().__str__()


class Map():
    """The drone network as a dictionary of zone name to :class:`ZoneNode`."""

    def __init__(
        self, dict_zoneNodes: dict[str, 'Map.ZoneNode'] | None = None
    ) -> None:
        """Create a map, optionally wrapping an existing node dictionary.

        Args:
            dict_zoneNodes: Mapping of zone name to node. Defaults to
                an empty map.
        """
        self.dict_zoneNodes: dict[str, 'Map.ZoneNode'] = dict_zoneNodes or {}

    class ZoneNode():
        """A zone together with its neighboring zones and connections."""

        def __init__(self, zone: 'Zone'):
            """Create a node wrapping ``zone`` with no neighbors yet.

            Args:
                zone: The zone data this node represents.
            """
            self.zone: Zone = zone
            self.neighbor_zones: list[tuple['Map.ZoneNode', 'Connection']] = []

    @classmethod
    def from_config(cls, config: Config_Map) -> 'Map':
        """Build a :class:`Map` from a parsed :class:`Config_Map`.

        Args:
            config: The parsed map configuration, with zones and
                connections already populated.

        Returns:
            The resulting map, excluding blocked zones.

        Raises:
            CustomException: If a connection references an unknown or
                blocked zone, or if the start/end zone is missing or
                blocked.
        """
        assert config.zones is not None
        assert config.connections is not None
        zoneNode_dict: dict[str, 'Map.ZoneNode'] = {}
        for zone in config.zones:
            if zone.zone == zone_types.blocked:
                continue
            zoneNode_dict[zone.name] = Map.ZoneNode(zone=zone)
        for connection in config.connections:
            node_a = zoneNode_dict.get(connection.zone_a)
            node_b = zoneNode_dict.get(connection.zone_b)
            if not node_a or not node_b:
                raise CustomException(
                    'Invalid Connection Node/Zone'
                )
            node_a.neighbor_zones.append((node_b, connection))
            node_b.neighbor_zones.append((node_a, connection))
        if (config.start not in zoneNode_dict
                or config.end not in zoneNode_dict):
            raise CustomException(
                'Invalid config file: start or end zone is missing or blocked'
            )
        return cls(dict_zoneNodes=zoneNode_dict)


class Graph():
    """Dijkstra-based shortest-path search over a :class:`Map`."""

    def __init__(self, map: Map):
        """Wrap ``map`` for shortest-path queries.

        Args:
            map: The drone network to search over.
        """
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
        """Run Dijkstra's algorithm from ``source``.

        Args:
            source: Name of the zone to search from.
            weight_fn: Optional custom edge-weight function. Defaults
                to the destination zone's movement cost.

        Returns:
            A pair of (distances, predecessors), each keyed by zone
            name.
        """
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
        start_hub: str,
        end_hub: str,
        distances: dict[str, float],
        predecessors: dict[str, str],
    ) -> list[str]:
        """Reconstruct the shortest path from a predecessor map.

        Args:
            start_hub: Name of the starting zone.
            end_hub: Name of the destination zone.
            distances: Distance map produced by :meth:`shortest_distance`,
                used to detect unreachable destinations.
            predecessors: Predecessor map produced by
                :meth:`shortest_distance`.

        Returns:
            The zone names from (excluding) ``start_hub`` to
            ``end_hub``, in traversal order.

        Raises:
            CustomException: If ``end_hub`` is unreachable from
                ``start_hub``.
        """
        if distances.get(end_hub, float('inf')) == float('inf'):
            raise CustomException(
                'Invalid config file: No valid path from start to endhub'
            )
        path: list[str] = []
        curr_zone = end_hub
        while curr_zone != start_hub:
            path.append(curr_zone)
            curr_zone = predecessors[curr_zone]
        return path[::-1]
