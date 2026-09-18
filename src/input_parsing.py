#! /usr/bin/env python3
"""Parser for the Fly-In map configuration file format."""

from typing import Any
from pydantic import BaseModel, Field, ValidationError
from enum import Enum
import sys


class InvalidZoneType(Exception):
    """Raised when a movement cost is requested for an invalid zone type."""

    def __str__(self) -> str:
        """Return a fixed, human-readable error message."""
        return "Invaid Zone Type Error occured"


class zone_types(Enum):
    """The zone types allowed in a map configuration file."""

    normal = 'normal'
    blocked = 'blocked'
    restricted = 'restricted'
    priority = 'priority'

    @property
    def movement_cost(self) -> int:
        """Return the turn cost of moving into a zone of this type.

        Raises:
            InvalidZoneType: If called on the ``blocked`` zone type,
                which can never be entered.
        """
        match self:
            case zone_types.normal | zone_types.priority:
                return 1
            case zone_types.restricted:
                return 2
            case zone_types.blocked:
                raise InvalidZoneType(
                    'Error in calculating the Zone Cost,'
                    'no Zone cost for restricted Zone!'
                )


class Connection(BaseModel):
    """A bidirectional connection between two zones."""

    zone_a: str = Field(...)
    zone_b: str = Field(...)
    max_link_capacity: int | None = Field(default=None, gt=0)
    color: str = Field(default='White')


class Zone(BaseModel):
    """A single zone (hub) of the drone network."""

    name: str = Field(...)
    coordinates: tuple[int, int] = Field(...)
    zone: zone_types = Field(default=zone_types.normal)
    max_drones: int | None = Field(default=None, gt=0)
    color: str = Field(default='Red')

    @property
    def cost(self) -> int:
        """Return the turn cost of moving into this zone."""
        return self.zone.movement_cost


class InputParsingError(Exception):
    """Raised for any malformed content in a map configuration file."""
    def __init__(self, path: str | None, line: int, message: str):
        """Create a Exception with the path of file,
            line number and Error Message"""
        self.path = path
        self.line = line
        self.message = message
        super().__init__(f"{path}:{line}: {message}")


