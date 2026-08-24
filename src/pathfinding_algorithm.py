from .input_parsing import Config_Map, Zone, Connection
from pydantic import BaseModel


zone_node = {}

class Map():
    def __init__(self):
        # zone_node = {}
        ...

    class ZoneNode(BaseModel):
        zone: Zone | None = None
        neighbor_zones: list[tuple['Zone', 'Connection']] = []

    @staticmethod
    def assign_Config_to(config: 'Config_Map'):
        for zone in config.zones:
            zone_node[zone.name] = Map.ZoneNode(zone=zone)
            for connection in config.connections:
                if connection.zone_a.name == zone.name:
                    zone_node[zone.name].neighbor_zones.append((connection.zone_b, connection))

    @classmethod
    def from_config(config):
        ...


    def find_neighbor(self):
        ...