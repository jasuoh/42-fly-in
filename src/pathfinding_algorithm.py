from .input_parsing import Config_Map, Zone, Connection
from pydantic import BaseModel



class Map(BaseModel):
    dict_zoneNodes: dict = {}

    class ZoneNode(BaseModel):
        zone: Zone | None = None
        neighbor_zones: list[tuple['Map.ZoneNode', 'Connection']] = []

    @classmethod
    def from_config(cls, config):
        zoneNode_dict: dict = {}
        for zone in config.zones:
            zoneNode_dict[zone.name] = Map.ZoneNode(zone=zone, neighbor_zones=[])
        for connection in config.connections:
            node_a = zoneNode_dict.get(connection.zone_a)
            node_b = zoneNode_dict.get(connection.zone_b)
            if not node_a or not node_b:
                return "error"
            node_a.neighbor_zones.append((node_b, connection))
            node_b.neighbor_zones.append((node_a, connection))

        return cls(dict_zoneNodes=zoneNode_dict)