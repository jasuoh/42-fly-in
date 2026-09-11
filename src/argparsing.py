#! /usr/bin/env python3
import argparse


class ArgParsing:
    def __init__(self):
        pass

    @staticmethod
    def get_flag():
        argument_parser = argparse.ArgumentParser(description="CLI for Fly-In")
        argument_parser.add_argument(
            "--map", default="maps/easy/01_linear_path.txt", dest="maps"
        )
        return argument_parser.parse_args()
