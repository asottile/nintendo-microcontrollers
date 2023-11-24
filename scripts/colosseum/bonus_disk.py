from __future__ import annotations

import argparse

import serial

from scripts.engine import all_match
from scripts.engine import always_matches
from scripts.engine import Color
from scripts.engine import do
from scripts.engine import make_vid
from scripts.engine import match_px
from scripts.engine import match_text
from scripts.engine import Point
from scripts.engine import Press
from scripts.engine import run
from scripts.engine import States
from scripts.engine import Wait
from scripts.thrids import SERIAL_DEFAULT


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--serial', default=SERIAL_DEFAULT)
    args = parser.parse_args()

    states: States = {
        'INITIAL': (
            (
                match_text(
                    'Play',
                    Point(y=618, x=1013),
                    Point(y=649, x=1111),
                    invert=True,
                ),
                do(Wait(.5), Press('A')),
                'WAIT_FOR_PREPARE',
            ),
        ),
        'WAIT_FOR_PREPARE': (
            (
                all_match(
                    match_px(
                        Point(y=162, x=515),
                        Color(b=245, g=189, r=139),
                    ),
                    match_text(
                        'GameCube',
                        Point(y=525, x=318),
                        Point(y=559, x=542),
                        invert=True,
                    ),
                ),
                do(Press('A'), Wait(.25)),
                'WAIT_FOR_PROGRAM',
            ),
        ),
        'WAIT_FOR_PROGRAM': (
            (
                match_text(
                    'Program',
                    Point(y=489, x=357),
                    Point(y=526, x=533),
                    invert=True,
                ),
                do(Press('A'), Wait(.25)),
                'WAIT_FOR_CONFIRM',
            ),
        ),
        'WAIT_FOR_CONFIRM': (
            (
                match_text(
                    'Yes',
                    Point(y=555, x=572),
                    Point(y=589, x=661),
                    invert=True,
                ),
                do(Press('A'), Wait(1)),
                'WAIT_FOR_INSERT',
            ),
        ),
        'WAIT_FOR_INSERT': (
            (
                all_match(
                    match_px(
                        Point(y=145, x=631),
                        Color(b=246, g=246, r=244),
                    ),
                    match_text(
                        'Nintendo',
                        Point(y=559, x=202),
                        Point(y=594, x=391),
                        invert=True,
                    ),
                ),
                Press('A'),
                'WAIT_FOR_COMMUNICATING',
            ),
        ),
        'WAIT_FOR_COMMUNICATING': (
            (
                all_match(
                    match_px(Point(y=240, x=661), Color(b=247, g=248, r=244)),
                    match_text(
                        'Please',
                        Point(y=451, x=115),
                        Point(y=484, x=257),
                        invert=True,
                    ),
                ),
                do(),
                'RESET',
            ),
        ),
        'RESET': (
            (always_matches, do(Wait(30), Press('*')), 'INITIAL'),
        ),
    }

    with serial.Serial(args.serial, 9600) as ser:
        run(vid=make_vid(), ser=ser, initial='INITIAL', states=states)


if __name__ == '__main__':
    raise SystemExit(main())
