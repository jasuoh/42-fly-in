from .input_parsing import Config_Map, Zone, Connection
from pydantic import BaseModel

class ZoneNode(BaseModel):
    zone: int
    neighbor_zones: list[tuple['Zone', 'Connection']]

    def _assign_Config_to():
        ...
    
    