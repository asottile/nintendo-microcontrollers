from __future__ import annotations

import argparse
import os.path
from typing import NamedTuple

import cv2
import numpy
import serial

from scripts.engine import always_matches
from scripts.engine import Color
from scripts.engine import do
from scripts.engine import getframe
from scripts.engine import make_vid
from scripts.engine import match_px
from scripts.engine import match_text
from scripts.engine import Point
from scripts.engine import Press
from scripts.engine import run
from scripts.engine import States
from scripts.engine import Wait
from scripts.sv._bootup import bootup
from scripts.sv._bootup import world
from scripts.sv._raid import large_star_count
from scripts.sv._raid import raid_pokemon
from scripts.sv._raid import raid_type
from scripts.sv._skip_day import skip_day
from scripts.switch import alarm
from scripts.switch import reset
from scripts.switch import SERIAL_DEFAULT


class HSVRange(NamedTuple):
    low: tuple[int, int, int]
    hi: tuple[int, int, int]


COLORS: dict[str, tuple[HSVRange, ...]] = {
    'bug': (
        HSVRange((13, 200, 65), (16, 220, 75)),
    ),
    'dark': (
        HSVRange((173, 185, 65), (178, 210, 80)),
    ),
    'dragon': (
        HSVRange((166, 135, 65), (169, 175, 75)),
    ),
    'electric': (
        HSVRange((13, 180, 70), (17, 205, 80)),
    ),
    'fairy': (
        HSVRange((166, 195, 70), (170, 225, 80)),
    ),
    'fighting': (
        HSVRange((5, 245, 65), (8, 255, 75)),
    ),
    'fire': (
        HSVRange((0, 195, 70), (4, 220, 80)),
    ),
    'flying': (
        HSVRange((0, 105, 55), (3, 130, 70)),
        HSVRange((177, 105, 55), (180, 130, 70)),
    ),
    'ghost': (
        HSVRange((171, 165, 60), (175, 190, 75)),
    ),
    'grass': (
        HSVRange((14, 185, 60), (19, 210, 75)),
    ),
    'ground': (
        HSVRange((4, 210, 65), (8, 230, 75)),
    ),
    'ice': (
        HSVRange((174, 90, 65), (179, 125, 80)),
    ),
    'normal': (
        HSVRange((0, 120, 65), (2, 150, 75)),
        HSVRange((178, 120, 65), (180, 150, 75)),
    ),
    'poison': (
        HSVRange((167, 185, 65), (170, 215, 75)),
    ),
    'psychic': (
        HSVRange((171, 165, 60), (175, 210, 75)),
    ),
    'rock': (
        HSVRange((1, 155, 65), (8, 175, 80)),
    ),
    'steel': (
        HSVRange((0, 120, 65), (2, 150, 75)),
        HSVRange((178, 120, 65), (180, 150, 75)),
    ),
    'water': (
        HSVRange((166, 90, 60), (171, 130, 70)),
    ),
}


