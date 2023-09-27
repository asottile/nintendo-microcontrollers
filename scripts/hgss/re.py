from __future__ import annotations

import argparse
import time

import cv2
import serial

from scripts._alarm import alarm
from scripts.engine import Action
from scripts.engine import always_matches
from scripts.engine import do
from scripts.engine import make_vid
from scripts.engine import Point
from scripts.engine import Press
from scripts.engine import run
from scripts.engine import States
from scripts.engine import Wait
from scripts.thrids import region_colorish
from scripts.thrids import SERIAL_DEFAULT


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--serial', default=SERIAL_DEFAULT)
    args = parser.parse_args()

    t0 = duration = 0.

    def start_timer(vid: object, ser: object) -> None:
        nonlocal t0
        t0 = time.monotonic()

    def stop_timer(vid: object, ser: object) -> None:
        nonlocal duration
        duration = time.monotonic() - t0

    def is_shiny(frame: object) -> bool:
        print(f'delay: {duration:.2f}')

        return duration >= 9.5

    def tap(s: str) -> Action:
        def tap_impl(vid: cv2.VideoCapture, ser: serial.Serial) -> None:
            print(s, end='', flush=True)
            ser.write(s.encode())
            time.sleep(.04)
            ser.write(b'0')
            Wait(.05)(vid, ser)
        return tap_impl

    def nl(vid: object, ser: object) -> None:
        print(flush=True)

    states: States = {
        'INITIAL': (
            (
                region_colorish(
                    Point(y=341, x=861),
                    Point(y=372, x=873),
                    (80, 200, 100),
                    (87, 255, 150),
                    .75,
                ),
                do(tap('w'), Wait(.25), nl),
                'WIGGLE',
            ),
        ),
        'WIGGLE': (
            (
                region_colorish(
                    Point(y=278, x=867),
                    Point(y=301, x=884),
                    (0, 0, 0),
                    (255, 25, 25),
                    .95,
                ),
                do(nl, start_timer),
                'WAIT_FOR_FIGHT',
            ),
            (always_matches, do(tap('a'), tap('w')), 'WIGGLE'),
        ),
        'WAIT_FOR_FIGHT': (
            (
                region_colorish(
                    Point(y=233, x=945),
                    Point(y=256, x=966),
                    (167, 130, 140),
                    (173, 180, 210),
                    .75,
                ),
                stop_timer,
                'DECIDE',
            ),
        ),
        'DECIDE': (
            (is_shiny, do(), 'ALARM'),
            (
                always_matches,
                do(
                    Press('B'), Wait(.25),
                    Press('s'), Wait(.05),
                    Press('d'), Wait(.05),
                    Press('A'), Wait(.05),
                ),
                'INITIAL',
            ),
        ),
        **alarm('ALARM', quiet=False),
    }

    with serial.Serial(args.serial, 9600) as ser:
        run(vid=make_vid(), ser=ser, initial='INITIAL', states=states)


if __name__ == '__main__':
    raise SystemExit(main())
