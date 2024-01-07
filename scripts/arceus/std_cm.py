from __future__ import annotations

import argparse
import functools
import math
import os.path
import sys
import time
from typing import NamedTuple
from typing import TypedDict

import cv2
import numpy
import serial

from scripts.engine import Action
from scripts.engine import all_match
from scripts.engine import always_matches
from scripts.engine import bye
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
from scripts.engine import Timeout
from scripts.engine import Wait
from scripts.engine import Write
from scripts.switch import SERIAL_DEFAULT
from scripts.switch import stick
from scripts.switch import STICK_0
from scripts.switch import STICK_MAX
from scripts.thrids import region_colorish

HERE = os.path.abspath(os.path.dirname(__file__))

_green_bar = region_colorish(
    Point(y=692, x=1087),
    Point(y=695, x=1133),
    (70, 190, 220),
    (74, 200, 255),
    .9,
)


@functools.lru_cache(maxsize=1)
def _std_mask() -> tuple[numpy.ndarray, numpy.ndarray]:
    tmpl = cv2.imread(os.path.join(HERE, 'templates', 'std-icon.png'))
    mask = 255 - cv2.inRange(tmpl, tmpl[0][0], tmpl[0][0])
    return tmpl, mask


@functools.lru_cache
def _bird() -> tuple[numpy.ndarray, numpy.ndarray]:
    tmpl = cv2.imread(os.path.join(HERE, 'templates', 'bird-icon.png'))
    mask = numpy.any(tmpl == tmpl[0][0], axis=2)
    return tmpl, mask


def is_bird(frame: numpy.ndarray) -> bool:
    tl = Point(y=487, x=1177)
    br = Point(y=547, x=1237)
    crop = frame[tl.y:br.y, tl.x:br.x]

    bird, mask = _bird()
    crop[numpy.nonzero(mask)] = bird[0][0]
    avg = float(numpy.average(cv2.absdiff(crop, bird)))
    return avg < 8


def _save(name: str, frame: numpy.ndarray, *, success: bool) -> None:
    target = os.path.join('..', 'nintendo-microcontrollers', 'i', name)
    os.makedirs(target, exist_ok=True)
    n = len(os.listdir(target))
    filename = f'{target}/{n:03}{"" if success else "_fail"}.png'
    print(f'+ {filename}')
    cv2.imwrite(filename, frame)


def capture(name: str) -> Action:
    def capture_impl(vid: cv2.VideoCapture, ser: object) -> None:
        _save(name, getframe(vid), success=True)
    return capture_impl


class Rect(NamedTuple):
    x1: int
    y1: int
    x2: int
    y2: int

    @classmethod
    def from_cv2(cls, rect: tuple[int, int, int, int]) -> Rect:
        x, y, w, h = rect
        return cls(x, y, x + w, y + h)

    def expand(self, n: int = 5) -> Rect:
        return type(self)(self.x1 - n, self.y1 - n, self.x2 + n, self.y2 + n)

    def intersects(self, other: Rect) -> bool:
        return (
            self.x1 < other.x2 and
            self.x2 > other.x1 and
            self.y1 < other.y2 and
            self.y2 > other.y1
        )


