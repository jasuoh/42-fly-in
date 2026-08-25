from .input_parsing import Zone, Connection, zone_types


class CustomException(Exception):
    '''
    Custom Exception for Error managment for graph theorie
    '''

class Map():
    def __init__(self, dict_zoneNodes = None):
        self.dict_zoneNodes: dict = dict_zoneNodes or {}
    class ZoneNode():
        def __init__(self, zone: 'Zone'):
            self.zone: Zone = zone
            self.neighbor_zones: list[tuple['Map.ZoneNode', 'Connection']] = []
            self.cost: int = 1


    @classmethod
    def from_config(cls, config):
        zoneNode_dict: dict = {}
        for zone in config.zones:
            if zone.zone == zone_types.blocked:
                continue
            zoneNode_dict[zone.name] = Map.ZoneNode(zone=zone)
        for connection in config.connections:
            node_a = zoneNode_dict.get(connection.zone_a)
            node_b = zoneNode_dict.get(connection.zone_b)
            if not node_a or not node_b:
                raise CustomException('Invalid Connection Node/Zone')
            node_a.neighbor_zones.append((node_b, connection))
            node_b.neighbor_zones.append((node_a, connection))
        return cls(dict_zoneNodes=zoneNode_dict)