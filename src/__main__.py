#! /usr/bin/env python3

from .input_parsing import input_parsing
from .pathfinding_algorithm import Map, Graph

def main() -> None:
    config = input_parsing()
    map = Map.from_config(config)
    G = Graph(map)
    distances, pred = G.shortest_distance('start')
    print(G.shortest_path(start_hub=config.start, end_hub=config.end, predecessors=pred))

    
if __name__ == "__main__":
    main()
