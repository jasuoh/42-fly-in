#! /usr/bin/env python3
import argparse


class ArgParsing:
    @staticmethod
    def get_flag() -> argparse.Namespace:
        argument_parser = argparse.ArgumentParser(description="CLI for Fly-In")
        argument_parser.add_argument(
            "--map", default=None, dest="maps"
        )
        return argument_parser.parse_args()
