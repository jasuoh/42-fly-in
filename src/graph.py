#! /usr/bin/env python3

import sys
import random
import os
from pydantic import BaseModel, model_validator, Field
from .input_parsing import Config_Map

def main() -> None:
    print("Hello, World")

if __name__ == "__main__":
    main()

class Map():
    def __init__(self):
        zonesNodes: list= []

    def convert_Config(self, config: 'Config_Map'):
        for connection in config.connections:
            ...
        for zone in config.zones:
            ...

    
    class ZoneNode():
        def __init__(self):
            ...



    