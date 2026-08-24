#! /usr/bin/env python3

from .input_parsing import input_parsing

def main() -> None:
    config = input_parsing()
    print(config.zones)

if __name__ == "__main__":
    main()
