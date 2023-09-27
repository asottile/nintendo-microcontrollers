from __future__ import annotations

import argparse
import os.path
import select
import sys
import time

import serial

from scripts.switch import SERIAL_DEFAULT


def t() -> bytes:
    return f'[{time.time():.3f}]'.encode()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--serial', default=SERIAL_DEFAULT)
    args = parser.parse_args()

    nl = True
    with serial.Serial(args.serial, 9600) as ser:
        ser.write(b'V')
        try:
            rlist = (ser.fd,)
            while True:
                select.select(rlist, (), ())
                if ser.in_waiting:
                    if nl:
                        sys.stdout.buffer.write(t())
                    read = os.read(ser.fd, 100)
                    nl = read.endswith(b'\n')
                    read = read.rstrip(b'\n')
                    sys.stdout.buffer.write(read.replace(b'\n', b'\n' + t()))
                    if nl:
                        sys.stdout.buffer.write(b'\n')
                    sys.stdout.buffer.flush()
        finally:
            ser.write(b'v')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
