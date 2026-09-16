#! /usr/bin/env python3
"""Drone state machine and factory used by the simulation engine."""
from enum import Enum


class status_type(Enum):
    """The movement state a :class:`Drone` can be in during a turn."""

    on_way = 'on_way'
    delivered = 'delivered'
    can_move = 'can_move'


class Drone():
    """A single drone following a precomputed path of zone names."""

    def __init__(self, drone_id: int, zone: str, path: list[str]):
        """Create a drone starting at ``zone`` following ``path``.

        Args:
            drone_id: Unique identifier of the drone.
            zone: Name of the zone the drone starts in.
            path: Ordered list of zone names the drone must visit,
                ending at the destination zone.
        """
        self.drone_id: int = drone_id
        self.current_zone: str | None = zone
        self.last_zones: list[str] = ['start_hub']
        self.current_path: list[str] = path
        self.blocked_turns: int = 0
        self.current_status: status_type = (
            status_type.delivered if not path else status_type.can_move
        )

    def peek_next(self) -> str | None:
        """Return the next zone on the path without consuming it."""
        return self.current_path[0] if self.current_path else None

    def mark_blocked(self) -> None:
        """Record that the drone could not move during the current turn."""
        self.blocked_turns += 1

    def move(self, destination: str) -> None:
        """Move the drone directly into ``destination`` for this turn.

        Args:
            destination: Name of the zone the drone enters.
        """
        self.current_path.pop(0)
        self.current_zone = destination
        self.blocked_turns = 0
        self.current_status = (
            status_type.delivered if not self.current_path
            else status_type.can_move
        )

    def start_transit(self) -> str:
        """Begin a multi-turn transit toward a restricted zone.

        Returns:
            The name of the zone the drone departs from.
        """
        source = self.current_zone
        self.current_path.pop(0)
        self.current_zone = None
        self.blocked_turns = 0
        self.current_status = status_type.on_way
        assert source is not None
        return source

    def complete_transit(self, destination: str) -> None:
        """Finish a multi-turn transit by arriving at ``destination``.

        Args:
            destination: Name of the zone the drone arrives in.
        """
        self.current_zone = destination
        self.blocked_turns = 0
        self.current_status = (
            status_type.delivered if not self.current_path
            else status_type.can_move
        )


class DroneFactory():
    """Builds the fleet of :class:`Drone` instances for a simulation."""

    def __init__(self, drone_number: int):
        """Create a factory expecting ``drone_number`` drones.

        Args:
            drone_number: Number of drones the factory must produce.
        """
        self.drone_number = drone_number
        self.drone_list: list[Drone] = []

    def get_drone_list(self, start_hub: str, paths: list[list[str]]) -> None:
        """Populate ``drone_list`` with one drone per path.

        Args:
            start_hub: Name of the zone every drone starts in.
            paths: One path per drone, ordered by drone id.

        Raises:
            ValueError: If the number of paths does not match
                ``drone_number``.
        """
        if len(paths) != self.drone_number:
            raise ValueError(
                f"Expected {self.drone_number} paths, got {len(paths)}"
            )
        for drone_id, path in enumerate(paths):
            self.drone_list.append(Drone(drone_id, start_hub, path[:]))
