from __future__ import annotations

import argparse
import time

import serial

from scripts.switch import SERIAL_DEFAULT


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--serial', default=SERIAL_DEFAULT)
    args = parser.parse_args()

    with serial.Serial(args.serial, 9600) as ser:
        while True:
            ser.write(b'l')
            time.sleep(.2)
            ser.write(b'A')
            time.sleep(.1)
            ser.write(b'.')
            time.sleep(.05)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
