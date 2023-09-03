from __future__ import annotations

import argparse
import difflib
import time

import serial

from scripts._alarm import alarm
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

    t0 = duration = 0.

    def encounter_start(vid: object, ser: object) -> None:
        nonlocal t0
        t0 = time.monotonic()

    def animation_end(vid: object, ser: object) -> None:
        nonlocal duration
        duration = time.monotonic() - t0

    def is_shiny_target(frame: object) -> bool:
        horde_matches = all_match(
            region_colorish(
                Point(y=101, x=306),
                Point(y=124, x=308),
                (55, 150, 100),
                (69, 255, 200),
                .5,
            ),
            region_colorish(
                Point(y=107, x=356),
                Point(y=131, x=360),
                (55, 150, 100),
                (69, 255, 200),
                .5,
            ),
        )

        if horde_matches(frame):
            print('ignoring horde')
            return False

        pokemon = get_text_rotated(
            frame,
            Point(y=152, x=277),
            Point(y=223, x=303),
            invert=True,
        )
        print(f'raw text: {pokemon}')

        ocr_mistakes = {
            'sogup': 'skorupi',
            'ket': 'klefki',
        }
        targets = (
            'watchog', 'foongus', 'pawniard',
            'mightyena', 'skorupi', 'klefki',
            *ocr_mistakes,
        )
        best = difflib.get_close_matches(pokemon.lower(), targets)
        if not best:
            print('=> unknown pokemon')
            return is_shiny(frame)
        else:
            pokemon = best[0]
            pokemon = ocr_mistakes.get(pokemon, pokemon)
            print(f'=> {pokemon}')
            return pokemon == 'watchog' and is_shiny(frame)

    def is_shiny(frame: object) -> bool:
        print(f'delay: {duration:.2f}')

        return duration >= 4

    states: States = {
        'INITIAL': (
            (
                region_colorish(
                    Point(y=220, x=847),
                    Point(y=242, x=868),
                    (18, 40, 160),
                    (26, 100, 220),
                    .75,
                ),
                Press('w', duration=.1),
                'RL',
            ),
        ),
        'RL': (
            (
                region_colorish(
                    Point(y=220, x=847),
                    Point(y=242, x=868),
                    (0, 0, 0),
                    (255, 25, 25),
                    .9,
                ),
                Wait(2),
                'WAIT_FOR_WIDESCREEN',
            ),
            (
                always_matches,
                do(
                    Press('a', duration=.17), Wait(.075),
                    Press('d', duration=.17), Wait(.075),
                ),
                'RL',
            ),
        ),
        'WAIT_FOR_WIDESCREEN': (
            (
                all_match(
                    region_colorish(
                        Point(y=232, x=282),
                        Point(y=407, x=291),
                        (0, 0, 0),
                        (255, 255, 25),
                        .9,
                    ),
                    region_colorish(
                        Point(y=250, x=343),
                        Point(y=345, x=426),
                        (0, 0, 50),
                        (255, 255, 255),
                        .6,
                    ),
                ),
                encounter_start,
                'WAIT_FOR_BALLS',
            ),
        ),
        'WAIT_FOR_BALLS': (
            (
                region_colorish(
                    Point(y=524, x=535),
                    Point(y=642, x=549),
                    (174, 120, 160),
                    (180, 170, 220),
                    .03,
                ),
                animation_end,
                'WAIT_FOR_FIGHT',
            ),
        ),
        'WAIT_FOR_FIGHT': (
            (
                region_colorish(
                    Point(y=307, x=958),
                    Point(y=321, x=973),
                    (175, 150, 180),
                    (180, 170, 210),
                    .7,
                ),
                do(),
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
            (always_matches, do(), 'RUN'),
        ),
        **alarm('ALARM', quiet=False),
    }

    with serial.Serial(args.serial, 9600) as ser:
        run(vid=make_vid(), ser=ser, initial='INITIAL', states=states)


if __name__ == '__main__':
    raise SystemExit(main())
