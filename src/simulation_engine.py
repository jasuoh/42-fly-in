#! /usr/bin/env python3
from .input_parsing import Zone

class Drone():
    def __init__(self):
        self.drone_id: int
        self.current_zone: Zone
        self.current_path: list[Zone]

    

class Scheduler():
    def __init__(self):
        ...






def main() -> None:
    print('Hello, World')

if __name__ == "__main__":
    main()