def _rects(
        hsv: numpy.ndarray,
        low: tuple[int, int, int],
        high: tuple[int, int, int],
) -> list[Rect]:
    m = cv2.inRange(hsv, low, high)

    kernel = numpy.ones((3, 3), numpy.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(
        m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE,
    )
    return [
        Rect.from_cv2(cv2.boundingRect(contour)).expand(5)
        for contour in contours
        if cv2.contourArea(contour) > 50
    ]


def _poke_like(tops: list[Rect], bottoms: list[Rect]) -> bool:
    for top in tops:
        for bottom in bottoms:
            if top.intersects(bottom) and top.y2 < bottom.y2:
                return True
    else:
        return False


class Checker:
    def __init__(self) -> None:
        self.known_pokemon = False

    def determine(self, name: str) -> Action:
        def determine_impl(vid: cv2.VideoCapture, ser: serial.Serial) -> None:
            self.known_pokemon = False

            getframe(vid)  # clear buffer frame

            for _ in range(5):
                frame = getframe(vid)
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

                # first make sure we are on horse
                if _green_bar(frame):
                    print('NOT ON HORSE!')
                    _save(name, frame, success=False)
                    return

                # blank out pokemon
                cv2.circle(hsv, (1050, 596), 22, (0, 0, 0), -1)
                cv2.circle(hsv, (1128, 596), 36, (0, 0, 0), -1)
                cv2.circle(hsv, (1207, 596), 22, (0, 0, 0), -1)

                p_pink_rects = _rects(hsv, (164, 145, 80), (175, 210, 255))
                p_blue_rects = _rects(hsv, (90, 70, 95), (100, 150, 255))

                p2_pink_rects = _rects(hsv, (159, 170, 75), (162, 230, 135))
                p2_blue_rects = _rects(hsv, (102, 115, 80), (108, 165, 170))

                pz_pink_rects = _rects(hsv, (162, 200, 75), (164, 255, 130))
                pz_blue_rects = _rects(hsv, (105, 140, 80), (112, 200, 155))

                if _poke_like(p_pink_rects, p_blue_rects):
                    print('found porygon!')
                    self.known_pokemon = True
                    _save(name, frame, success=True)
                    return
                elif _poke_like(p2_pink_rects, p2_blue_rects):
                    print('found porygon 2!')
                    self.known_pokemon = True
                    _save(name, frame, success=True)
                    return
                elif _poke_like(pz_pink_rects, pz_blue_rects):
                    print('found porygon z!')
                    self.known_pokemon = True
                    _save(name, frame, success=True)
                    return

                Wait(.1)(vid, ser)

            print('no porygons...')
            _save(name, frame, success=False)

        return determine_impl

    def known(self, frame: object) -> bool:
        return self.known_pokemon


class XY(TypedDict):
    x: int
    y: int


def rot(deg: float) -> XY:
    r = 127
    rad = 2 * math.pi * deg / 360
    x = 128 + r * math.sin(rad)
    y = 256 - (128 + r * math.cos(rad))
    return {'x': round(x), 'y': round(y)}


def look(*, x: int, y: int) -> Action:
    return do(
        stick('<', x=x, y=y, duration=.25), Wait(.1),
        Press('l'), Wait(.5),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--serial', default=SERIAL_DEFAULT)
    parser.add_argument('--sleep-after', action='store_true')
    args = parser.parse_args()

    if args.sleep_after:
        maybe_sleep = do(Press('H', duration=1), Press('A'))
    else:
        maybe_sleep = Press('!')

    nudge = Timeout()
    step_timeout = Timeout()

    checker = Checker()

    t0 = time.monotonic()

    def display_time(vid: object, ser: object) -> None:
        taken = (time.monotonic() - t0) / 60
        print(f'found after {taken:.1f} minutes')

    sessions = 0

    def increment_sessions(vid: object, ser: object) -> None:
        nonlocal sessions, t0
        sessions += 1
        t0 = time.monotonic()

    def print_sessions(vid: object, ser: object) -> None:
        print(f'total sessions: {sessions}')

    std = 'unknown'

    def determine_std(vid: cv2.VideCapture, ser: serial.Serial) -> None:
        nonlocal std

        do(Press('-'), Wait(1),  Press('w', duration=1), Wait(.5))(vid, ser)

        frame = getframe(vid)

        do(Press('B'), Wait(1))(vid, ser)

        tmpl, mask = _std_mask()
        match = cv2.matchTemplate(frame, tmpl, cv2.TM_CCOEFF_NORMED, mask=mask)
        _, _, _, (std_x, std_y) = cv2.minMaxLoc(match)

        if 760 <= std_x <= 762 and 508 <= std_y <= 510:
            std = 'close'
        elif 579 <= std_x <= 581 and 556 <= std_y <= 558:
            std = 'hay'
        elif 833 <= std_x <= 835 and 454 <= std_y <= 456:
            std = 'maze'
        elif 483 <= std_x <= 485 and 406 <= std_y <= 408:
            std = 'monuments'
        elif 809 <= std_x <= 811 and 297 <= std_y <= 299:
            std = 'terrace'
        else:
            raise AssertionError(f'unexpected std position {std_x}, {std_y}')

        print(f'std location: {std}')

    bootup_timeout = time.monotonic() + 20

    fly_timeout = Timeout()
    fly_debounce = Timeout()

    states: States = {
        'INITIAL': (
            (
                all_match(
                    match_px(Point(y=532, x=46), Color(b=202, g=227, r=231)),
                    match_px(Point(y=621, x=78), Color(b=204, g=227, r=229)),
                    match_px(Point(y=677, x=80), Color(b=198, g=228, r=229)),
                    match_text(
                        'L',
                        Point(y=667, x=1013),
                        Point(y=683, x=1030),
                        invert=False,
                    ),
                    match_text(
                        'R',
                        Point(y=667, x=1229),
                        Point(y=685, x=1244),
                        invert=False,
                    ),
                ),
                do(),
                'BOOTED',
            ),
            (
                lambda _: time.monotonic() > bootup_timeout,
                do(Press('!', duration=1), bye),
                'UNREACHABLE',
            ),
            (always_matches, do(Press('H'), Wait(1)), 'INITIAL'),
        ),
        'BOOTED': (
            (
                match_text(
                    'A space-time distortion seems to be forming!',
                    Point(y=100, x=465),
                    Point(y=126, x=816),
                    invert=True,
                ),
                do(
                    display_time,
                    Press('l'), Wait(1),
                    Press('w', duration=1.5), Wait(.5),
                ),
                'POKE',
            ),
            (nudge.expired, do(Press('X'), nudge.after(180)), 'BOOTED'),
            (always_matches, Wait(1), 'BOOTED'),
        ),
        'POKE': (
            (_green_bar, step_timeout.after(10), 'BIRD'),
            (always_matches, do(Press('X'), Wait(.5)), 'POKE'),
        ),
        'BIRD': (
            (step_timeout.expired, do(), 'DONE'),
            (is_bird, determine_std, 'DISPATCH'),
            (always_matches, do(Press('1'), Wait(.5)), 'BIRD'),
        ),
        'DISPATCH': (
            (lambda _: std == 'close', do(), 'CLOSE'),
            (lambda _: std == 'hay', do(), 'HAY'),
            (lambda _: std == 'maze', do(), 'MAZE'),
            (lambda _: std == 'monuments', do(), 'MONUMENTS'),
            (lambda _: std == 'terrace', do(), 'TERRACE'),
        ),
        'CLOSE': (
            (
                always_matches,
                do(
                    Press('-'), Wait(1),
                    Press('X'), Wait(.5),
                    Press('s'), Press('A'), Wait(5),
                    look(**rot(-12)),
                    Wait(109),
                    Press('+'), Wait(.25),
                    Press('B', duration=4.9),
                    Press('Y', duration=4.25),
                    look(**rot(-80)),
                    Press('3'), Press('+'),
                    Press('j', duration=.3), Wait(.2),
                    checker.determine('close-1-v19-12'),
                ),
                'CLOSE_1',
            ),
        ),
        'CLOSE_1': (
            (
                checker.known,
                do(
                    look(**rot(144)),
                    Press('B', duration=1.6),
                    Press('j', duration=.3), Wait(.5),
                    checker.determine('close-2-v11-144'),
                ),
                'CLOSE_2',
            ),
            (always_matches, do(), 'DONE'),
        ),
        'CLOSE_2': (
            (
                checker.known,
                do(
                    look(**rot(-95)),
                    Press('B', duration=2.2), Wait(.3),
                    Press('q', duration=.2),
                    Press('n', duration=.6), Wait(.2),
                    checker.determine('close-3-v37-95'),
                ),
                'CHECK_3',
            ),
            (always_matches, do(), 'DONE'),
        ),
        'HAY': (
            (
                always_matches,
                do(
                    look(**rot(-71)),
                    Wait(172),
                    Press('+'), Wait(.25),
                    Press('B', duration=15.2),
                    Press('Y', duration=2.55),
                    Press('3'), Press('+'),
                    Press('j', duration=.4), Wait(.1),
                    checker.determine('hay-1-v25'),
                ),
                'HAY_1',
            ),
        ),
        'HAY_1': (
            (
                checker.known,
                do(
                    look(**rot(-71)),
                    Press('B', duration=2),
                    Press('j', duration=.3), Wait(.4),
                    checker.determine('hay-2-v9-71'),
                ),
                'HAY_2',
            ),
            (always_matches, do(), 'DONE'),
        ),
        'HAY_2': (
            (
                checker.known,
                do(
                    look(**rot(-56)),
                    capture('hay-DEBUG-v0'),
                    Press('B', duration=1.9),
                    Press('j', duration=.3), Wait(.4),
                    checker.determine('hay-3-v18-56'),
                ),
                'CHECK_3',
            ),
            (always_matches, do(), 'DONE'),
        ),
        'MAZE': (
            (
                always_matches,
                do(
                    look(**rot(134)),
                    Wait(150),
                    Press('+'), Wait(.25),
                    Press('B', duration=11.5),
                    Press('Y', duration=2.75),
                    Press('3'), Press('+'),
                    Press('j', duration=.2), Wait(.3),
                    checker.determine('maze-1-v7'),
                ),
                'MAZE_1',
            ),
        ),
        'MAZE_1': (
            (
                checker.known,
                do(
                    Press('B', duration=2.1), Wait(.75),
                    look(**rot(37)),
                    Press('B', duration=2.1),
                    Press('j', duration=.2), Wait(.5),
                    checker.determine('maze-2-v22-37'),
                ),
                'MAZE_2',
            ),
            (always_matches, do(), 'DONE'),
        ),
        'MAZE_2': (
            (
                checker.known,
                do(
                    look(**rot(90)),
                    Press('B', duration=1.4), Wait(.6),
                    stick('<', **rot(65), duration=1.5),
                    look(**rot(-13)),
                    Press('B', duration=1),
                    Press('j', duration=.2), Wait(.3),
                    checker.determine('maze-3-v30-90-65-13'),
                ),
                'CHECK_3',
            ),
            (always_matches, do(), 'DONE'),
        ),
        'MONUMENTS': (
            (
                always_matches,
                do(
                    Press('-'), Wait(1),
                    Press('X'), Wait(.5),
                    Press('A'), Wait(5),
                    look(x=STICK_0 + 85, y=STICK_MAX),
                    Wait(228),
                    Press('+'), Wait(.25),
                    Press('B', duration=9.9),
                    Press('Y', duration=3.55),
                    Press('3'), Press('+'),
                    Press('j', duration=.2), Wait(.3),
                    checker.determine('monuments-1-v8'),
                ),
                'MONUMENTS_1',
            ),
        ),
        'MONUMENTS_1': (
            (
                checker.known,
                do(
                    look(**rot(62)),
                    Press('B', duration=3.15),
                    Press('j', duration=.2), Wait(.5),
                    checker.determine('monuments-2-v24-62'),
                ),
                'MONUMENTS_2',
            ),
            (always_matches, do(), 'DONE'),
        ),
        'MONUMENTS_2': (
            (
                checker.known,
                do(
                    look(**rot(-115)),
                    capture('monuments-DEBUG-v3'),
                    Press('B', duration=3.4),
                    Press('j', duration=.3), Wait(.4),
                    checker.determine('monuments-3-v30-115'),
                ),
                'CHECK_3',
            ),
            (always_matches, do(), 'DONE'),
        ),
        'TERRACE': (
            (
                always_matches,
                do(
                    Press('-'), Wait(1),
                    Press('X'), Wait(.5),
                    Press('w'), Press('w'), Press('w'), Press('A'),
                    Wait(5),
                    look(x=STICK_MAX, y=STICK_0 + 60),
                    Wait(200),
                    Press('+'), Wait(.25),
                    Press('B', duration=13),
                    Press('Y', duration=3), Wait(4.5),
                    look(**rot(-61)),
                    Press('3'), Press('+'),
                    Press('B', duration=2.3), Wait(.75),
                    look(**rot(142)),
                    Press('j', duration=.4), Wait(.1),
                    checker.determine('terrace-1-61-142-v18'),
                ),
                'TERRACE_1',
            ),
        ),
        'TERRACE_1': (
            (
                checker.known,
                do(
                    Press('B', duration=2.25),
                    Press('j', duration=.2), Wait(.5),
                    checker.determine('terrace-2-v12'),
                ),
                'TERRACE_2',
            ),
            (always_matches, do(), 'DONE'),
        ),
        'TERRACE_2': (
            (
                checker.known,
                do(
                    look(**rot(43)),
                    Press('B', duration=1.9),
                    Press('m', duration=.5), Wait(.2),
                    checker.determine('terrace-3-43-v14'),
                ),
                'CHECK_3',
            ),
            (always_matches, do(), 'DONE'),
        ),
        'CHECK_3': (
            (
                checker.known,
                do(
                    Press('1'), Wait(1), Write('B'), Wait(2),
                    fly_debounce.after(3),
                    fly_timeout.after(12),
                ),
                'CHECK_ON_BIRD',
            ),
            (always_matches, do(), 'DONE'),
        ),
        'CHECK_ON_BIRD': (
            (
                region_colorish(
                    Point(y=493, x=1201),
                    Point(y=501, x=1212),
                    (29, 240, 250),
                    (31, 255, 255),
                    .9,
                ),
                do(),
                'FLYING',
            ),
            (always_matches, Write('.'), 'DONE'),
        ),
        'FLYING': (
            (fly_timeout.expired, Write('.'), 'DONE'),
            (
                region_colorish(
                    Point(y=48, x=620),
                    Point(y=69, x=658),
                    (4, 140, 225),
                    (8, 230, 255),
                    .3,
                ),
                fly_debounce.after(1),
                'FLYING',
            ),
            (
                fly_debounce.expired,
                do(
                    Press('-'), Wait(1),
                    Press('X'), Wait(.5),
                    Press('s'), Press('A'), Wait(5),
                    stick('<', **rot(-20), duration=1.75),
                    Press('A'), Wait(1),
                ),
                'REST',
            ),
        ),
        'REST': (
            (
                match_text(
                    'How long would you like to rest?',
                    Point(y=563, x=352),
                    Point(y=600, x=735),
                    invert=True,
                ),
                do(Press('A'), Wait(1), Press('s'), Press('A'), Wait(3)),
                'RESTED',
            ),
            (always_matches, do(), 'DONE'),
        ),
        'RESTED': (
            (
                match_text(
                    'healthy again!',
                    Point(y=604, x=356),
                    Point(y=644, x=527),
                    invert=True,
                ),
                do(Press('A'), Wait(1), increment_sessions),
                'BOOTED',
            ),
        ),
        'DONE': (
            (
                always_matches,
                do(
                    Press('C', duration=1),
                    Press('H'), Wait(1),
                    maybe_sleep, print_sessions, bye,
                ),
                'UNREACHABLE',
            ),
        ),
    }

    with serial.Serial(args.serial, 9600) as ser:
        run(
            vid=make_vid(),
            ser=ser,
            initial='INITIAL',
            states=states,
            transition_timeout=sys.maxsize,
        )


if __name__ == '__main__':
    raise SystemExit(main())
