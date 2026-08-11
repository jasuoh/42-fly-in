#! /usr/bin/env python3

from .input_parsing import input_parsing

def main() -> None:
    try:
        config_dict = input_parsing()
        print(config_dict)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    main()