from __future__ import annotations

import argparse
import functools
import os.path

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
from scripts.sv._raid import raid_type
from scripts.sv._skip_day import skip_day
from scripts.switch import reset
from scripts.switch import SERIAL_DEFAULT


@functools.lru_cache
def _sprites() -> list[tuple[str, numpy.ndarray]]:
    return [
        (
            os.path.splitext(fname)[0],
            cv2.resize(
                cv2.imread(
                    os.path.join('sv-sprites', fname),
                    flags=cv2.IMREAD_UNCHANGED,
                )[:, :, 3],
                (235, 235),
            ),
        )
        for fname in os.listdir('sv-sprites')
    ]


def _pokemon(frame: numpy.ndarray) -> str:
    frame = cv2.resize(frame, (1280, 720))
    tl = Point(y=145, x=763)
    br = Point(y=380, x=998)
    crop = frame[tl.y:br.y, tl.x:br.x]
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, (100, 80, 55), (125, 160, 80))
    kernel = numpy.ones((2, 2), numpy.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    best_name = ''
    best_diff = 1e9
    for name, img in _sprites():
        diff = numpy.average(cv2.absdiff(mask, img))
        if diff < best_diff:
            best_name = name
            best_diff = diff

    return best_name


@functools.lru_cache
def _stars() -> list[tuple[int, numpy.ndarray]]:
    stars_dir = os.path.join(os.path.dirname(__file__), 'stars')
    return [
        (n, cv2.imread(os.path.join(stars_dir, f'{n}.png')))
        for n in (3, 4, 5, 6)
    ]


def _star_count(frame: numpy.ndarray) -> int:
    frame = cv2.resize(frame, (1280, 720))
    tl_stars = Point(y=399, x=706)
    br_stars = Point(y=453, x=1055)
    stars = frame[tl_stars.y:br_stars.y, tl_stars.x:br_stars.x]

    best_n = -1
    best_diff = 1e9
    for n, star_img in _stars():
        diff = numpy.average(cv2.absdiff(stars, star_img))
        if diff < best_diff:
            best_n = n
            best_diff = diff

    return best_n


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--serial', default=SERIAL_DEFAULT)
    parser.add_argument('--targets-file', default='sv-targets')
    args = parser.parse_args()

    with open(args.targets_file) as f:
        targets = frozenset(f.read().splitlines())

    if not _sprites():
        raise SystemExit('run python -m scripts.sv._download_sprites')

    counter = 30

    def counter_expired(frame: object) -> bool:
        return counter == 0

    def counter_decrement(vid: object, ser: object) -> None:
        nonlocal counter
        counter -= 1

    def counter_reset(vid: object, ser: object) -> None:
        nonlocal counter
        counter = 30

    key = ''

    def is_desired_target(frame: numpy.ndarray) -> bool:
        nonlocal key

        stars = _star_count(frame)
        pokemon = _pokemon(frame)
        tp = raid_type(frame)
        key = f'{stars}_{pokemon}'
        print(f'raid is: {key} ({tp})')
        return key in targets

    def screen(vid: cv2.VideoCapture, ser: serial.Serial) -> None:
        frame = getframe(vid)
        n = sum(1 for f in os.listdir('imgs') if f.startswith(f'{key}-'))
        cv2.imwrite(f'imgs/{key}-{n:02}.png', frame)
        cv2.imwrite('mon.png', frame)

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
            (is_desired_target, Press('!'), 'SAVE_RAID'),
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
                    Press('A'), Wait(6),
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
            (always_matches, do(), 'WAIT_FOR_WHITE_2'),
        ),
        'WAIT_FOR_WHITE_2': (
            (
                match_px(Point(y=379, x=615), Color(b=253, g=255, r=253)),
                do(),
                'FOUND_WHITE_2',
            ),
        ),
        'FOUND_WHITE_2': (
            (
                match_px(Point(y=379, x=615), Color(b=253, g=255, r=253)),
                do(),
                'FOUND_WHITE_2',
            ),
            (always_matches, do(Wait(.5), screen), 'WAIT'),
        ),
        'WAIT': (),
    }

    with serial.Serial(args.serial, 9600) as ser:
        run(vid=make_vid(), ser=ser, initial='INITIAL', states=states)


if __name__ == '__main__':
    raise SystemExit(main())
