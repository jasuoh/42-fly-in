#! /usr/bin/env python3
"""Entry point: parses a map, plans routes, simulates and visualizes them."""

import sys
from .input_parsing import input_parsing
from .argparsing import ArgParsing
from .pathfinding_algorithm import CustomException
from .simulation_engine import build_scheduler
from .visual_representation import Visualizer


class Main:
    @staticmethod
    def main() -> None:
        """Run the Fly-In simulation with/without menu"""
        map_path = ArgParsing.get_flag().maps
        if map_path is None:
            Visualizer(None, None).run()
            return

        config = input_parsing(map_path)
        try:
            S = build_scheduler(config)
        except CustomException as e:
            print(e, file=sys.stderr)
            sys.exit(1)
        Visualizer(
            config.zones, config.connections, S
        ).run()


if __name__ == "__main__":
    Main.main()
