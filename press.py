from __future__ import annotations

import argparse
import time

import serial

from scripts.switch import SERIAL_DEFAULT


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--serial', default=SERIAL_DEFAULT)
    parser.add_argument('--duration', type=float, default=.1)
    parser.add_argument('--count', type=int, default=1)
    parser.add_argument('key')
    args = parser.parse_args()

    with serial.Serial(args.serial, 9600) as ser:
        for _ in range(args.count):
            ser.write(args.key.encode())
            time.sleep(args.duration)
            ser.write(b'.')
            time.sleep(.05)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
