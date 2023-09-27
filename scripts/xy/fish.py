from __future__ import annotations

import argparse
import difflib
import time

import serial

from scripts._alarm import alarm
from scripts._timeout import Timeout
from scripts.engine import all_match
from scripts.engine import always_matches
from scripts.engine import do
from scripts.engine import make_vid
from scripts.engine import Point
from scripts.engine import Press
from scripts.engine import run
from scripts.engine import States
from scripts.engine import Wait
from scripts.thrids import get_text_rotated
from scripts.thrids import region_colorish
from scripts.thrids import SERIAL_DEFAULT


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--serial', default=SERIAL_DEFAULT)
    args = parser.parse_args()

    encounter_timeout = Timeout()

    t0 = duration = 0.

    def record_start(vid: object, ser: object) -> None:
        nonlocal t0
        t0 = time.monotonic()

    def battle_started(vid: object, ser: object) -> None:
        nonlocal duration
        duration = time.monotonic() - t0

    def is_shiny_target(frame: object) -> bool:
        pokemon = get_text_rotated(
            frame,
            Point(y=171, x=289),
            Point(y=239, x=311),
            invert=True,
        )
        print(f'raw text: {pokemon}')

        targets = ('corsola', 'octillery', 'huntail')
        best = difflib.get_close_matches(pokemon.lower(), targets)
        if not best:
            print('=> unknown pokemon')
            return is_shiny(frame)
        else:
            print(f'=> {best[0]}')
            return best[0] == 'huntail' and is_shiny(frame)

    def is_shiny(frame: object) -> bool:
        print(f'delay: {duration:.2f}')

        return duration >= 12

    states: States = {
        'INITIAL': (
            (
                region_colorish(
                    Point(y=263, x=862),
                    Point(y=279, x=877),
                    (20, 75, 130),
                    (24, 100, 160),
                    .75,
                ),
                Press('Y'),
                'WAIT',
            ),
        ),
        'WAIT': (
            (
                region_colorish(
                    Point(y=352, x=382),
                    Point(y=399, x=434),
                    (173, 50, 100),
                    (180, 255, 200),
                    .001,
                ),
                do(Press('A'), encounter_timeout.after(3)),
                'WAIT_FOR_BATTLE',
            ),
        ),
        'WAIT_FOR_BATTLE': (
            (
                region_colorish(
                    Point(y=263, x=862),
                    Point(y=279, x=877),
                    (0, 0, 0),
                    (255, 25, 25),
                    .9,
                ),
                record_start,
                'WAIT_FOR_FIGHT',
            ),
            (
                all_match(
                    encounter_timeout.expired,
                    region_colorish(
                        Point(y=159, x=579),
                        Point(y=184, x=602),
                        (105, 160, 10),
                        (109, 190, 40),
                        .9,
                    ),
                ),
                do(Press('B'), Wait(2)),
                'INITIAL',
            ),
        ),
        'WAIT_FOR_FIGHT': (
            (
                region_colorish(
                    Point(y=335, x=952),
                    Point(y=358, x=973),
                    (175, 160, 100),
                    (180, 255, 150),
                    .7,
                ),
                battle_started,
                'DECIDE',
            ),
        ),
        'DECIDE': (
            (is_shiny_target, do(), 'ALARM'),
            (is_shiny, Press('!', duration=.5), 'RUN'),
            (always_matches, do(), 'RUN'),
        ),
        'RUN': (
            (
                always_matches,
                do(Press('s'), Wait(.25), Press('d'), Wait(.25), Press('A')),
                'INITIAL',
            ),
        ),
        **alarm('ALARM', quiet=False),
    }

    with serial.Serial(args.serial, 9600) as ser:
        run(vid=make_vid(), ser=ser, initial='INITIAL', states=states)


if __name__ == '__main__':
    raise SystemExit(main())
