from __future__ import annotations

import argparse
import time

import cv2
import numpy
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
from scripts.engine import Timeout
from scripts.engine import Wait
from scripts.thrids import alarm
from scripts.thrids import SERIAL_DEFAULT


def _bootup(start: str, end: str) -> States:
    def _a(vid: object, ser: serial.Serial) -> None:
        ser.write(b'A')
        time.sleep(.05)
        ser.write(b'.')
        print('A', end='', flush=True)

    def nl(vid: object, ser: object) -> None:
        print()

    return {
        start: (
            (
                all_match(
                    match_px(Point(y=421, x=997), Color(b=40, g=68, r=255)),
                    match_px(Point(y=88, x=876), Color(b=245, g=96, r=93)),
                    match_px(Point(y=114, x=1130), Color(b=245, g=96, r=93)),
                ),
                nl,
                end,
            ),
            (always_matches, do(_a, Wait(.1)), start),
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--serial', default=SERIAL_DEFAULT)
    args = parser.parse_args()

    crash = Timeout()

    def is_shiny(frame: numpy.ndarray) -> bool:
        tl = Point(y=140, x=154)
        br = Point(y=149, x=157)
        crop = frame[tl.y:br.y, tl.x:br.x]
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        thres = cv2.inRange(hsv, (105, 110, 200), (113, 200, 255))

        count = int(numpy.count_nonzero(thres))
        total = int(crop.shape[0] * crop.shape[1])
        print(f'blues: {count}')
        return count != total

    def _confirm(vid: object, ser: serial.Serial) -> None:
        ser.write(b'A')
        time.sleep(.05)
        ser.write(b'*')
        time.sleep(.25)
        ser.write(b'.')

    states: States = {
        'INITIAL': (
            (
                always_matches,
                do(Press('@'), crash.after(15)),
                'WAIT_FOR_JIRACHI_DONE',
            ),
        ),
        'WAIT_FOR_JIRACHI_DONE': (
            (
                match_text(
                    'You',
                    Point(y=607, x=218),
                    Point(y=678, x=382),
                    invert=True,
                ),
                Press('*'),
                'BOOTUP',
            ),
            (crash.expired, Press('*'), 'CRASHED'),
        ),
        'CRASHED': (
            (always_matches, Wait(45), 'INITIAL'),
        ),
        **_bootup('BOOTUP', 'TO_JIRACHI'),
        'TO_JIRACHI': (
            (
                always_matches,
                do(
                    Press('['), Wait(.25),
                    Press('s'), Press('A'), Wait(1),
                    Press('A'), Press('A'), Wait(1),
                    Press('s'), Wait(.5),
                ),
                'CHECK',
            ),
        ),
        'CHECK': (
            (is_shiny, do(), 'ALARM'),
            (always_matches, Press('@'), 'CORRUPT'),
        ),
        **alarm('ALARM'),
        'CORRUPT': (
            (
                match_px(Point(y=43, x=138), Color(b=0, g=128, r=23)),
                do(Wait(.5), Press('A'), Wait(1), Press('~')),
                'CORRUPT_CONFIRM',
            ),
        ),
        'CORRUPT_CONFIRM': (
            (
                all_match(
                    match_px(Point(y=64, x=586), Color(b=125, g=79, r=11)),
                    match_px(Point(y=109, x=332), Color(b=255, g=255, r=255)),
                    match_text(
                        'all save',
                        Point(y=526, x=295),
                        Point(y=594, x=504),
                        invert=False,
                    ),
                ),
                do(Press('w'), _confirm, crash.after(7)),
                'WAIT_FOR_BOOTUP2',
            ),
        ),
        'WAIT_FOR_BOOTUP2': (
            (
                match_px(Point(y=50, x=50), Color(b=0, g=0, r=0)),
                do(),
                'BOOTUP2',
            ),
            (crash.expired, do(), 'CRASH2'),
        ),
        'CRASH2': (
            (
                always_matches,
                do(Press('*'), crash.after(7)),
                'WAIT_FOR_BOOTUP2',
            ),
        ),
        **_bootup('BOOTUP2', 'SAVE_1'),
        'SAVE_1': (
            (
                always_matches,
                do(
                    Press('['), Wait(.25),
                    Press('s'), Press('s'), Press('s'), Press('s'),
                    Press('A'), Wait(1),
                    Press('A'), Wait(1.5),
                    Press('A'), Wait(1),
                ),
                'SAVE_1_WAIT',
            ),
        ),
        'SAVE_1_WAIT': (
            (
                match_text(
                    'saved the game.',
                    Point(y=520, x=218),
                    Point(y=595, x=640),
                    invert=False,
                ),
                do(
                    Press('B'), Wait(2),
                    Press('['), Wait(.25),
                    Press('A'), Wait(1),
                    Press('A'), Wait(1.5),
                    Press('A'), Wait(1),
                ),
                'SAVE_2_WAIT',
            ),
        ),
        'SAVE_2_WAIT': (
            (
                match_text(
                    'saved the game.',
                    Point(y=520, x=218),
                    Point(y=595, x=640),
                    invert=False,
                ),
                do(),
                'INITIAL',
            ),
        ),
    }

    with serial.Serial(args.serial, 9600) as ser:
        run(vid=make_vid(), ser=ser, initial='INITIAL', states=states)


if __name__ == '__main__':
    raise SystemExit(main())
