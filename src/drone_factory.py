#! /usr/bin/env python3
from enum import Enum


class status_type(Enum):
    on_way = 'on_way'
    delivered = 'delivered'
    can_move = 'can_move'


class Drone():
    def __init__(self, drone_id: int, zone: str, path: list[str]):
        self.drone_id: int = drone_id
        self.current_zone: str | None = zone
        self.current_path: list[str] = path
        self.current_status: status_type = (
            status_type.delivered if not path else status_type.can_move
        )

    def peek_next(self) -> str | None:
        return self.current_path[0] if self.current_path else None

    def move(self, destination: str) -> None:
        self.current_path.pop(0)
        self.current_zone = destination
        self.current_status = (
            status_type.delivered if not self.current_path
            else status_type.can_move
        )

    def start_transit(self) -> str:
        source = self.current_zone
        self.current_path.pop(0)
        self.current_zone = None
        self.current_status = status_type.on_way
        assert source is not None
        return source

    def complete_transit(self, destination: str) -> None:
        self.current_zone = destination
        self.current_status = (
            status_type.delivered if not self.current_path
            else status_type.can_move
        )


class DroneFactory():
    def __init__(self, drone_number: int):
        self.drone_number = drone_number
        self.drone_list: list[Drone] = []

    def get_drone_list(self, start_hub: str, path: list[str]) -> None:
        for i in range(0, self.drone_number):
            self.drone_list.append(Drone(i, start_hub, path[:]))
