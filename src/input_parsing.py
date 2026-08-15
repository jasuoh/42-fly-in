#! /usr/bin/env python3

import argparse
from typing import Dict, Any, List, Tuple
from pydantic import BaseModel, Field, model_validator, ValidationError
from enum import Enum
import sys


class Connection(BaseModel):
    zone_a: str = Field(...)
    zone_b: str = Field(...)
    max_link_capacity: int = Field(default=None, ge=0)
    color: str = Field(default=None)

class Config(BaseModel):
    nb_drones: int = None
    start: tuple = None
    end: tuple = None
    zones: List = None
    connections: List = None


class zone_types(Enum):
    normal = 'normal'
    blocked = 'blocked'
    restricted = 'restricted'
    priority = 'priority'


class Zone(BaseModel):
    name: str = Field(...)
    coordinates: tuple[int, int] = Field(...)
    zone: zone_types = Field(default=zone_types.normal)
    max_drones: int | None = Field(default=None, ge=0)
    color: str | None = Field(default=None)


class InputParsingError(Exception):
    """
    Error with parsing the file
    """


def input_parsing_and_error_handling() -> Dict[Any, Any]:
    allowed_keys = ["nb_drones", "start_hub", "end_hub", "hub", "connection"]
    argument_parser = argparse.ArgumentParser(description="CLI for Fly-In")
    argument_parser.add_argument(
        "--map", default="../maps/easy/01_linear_path.txt", dest="maps"
    )
    args = argument_parser.parse_args()
    value_dict: Dict = {}
    value_dict["hub"] = []
    value_dict["connection"] = []
    try:
        with open(args.maps) as f:
            data = f.read()
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
            if key.strip() in ["hub", "connection"]:
                value_dict[key.strip()].append(value.strip())
            else:
                value_dict[key.strip()] = value.strip()
    except Exception as e:
        print(e)
    return value_dict


def assign_dict_to_obj(input_dict: Dict[Any, Any]):
    allowed_keys_zones = ['zone', 'color', 'max_drones']
    allowed_keys_connections = ['max_link_capacity']
    zones = []
    connections = []
    for zone in input_dict['hub']:
        metadata_dict: Dict = {}
        try:
            zone = zone.split(" ")
            metadata_dict["name"] = zone[0]
            metadata_dict["coordinates"] = (zone[1], zone[2])
        except Exception:
            raise InputParsingError('Invalid Name or coordinates')
        for i in range(3, len(zone)):
            try:
                key, value = zone[i].split('=')
            except Exception:
                raise InputParsingError(f"Inputparsing Error: Invalid key")
            if key.strip().replace('[','') not in allowed_keys_zones:
                raise InputParsingError(f'Inputparsing Error: {key.strip().replace("[", "")} is invalid!')
            metadata_dict[key.strip().replace("[", '')] = value.strip().replace(']', '')
        try:
            zones.append(Zone.model_validate(metadata_dict))
        except ValidationError:
            raise InputParsingError("Error with validating data for Zone")
    for connection in input_dict['connection']:
        metadata_dict = {}
        try:
            connection = connection.split(" ")
            if connection.count('-') > 1:
                raise InputParsingError(f"Invalid connection syntax for {connection}")
            connection_path = connection[0].split('-')
            metadata_dict['zone_a'] = connection_path[0]
            metadata_dict['zone_b'] = connection_path[1]
        except Exception:
            raise InputParsingError(f"Invalid connection syntax for {connection} ")
        for i in range(1, len(connection)):
            try:
                key, value = connection[i].split('=')
            except Exception:
                raise InputParsingError("Invalid key, value syntax for metadata")
            if key.strip().replace("[",'') not in allowed_keys_connections:
                raise InputParsingError("Invalid key for metadata")
            metadata_dict[key.strip().replace("[", '')] = value.strip().replace(']','')
        try:
            connections.append(Connection.model_validate(metadata_dict))
        except ValidationError:
            raise InputParsingError("Nice Error message")
    start_hub = input_dict['start_hub'].split(' ')
    end_hub = input_dict['end_hub'].split(' ')
    try:
        return Config(
            nb_drones=input_dict['nb_drones'],
            zones=zones, start=(int(start_hub[1]), int(start_hub[2])),
            end=(int(end_hub[1]), int(end_hub[2])), connections=connections
            )
    except Exception:
        raise InputParsingError("Error with parsing into Config Model")


def main() -> None:
    dictus = input_parsing_and_error_handling()
    try:
        obj = assign_dict_to_obj(dictus)
    except InputParsingError as e:
        print(e)
        sys.exit(1)
    else:
        print(obj)

if __name__ == "__main__":
    main()
