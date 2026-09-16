#! /usr/bin/env python3
"""Command-line argument parsing for the Fly-In CLI."""
import argparse


class ArgParsing():
    """Namespace holding the CLI argument parser."""

    @staticmethod
    def get_flag() -> argparse.Namespace:
        """Parse and return the command-line arguments.

        Returns:
            The parsed arguments, exposing ``maps`` as the optional
            path to a map configuration file.
        """
        argument_parser = argparse.ArgumentParser(description="CLI for Fly-In")
        argument_parser.add_argument(
            "--map", default=None, dest="maps"
        )
        return argument_parser.parse_args()
