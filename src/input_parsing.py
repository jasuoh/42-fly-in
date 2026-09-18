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
                    'no Zone cost for blocked Zone!'
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


def _describe_validation_error(error: ValidationError, subject: str) -> str:
    """Build a readable message from the first pydantic validation error.

    Args:
        error: The validation error raised by a pydantic model.
        subject: What was being validated, e.g. ``"zone"``.

    Returns:
        A message naming the offending field, the reason and the value.
    """
    first = error.errors()[0]
    field = str(first['loc'][0]) if first['loc'] else subject
    return (
        f'Invalid {subject} definition: "{field}": {first["msg"]} '
        f'(got {first["input"]!r})'
    )


def _split_metadata(
    path: str | None, line_no: int, text: str, allowed: list[str]
) -> tuple[list[str], dict[str, str]]:
    """Split a definition into its plain fields and its metadata block.

    The optional block has the form ``[key=value key=value ...]``. There
    can be only one block, it must be closed and it must end the line.

    Args:
        path: Path of the map file, for error messages.
        line_no: Line of the definition, for error messages.
        text: The definition without its ``hub:``/``connection:`` prefix.
        allowed: The metadata keys that are valid for this definition.

    Returns:
        The fields before the block and the key/value pairs inside it.

    Raises:
        InputParsingError: If the brackets or the key/value pairs are
            malformed, or a key is unknown or given twice.
    """
    def fail(message: str) -> InputParsingError:
        return InputParsingError(path, line_no, message)

    opening, closing = text.find('['), text.find(']')
    if opening == -1 and closing == -1:
        return text.split(), {}
    if text.count('[') > 1 or text.count(']') > 1:
        raise fail('Only one metadata block [key=value ...] is allowed')
    if closing == -1:
        raise fail("Metadata block is not closed: missing ']'")
    if opening == -1:
        raise fail("Unexpected ']' without a matching '['")
    if closing < opening:
        raise fail("Unexpected ']' before '['")
    trailing = text[closing + 1:].strip()
    if trailing:
        raise fail(f'Unexpected text after ]: "{trailing}"')
    metadata: dict[str, str] = {}
    for token in text[opening + 1:closing].split():
        key, separator, value = token.partition('=')
        if not separator or not key or '=' in value:
            raise fail(f'Invalid metadata "{token}": expected key=value')
        if key not in allowed:
            raise fail(
                f'Invalid metadata key "{key}" '
                f'(allowed: {", ".join(allowed)})'
            )
        if key in metadata:
            raise fail(f'Metadata key "{key}" is given twice')
        metadata[key] = value
    return text[:opening].split(), metadata


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
        self.zones_lines: dict[str, int] | None = None

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
        first_line_seen = False
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
            if not first_line_seen:
                first_line_seen = True
                if key.strip() != 'nb_drones':
                    raise InputParsingError(
                        path, line_no,
                        'The first line must define nb_drones'
                    )
            if key.strip() in ['start_hub', 'end_hub']:
                if value_dict.get(key.strip()) is not None:
                    raise InputParsingError(
                        path, line_no,
                        f'Error: {key.strip()} should be defined once'
                    )
                value_dict['hub'].append((line_no, value.strip()))
                value_dict[key.strip()] = (value.split() or [''])[0]
            elif key.strip() not in ["hub", "connection"]:
                try:
                    nb_drones_value = int(value.strip())
                except ValueError:
                    raise InputParsingError(
                        path, line_no, 'Number of Drones should be int'
                    )
                if nb_drones_value < 1:
                    raise InputParsingError(
                        path, line_no,
                        'Number of drones must be a positive integer, '
                        f'got {nb_drones_value}'
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
        connection_lines: dict[frozenset[str], int] = {}

        for line_no, raw_zone in input_dict['hub']:
            fields, metadata = _split_metadata(
                path, line_no, raw_zone, allowed_keys_zones
            )
            if len(fields) < 3:
                raise InputParsingError(
                    path, line_no,
                    f'Invalid zone definition "{raw_zone}": '
                    'expected <name> <x> <y> [metadata]'
                )
            if len(fields) > 3:
                raise InputParsingError(
                    path, line_no,
                    f'Unexpected text "{" ".join(fields[3:])}" in the zone '
                    'definition (metadata must be enclosed in [ ])'
                )
            if '-' in fields[0]:
                raise InputParsingError(
                    path, line_no,
                    f'Invalid zone name "{fields[0]}": '
                    'zone names must not contain dashes'
                )
            metadata_dict: dict[str, Any] = {
                "name": fields[0], "coordinates": (fields[1], fields[2]),
                **metadata
            }
            try:
                zone = Zone.model_validate(metadata_dict)
            except ValidationError as error:
                raise InputParsingError(
                    path, line_no, _describe_validation_error(error, 'zone')
                )
            if zone.name in zone_lines:
                raise InputParsingError(
                    path, line_no,
                    f'Zone "{zone.name}" is already defined on line '
                    f'{zone_lines[zone.name]}'
                )
            zone_lines[zone.name] = line_no
            zones.append(zone)
        for line_no, raw_connection in input_dict['connection']:
            fields, metadata = _split_metadata(
                path, line_no, raw_connection, allowed_keys_connections
            )
            if len(fields) > 1:
                raise InputParsingError(
                    path, line_no,
                    f'Unexpected text "{" ".join(fields[1:])}" in the '
                    'connection (metadata must be enclosed in [ ])'
                )
            name_pair = fields[0] if fields else ''
            endpoints = name_pair.split('-')
            if len(endpoints) != 2 or not all(endpoints):
                raise InputParsingError(
                    path, line_no,
                    f'Invalid connection "{name_pair}": expected '
                    '<zone1>-<zone2> (zone names must not contain dashes)'
                )
            zone_a, zone_b = endpoints
            if zone_a == zone_b:
                raise InputParsingError(
                    path, line_no,
                    f'Connection "{name_pair}" links a zone to itself'
                )
            for name in endpoints:
                if name not in zone_lines:
                    raise InputParsingError(
                        path, line_no,
                        f'Connection uses undefined zone "{name}"'
                    )
                if zone_lines[name] > line_no:
                    raise InputParsingError(
                        path, line_no,
                        f'Connection uses zone "{name}" before it is '
                        f'defined (line {zone_lines[name]})'
                    )
            metadata_dict = {
                'zone_a': zone_a, 'zone_b': zone_b, **metadata
            }
            try:
                connection = Connection.model_validate(metadata_dict)
            except ValidationError as error:
                raise InputParsingError(
                    path, line_no,
                    _describe_validation_error(error, 'connection')
                )
            link = frozenset((zone_a, zone_b))
            if link in connection_lines:
                raise InputParsingError(
                    path, line_no,
                    f'Connection "{zone_a}-{zone_b}" is already defined '
                    f'on line {connection_lines[link]}'
                )
            connection_lines[link] = line_no
            connections.append(connection)
        self.start = input_dict['start_hub']
        self.end = input_dict['end_hub']
        self.nb_drones = input_dict['nb_drones']
        self.zones = zones
        self.connections = connections
        self.zones_lines = zone_lines

    def _after_validation_check(self) -> None:
        """Check constraints that need the complete configuration."""
        assert self.zones_lines is not None
        assert self.nb_drones is not None
        assert self.zones is not None
        for zone in self.zones:
            if (
                zone.name == self.start
                and zone.max_drones is not None
                and zone.max_drones < self.nb_drones
            ):
                raise InputParsingError(
                    self.path, self.zones_lines[zone.name],
                    f'Start zone "{zone.name}" has max_drones='
                    f'{zone.max_drones}, less than nb_drones='
                    f'{self.nb_drones}'
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
        config._after_validation_check()
    except BaseException as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    return config