class Config_Map():
    """Parsed representation of a map configuration file."""

    def __init__(self) -> None:
        """Create an empty configuration, filled by :func:`input_parsing`."""
        self.nb_drones: int | None = None
        self.start: str | None = None
        self.end: str | None = None
        self.zones: list[Zone] | None = None
        self.connections: list[Connection] | None = None
        self._value_dict: dict[str, Any] | None = None
        self.path: str | None = None

    def _input_parsing_and_error_handling(self, path: str) -> None:
        """Read the map file at ``path`` into a raw key/value dictionary.

        Args:
            path: Path to the map configuration file.
        """
        self.path = path
        line_nummer: int = 1
        allowed_keys = [
            "nb_drones", "start_hub", "end_hub", "hub", "connection"
        ]
        value_dict: dict[str, Any] = {}
        value_dict["hub"] = []
        value_dict["connection"] = []
        with open(path) as f:
            data = f.read()
        for line_no, line in enumerate(data.splitlines(), start=1):
            if not line or line.startswith("#"):
                continue
            try:
                key, value = line.split(":", 1)
            except ValueError:
                raise InputParsingError(
                    path, line_no, "Error: Malformed Line"
                )
            if key.strip() not in allowed_keys:
                raise InputParsingError(
                    path, line_no,
                    f"Invalid Argument for Map-file: {key.strip()}"
                )
            if key.strip() in ['start_hub', 'end_hub']:
                if value_dict.get(key.strip()) is not None:
                    raise InputParsingError(
                        path, line_no,
                        f'Error: {key.strip()} should be defined once'
                    )
                value_dict['hub'].append((line_no, value.strip()))
                value_dict[key.strip()] = value.strip().split(' ')[0]
            elif key.strip() not in ["hub", "connection"]:
                try:
                    nb_drones_value = int(value.strip())
                except ValueError:
                    raise InputParsingError(
                        path, line_no, 'Number of Drones should be int'
                    )
                if nb_drones_value < 1 or nb_drones_value > 9999:
                    raise InputParsingError(
                        path, line_no, 'Invalid value for number of drones'
                    )
                if value_dict.get(key.strip()) is not None:
                    raise InputParsingError(
                        path, line_no,
                        'Error: nb_drones should be defined once'
                    )
                else:
                    value_dict[key.strip()] = nb_drones_value
            else:
                value_dict[key.strip()].append((line_no, value.strip()))
            line_nummer = line_no
        if value_dict.get('nb_drones') is None:
            raise InputParsingError(
                path, line_nummer, 'Missing parameter: nb_drones'
            )
        if value_dict.get('start_hub') is None:
            raise InputParsingError(
                path, line_nummer, 'Missing parameter: start_hub'
            )
        if value_dict.get('end_hub') is None:
            raise InputParsingError(
                path, line_nummer, 'Missing parameter: end_hub'
            )
        self._value_dict = value_dict

    def _assign_dict_to_obj(self) -> None:
        """Validate the raw key/value dict into typed zones/connections."""
        assert self._value_dict is not None
        path = self.path
        input_dict = self._value_dict
        allowed_keys_zones = ['zone', 'color', 'max_drones']
        allowed_keys_connections = ['max_link_capacity']
        zones: list[Zone] = []
        connections: list[Connection] = []
        zone_lines: dict[str, int] = {}

        for line_no, raw_zone in input_dict['hub']:
            metadata_dict: dict[str, Any] = {}
            try:
                zone_fields = raw_zone.split(" ")
                metadata_dict["name"] = zone_fields[0]
                metadata_dict["coordinates"] = (
                    zone_fields[1], zone_fields[2]
                )
            except Exception:
                raise InputParsingError(
                    path, line_no, 'Invalid Name or coordinates'
                )
            for i in range(3, len(zone_fields)):
                try:
                    key, value = zone_fields[i].split('=')
                except Exception:
                    raise InputParsingError(
                        path, line_no,
                        "Inputparsing Error: Invalid key"
                    )
                if key.strip().replace('[', '') not in allowed_keys_zones:
                    raise InputParsingError(
                        self.path, line_no,
                        f'Inputparsing Error: "{key.strip().replace("[", "")}"'
                        ' is invalid!'
                    )
                metadata_dict[
                    key.strip().replace("[", '')
                ] = value.strip().replace(']', '')
            try:
                zone = Zone.model_validate(metadata_dict)
            except ValidationError:
                raise InputParsingError(
                    path, line_no,
                    "Error with validating data for Zone"
                )
            if zone.name in zone_lines:
                raise InputParsingError(
                    path, line_no,
                    f'Error: zone "{zone.name}" already defined on line '
                    f'{zone_lines[zone.name]}'
                )
            zone_lines[zone.name] = line_no
            zones.append(zone)
        for line_no, raw_connection in input_dict['connection']:
            metadata_dict = {}
            try:
                if raw_connection.count('-') > 1:
                    raise InputParsingError(
                        self.path, line_no,
                        f"Invalid connection syntax for {raw_connection}"
                    )
                connection_fields = raw_connection.split(" ")
                connection_path = connection_fields[0].split('-')
                metadata_dict['zone_a'] = connection_path[0]
                metadata_dict['zone_b'] = connection_path[1]
            except Exception:
                raise InputParsingError(
                    self.path, line_no,
                    f"Invalid connection syntax for {raw_connection} "
                )
            for i in range(1, len(connection_fields)):
                try:
                    key, value = connection_fields[i].split('=')
                except Exception:
                    raise InputParsingError(
                        self.path, line_no,
                        "Invalid key, value syntax for metadata"
                    )
                if key.strip().replace(
                    "[", ''
                ) not in allowed_keys_connections:
                    raise InputParsingError(
                        self.path, line_no,
                        "Invalid key for metadata"
                    )
                metadata_dict[
                    key.strip().replace("[", '')
                ] = value.strip().replace(']', '')
            try:
                connections.append(Connection.model_validate(metadata_dict))
            except ValidationError:
                raise InputParsingError(
                    self.path, line_no,
                    "Nice Error message"
                )
        try:
            self.start = input_dict['start_hub']
            self.end = input_dict['end_hub']
            self.nb_drones = input_dict['nb_drones']
            self.zones = zones
            self.connections = connections
        except Exception:
            raise InputParsingError(
                path, line_no,
                "Invalid Config File, missing parts"
            )


def input_parsing(path: str) -> Config_Map:
    """Parse the map configuration file at ``path``.

    Args:
        path: Path to the map configuration file.

    Returns:
        The fully parsed configuration.

    On any parsing error, an error message is printed and the process
    exits with status 1.
    """
    config = Config_Map()
    try:
        config._input_parsing_and_error_handling(path=path)
        config._assign_dict_to_obj()
    except BaseException as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    return config
