#! /usr/bin/env python3

from .input_parsing import input_parsing
from .argparsing import ArgParsing
from .pathfinding_algorithm import Map, Graph
from .drone_factory import DroneFactory
from .route_planner import RoutePlanner
from .simulation_engine import Scheduler
from .visual_representation import Visualizer


def main() -> None:
    map_path = ArgParsing.get_flag().maps
    if map_path is None:
        Visualizer(None, None).run()
        return

    config = input_parsing(map_path)
    map = Map.from_config(config)
    G = Graph(map)
    planner = RoutePlanner(
        map=map, graph=G, start=config.start, end=config.end
    )
    F = DroneFactory(int(config.nb_drones))
    F.get_drone_list(
        start_hub=config.start,
        paths=planner.assign_paths(int(config.nb_drones)),
    )
    S = Scheduler(map=map, graph=G, drone_list=F.drone_list, config=config)
    Visualizer(
        config.zones, config.connections, S
    ).run()


if __name__ == "__main__":
    main()
