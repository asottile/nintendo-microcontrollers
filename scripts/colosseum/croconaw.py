from __future__ import annotations

import argparse
import os.path
import time

import cv2
import numpy
import serial

from scripts.colosseum._bootup import bootup
from scripts.engine import Action
from scripts.engine import always_matches
from scripts.engine import do
from scripts.engine import make_vid
from scripts.engine import match_text
from scripts.engine import Point
from scripts.engine import Press
from scripts.engine import run
from scripts.engine import States
from scripts.engine import Timeout
from scripts.engine import Wait
from scripts.thrids import alarm
from scripts.thrids import region_colorish
from scripts.thrids import SERIAL_DEFAULT


def press(s: str) -> Action:
    def press_impl(vid: object, ser: serial.Serial) -> None:
        ser.write(s.encode())
        time.sleep(.05)
        ser.write(b'.')
    return press_impl


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--serial', default=SERIAL_DEFAULT)
    args = parser.parse_args()

    timeout = Timeout()

    def is_shiny(frame: numpy.ndarray) -> bool:
        tl = Point(y=448, x=613).norm(frame.shape)
        br = Point(y=499, x=675).norm(frame.shape)

        crop = frame[tl.y:br.y, tl.x:br.x]

        here = os.path.dirname(__file__)
        base = cv2.imread(os.path.join(here, 'img', 'croconaw.png'))

        diff = cv2.absdiff(base, crop)

        avg = float(numpy.average(diff))
        print(f'diff: {avg:.2f}')
        return avg >= 3

    states: States = {
        **bootup('INITIAL', 'OUTSIDE'),
        'OUTSIDE': (
            (
                region_colorish(
                    Point(y=218, x=583),
                    Point(y=243, x=688),
                    (62, 130, 150),
                    (70, 170, 180),
                    .1,
                ),
                do(
                    Press('c', duration=1.8), Wait(.1),
                    Wait(.75),
                ),
                'OTHER_BUILDING',
            ),
        ),
        'OTHER_BUILDING': (
            (
                region_colorish(
                    Point(y=192, x=312),
                    Point(y=229, x=359),
                    (30, 0, 110),
                    (110, 20, 140),
                    .9,
                ),
                do(
                    Press('s', duration=.3), Wait(.1),
                    Press('d', duration=1.7), Wait(.1),
                    Press('w', duration=.5), Wait(.1),
                    Wait(.75),
                ),
                'ELEVATOR1',
            ),
        ),
        'ELEVATOR1': (
            (
                region_colorish(
                    Point(y=388, x=622),
                    Point(y=399, x=638),
                    (98, 230, 75),
                    (102, 255, 120),
                    .9,
                ),
                do(
                    Press('w', duration=3), Wait(.1),
                    Wait(5),
                ),
                'ELEVATOR2',
            ),
        ),
        'ELEVATOR2': (
            (
                region_colorish(
                    Point(y=213, x=638),
                    Point(y=225, x=652),
                    (94, 120, 150),
                    (98, 140, 170),
                    .9,
                ),
                do(
                    Press('a', duration=.4), Wait(.1),
                    Press('s', duration=8.5), Wait(.1),
                    Press('z', duration=.75), Wait(.1),
                    Press('s', duration=1.4), Wait(.1),
                    Press('a', duration=1.6), Wait(.1),
                    Press('w', duration=2), Wait(.1),
                    Wait(5),
                ),
                'ELEVATOR3',
            ),
        ),
        'ELEVATOR3': (
            (
                region_colorish(
                    Point(y=201, x=663),
                    Point(y=208, x=688),
                    (94, 130, 120),
                    (97, 150, 140),
                    .9,
                ),
                do(
                    Press('d', duration=1.75), Wait(.1),
                    Press('w', duration=2), Wait(.1),
                    Press('e', duration=.5), Wait(.1),
                    Press('d', duration=1.1), Wait(.1),
                    Press('w', duration=1), Wait(.1),
                    Wait(5),
                ),
                'ELEVATOR4',
            ),
        ),
        'ELEVATOR4': (
            (
                region_colorish(
                    Point(y=198, x=622),
                    Point(y=205, x=643),
                    (95, 155, 95),
                    (98, 175, 115),
                    .9,
                ),
                do(
                    Press('a', duration=2.3), Wait(.1),
                    Press('w', duration=5.5), Wait(.1),
                    Press('d', duration=.75), Wait(.1),
                    Wait(.75),
                ),
                'FIND_THEM',
            ),
        ),
        'FIND_THEM': (
            (
                region_colorish(
                    Point(y=424, x=609),
                    Point(y=435, x=627),
                    (99, 230, 100),
                    (102, 255, 120),
                    .9,
                ),
                do(
                    Press('d', duration=.3), Wait(.1),
                    Press('s', duration=1.75), Wait(.1),
                    Press('d', duration=.5), Wait(.1),
                ),
                'TEXT_BOX',
            ),
        ),
        'TEXT_BOX': (
            (
                region_colorish(
                    Point(y=457, x=156),
                    Point(y=471, x=170),
                    (0, 0, 200),
                    (255, 20, 255),
                    .9,
                ),
                timeout.after(7),
                'FOUND',
            ),
        ),
        'FOUND': (
            (timeout.expired, do(), 'BATTLE'),
            (always_matches, do(press('A'), Wait(.1)), 'FOUND'),
        ),
        'BATTLE': (
            (
                match_text(
                    'FIGHT',
                    Point(y=559, x=200),
                    Point(y=589, x=321),
                    invert=True,
                ),
                do(
                    Press('d'), Wait(.25), Press('A'), Wait(1.25),
                    Press('d'), Wait(.5), Press('A'), Wait(.5),
                    Press('A'), Wait(2), Press('A'), Wait(.25),

                    Press('d'), Wait(.25), Press('A'), Wait(1.25),
                    Press('Y'), Wait(.25), Press('s'), Wait(.25),
                    Press('Y'), Wait(.25),
                    Press('B'), Wait(2),
                    Press('s'), Wait(.25), Press('A'), Wait(.5),
                ),
                'CAUGHT',
            ),
        ),
        'CAUGHT': (
            (
                match_text(
                    'FIGHT',
                    Point(y=559, x=200),
                    Point(y=589, x=321),
                    invert=True,
                ),
                do(Press('s'), Wait(.25), Press('A'), Wait(1.5)),
                'CHECK',
            ),
        ),
        'CHECK': (
            (is_shiny, do(), 'ALARM'),
            (always_matches, Press('*'), 'INITIAL'),
        ),
        **alarm('ALARM'),
    }

    with serial.Serial(args.serial, 9600) as ser:
        run(vid=make_vid(), ser=ser, initial='INITIAL', states=states)


if __name__ == '__main__':
    raise SystemExit(main())
