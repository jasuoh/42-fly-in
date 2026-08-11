#! /usr/bin/env python3

import argparse
import sys
import os
from typing import Dict, Any, List
from pydantic import BaseModel, Field, model_validator
from enum import Enum

class Config(BaseModel):
    nb_drones: int
    start: Zone
    end: Zone
    different_zones: List[Zone]


class zone_types(Enum):
    normal = 'normal'
    blocked = 'blocked'
    restricted = 'restricted'
    priority = 'priority'


class Zone(BaseModel):
    name: str
    coordinates: tuple[int, int]
    type: zone_types = zone_types.normal
    max_drones: int = 1


class InputParsingError(Exception):
    """
    Error with parsing the file
    """


def input_parsing_and_error_handling() -> Dict[Any, Any]:
    allowed_keys = ["nb_drones","start_hub", "end_hub", "hub", "connection"]
    argument_parser = argparse.ArgumentParser(description="CLI for Fly-In")
    argument_parser.add_argument("--input_map", default="maps/easy/01_linear_path.txt", dest="maps")
    args = argument_parser.parse_args()
    value_dict: Dict = {}
    try:
        with open(args.maps) as f:
            data = f.read()
    except Exception as e:
        print(e)
    for line in data.splitlines():
        if not line or line.startswith("#"):
            continue
        try:
            key, value = line.split(":", 1)
        except ValueError:
            print(f"Warning: Skipping malformed config line: {line}")
            continue
        if key.strip() not in allowed_keys:
            raise InputParsingError("Invalid map-file")
        value_dict[key.strip()] = value.strip()
    return value_dict


def assign_dict_to_obj(input_dict: Dict[Any, Any]) -> List[Zone]:
    config = Config()
    try:
        for index, key, value in enumerate(input_dict):
            print(index, key, value)
    except Exception as e:
        print(e)
    return config

def main() -> None:
    dictus = input_parsing_and_error_handling()
    print(assign_dict_to_obj(dictus))


if __name__ == "__main__":
    main()