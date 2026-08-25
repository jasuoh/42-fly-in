#! /usr/bin/env python3

from .input_parsing import input_parsing
from .pathfinding_algorithm import Map

def main() -> None:
    config = input_parsing()
    map = Map.from_config(config)
    for node  in map.dict_zoneNodes.values():
        print(node.neighbor_zones)

    
if __name__ == "__main__":
    main()
