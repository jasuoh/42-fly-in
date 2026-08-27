#! /usr/bin/env python3
from .input_parsing import Zone
from .pathfinding_algorithm import Graph, Map
from enum import Enum

class status_type(Enum):
    on_way = 'on_way'
    delivered = 'delivered'
    can_move = 'can_move'


class Drone():
    def __init__(self, drone_id, zone, path):
        self.drone_id: int = drone_id
        self.current_zone: Zone = zone
        self.current_path: list[Zone] = path
        self.current_status = status_type.can_move

    def get_next_move(self):
        if len(self.current_path) == 0:
            self.current_status = status_type.delivered
        else:
            return self.current_path[0]


class DroneFactory():
    def __init__(self, drone_number: int):
        self.drone_number = drone_number 
        self.drone_list = []

    def get_drone_list(self, start_hub: Zone, path: list[str]) -> None:
        for i in range(0, self.drone_number):
            self.drone_list.append(Drone(i, start_hub, path[:]))

def main():
    ...