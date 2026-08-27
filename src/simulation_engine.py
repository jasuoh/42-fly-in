#! /usr/bin/env python3

from .pathfinding_algorithm import Map, Graph
from .drone_factory import Drone
from .input_parsing import Config_Map

class Scheduler():
    def __init__(
            self, map: Map,
            graph: Graph, drone_list: list[Drone],
            config: Config_Map
        ):
        self.map = map
        self.graph = graph
        self.drone_list: list[Drone] = drone_list
        self.zone_dict = {zone.name: zone for zone in config.zones}
        self.connection_dict = {connection.name: connection for connection in config.connections}

    def gen_turn(self):
        for drone in self.drone_list[::-1]:
            next_move = drone.get_next_move()



def main() -> None:
    print('Hello, World')

if __name__ == "__main__":
    main()