def _filter_armarouge(f: numpy.ndarray, color: str) -> numpy.ndarray:
    hsv = cv2.cvtColor(f, cv2.COLOR_BGR2HSV)

    im = None
    for low, hi in COLORS[color]:
        filt = cv2.inRange(hsv, low, hi)
        if im is None:
            im = filt
        else:
            im = cv2.bitwise_or(im, filt)
    return im


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--serial', default=SERIAL_DEFAULT)
    parser.add_argument('--targets-file', default='sv-targets')
    args = parser.parse_args()

    with open(args.targets_file) as f:
        targets = frozenset(f.read().splitlines())

    counter = 30

    def counter_expired(frame: object) -> bool:
        return counter == 0

    def counter_decrement(vid: object, ser: object) -> None:
        nonlocal counter
        counter -= 1

    def counter_reset(vid: object, ser: object) -> None:
        nonlocal counter
        counter = 30

    key = pokemon = tp = ''

    def is_desired_target(frame: numpy.ndarray) -> bool:
        nonlocal key, pokemon, tp

        stars = large_star_count(frame)
        pokemon = raid_pokemon(frame)
        tp = raid_type(frame)
        key = f'{stars} {pokemon}'
        print(f'raid is: {key} ({tp})')
        return key in targets

    maybe_shiny = True

    def check(vid: cv2.VideoCapture, ser: serial.Serial) -> None:
        nonlocal maybe_shiny

        frame = getframe(vid)
        n = sum(1 for f in os.listdir('imgs') if f.startswith(f'{key}-'))

        os.makedirs('imgs', exist_ok=True)
        os.makedirs(f'{pokemon}/{tp}', exist_ok=True)
        cv2.imwrite(f'imgs/{key}-{n:04}.png', frame)
        cv2.imwrite(f'{pokemon}/{tp}/{key}-{n:04}.png', frame)
        cv2.imwrite('mon.png', frame)

        maybe_shiny = True

        if pokemon != 'armarouge':
            print(f'not armarouge: {pokemon}')
            return

        if tp not in COLORS:
            print(f'unknown type: {tp}')
            return

        eye = _filter_armarouge(frame[103:132, 839:892], tp)
        eye_count = numpy.count_nonzero(eye)
        if eye_count >= 600:
            maybe_shiny = False
            print(f'probably not shiny {eye_count=}')

    states: States = {
        **bootup('INITIAL', success='STARTED', fail='INITIAL'),
        'STARTED': (
            (always_matches, counter_reset, 'SKIP'),
        ),
        'SKIP': (
            (
                counter_expired,
                do(
                    Press('X'), Wait(.5),
                    Press('R'), Wait(1),
                    Press('A'), Wait(2.5),
                    reset,
                ),
                'INITIAL',
            ),
            (
                always_matches,
                do(skip_day, Press('A'), Wait(1), counter_decrement),
                'CHECK_RAID',
            ),
        ),
        'CHECK_RAID': (
            (
                match_text(
                    'Tera Raid Battle',
                    Point(y=116, x=183),
                    Point(y=172, x=470),
                    invert=False,
                ),
                do(),
                'CHECK_POKEMON',
            ),
            (always_matches, do(), 'SKIP'),
        ),
        'CHECK_POKEMON': (
            (is_desired_target, do(), 'SAVE_RAID'),
            (always_matches, do(Press('B'), Wait(1)), 'SKIP'),
        ),
        'SAVE_RAID': (
            (
                world,
                do(
                    Press('X'), Wait(.5),
                    Press('R'), Wait(1),
                    Press('A'), Wait(2.5),
                ),
                'TO_WORLD',
            ),
            (always_matches, do(Press('B'), Wait(.5)), 'SAVE_RAID'),
        ),
        'TO_WORLD': (
            (
                world,
                do(
                    Press('A'), Wait(1),
                    Press('s'), Wait(.25),
                    Press('A'), Wait(7),
                ),
                'WAIT_FOR_WHITE_1',
            ),
            (always_matches, do(Press('B'), Wait(.5)), 'TO_WORLD'),
        ),
        'WAIT_FOR_WHITE_1': (
            (
                match_px(Point(y=379, x=615), Color(b=253, g=255, r=253)),
                do(),
                'FOUND_WHITE_1',
            ),
        ),
        'FOUND_WHITE_1': (
            (
                match_px(Point(y=379, x=615), Color(b=253, g=255, r=253)),
                do(),
                'FOUND_WHITE_1',
            ),
            (always_matches, do(Wait(7.5), check), 'WAIT'),
        ),
        'WAIT': (
            (lambda _: maybe_shiny, do(), 'ALARM'),
            (always_matches, reset, 'INITIAL'),
        ),
        **alarm('ALARM', quiet=False),
    }

    with serial.Serial(args.serial, 9600) as ser:
        run(vid=make_vid(), ser=ser, initial='INITIAL', states=states)


if __name__ == '__main__':
    raise SystemExit(main())
