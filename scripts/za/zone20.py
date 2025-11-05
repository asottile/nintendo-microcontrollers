from __future__ import annotations

import argparse
import time

import serial

from scripts.engine import Action
from scripts.engine import always_matches
from scripts.engine import do
from scripts.engine import make_vid
from scripts.engine import Point
from scripts.engine import Press
from scripts.engine import run
from scripts.engine import States
from scripts.engine import Wait
from scripts.switch import SERIAL_DEFAULT
from scripts.thrids import region_colorish


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--serial', default=SERIAL_DEFAULT)
    args = parser.parse_args()

    world = region_colorish(
        Point(y=120, x=118),
        Point(y=124, x=122),
        (98, 190, 200),
        (104, 255, 255),
        .95,
    )

    def press(s: str) -> Action:
        def press_impl(vid: object, ser: serial.Serial) -> None:
            print(s, end='', flush=True)
            ser.write(s.encode())
            time.sleep(.1)
            ser.write(b'.')
        return press_impl

    def nl(vid: object, ser: object) -> None:
        print()

    states: States = {
        'INITIAL': (
            (
                world,
                do(
                    Press('w', duration=4),
                    Press('s', duration=4.3), Wait(.25),
                    Press('A'), Wait(.25),
                ),
                'SCREAM',
            ),
        ),
        'SCREAM': (
            (world, nl, 'INITIAL'),
            (always_matches, do(press('A'), Wait(.1)), 'SCREAM'),
        ),
    }

    with serial.Serial(args.serial, 9600) as ser:
        run(vid=make_vid(), ser=ser, initial='INITIAL', states=states)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
