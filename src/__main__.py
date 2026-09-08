#! /usr/bin/env python3

from .input_parsing import input_parsing
from .argparsing import ArgParsing
from .pathfinding_algorithm import Map, Graph
from .drone_factory import DroneFactory
from .simulation_engine import Scheduler
from .visual.visual_representation import Visualizer


def main() -> None:

    readed_path = ArgParsing.get_flag().maps
    config = input_parsing(ArgParsing.get_flag().maps)
    map = Map.from_config(config)
    G = Graph(map)
    _, predecessors = G.shortest_distance(config.start)
    F = DroneFactory(int(config.nb_drones))
    F.get_drone_list(
            start_hub=config.start,
            path=Graph.shortest_path(
                start_hub=config.start,
                end_hub=config.end,
                predecessors=predecessors)
        )
    if readed_path == 'maps/easy/01_linear_path.txt':
        Visualizer(None, None).run()
    else:
        S = Scheduler(map=map, graph=G, drone_list=F.drone_list, config=config)
        Visualizer(config.zones, config.connections, S).run()
    

if __name__ == "__main__":
    main()
