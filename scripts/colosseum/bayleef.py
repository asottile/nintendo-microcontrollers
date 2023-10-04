from __future__ import annotations

import argparse
import os.path
import sys
import time

import cv2
import numpy
import serial

from scripts.colosseum._bootup import bootup
from scripts.engine import Action
from scripts.engine import always_matches
from scripts.engine import do
from scripts.engine import getframe
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

    back = region_colorish(
        Point(y=409, x=624),
        Point(y=420, x=638),
        (99, 210, 95),
        (102, 255, 115),
        .9,
    )

    timeout = Timeout()

    def room_match(frame: numpy.ndarray) -> bool:
        hsv = cv2.cvtColor(frame[130:480, 0:480], cv2.COLOR_BGR2HSV)
        thres = cv2.inRange(hsv, (17, 110, 110), (24, 145, 145))

        kernel = numpy.ones((3, 3), numpy.uint8)
        m = cv2.erode(thres, kernel)
        count = int(numpy.count_nonzero(m))
        print(f'{count=}')
        return count >= 4000

    def find_them(vid: cv2.VideoCapture, ser: serial.Serial) -> None:
        frame = getframe(vid)

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        thres = cv2.inRange(hsv, (40, 240, 90), (45, 255, 140))

        kernel = numpy.ones((30, 30), numpy.uint8)
        m = cv2.morphologyEx(thres, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(
            m, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE,
        )
        if not contours:
            return
        min_x, min_y = sys.maxsize, sys.maxsize
        for contour in contours:
            x, y, _, _ = cv2.boundingRect(contour)
            min_x, min_y = min(min_x, x), min(min_y, y)

        p_y = frame.shape[0] // 2
        p_x = frame.shape[1] // 2
        dy, dx = min_y - p_y, min_x - p_x

        if abs(dy) > abs(dx):
            if dy > 0:
                direction = 's'
            else:
                direction = 'w'
        else:
            if dx > 0:
                direction = 'd'
            else:
                direction = 'a'

        do(Press(direction), Press('A'), Wait(.25))(vid, ser)

    def is_shiny(frame: numpy.ndarray) -> bool:
        tl = Point(y=448, x=613).norm(frame.shape)
        br = Point(y=499, x=675).norm(frame.shape)

        crop = frame[tl.y:br.y, tl.x:br.x]

        here = os.path.dirname(__file__)
        base = cv2.imread(os.path.join(here, 'img', 'bayleef.png'))

        diff = cv2.absdiff(base, crop)

        avg = float(numpy.average(diff))
        print(f'diff: {avg:.2f}')
        return avg >= 3

    states: States = {
        **bootup('INITIAL', 'STAIR1'),
        'STAIR1': (
            (
                region_colorish(
                    Point(y=138, x=515),
                    Point(y=201, x=693),
                    (55, 110, 150),
                    (75, 230, 230),
                    .1,
                ),
                do(
                    Press('q', duration=.75), Wait(.1),
                    Press('w', duration=1.5), Wait(.1),
                    Press('a', duration=1.3), Wait(.1),
                    Press('w', duration=.75), Wait(.1),
                    Wait(.75),
                ),
                'STAIR2',
            ),
        ),
        'STAIR2': (
            (
                back,
                do(
                    Press('d', duration=.7), Wait(.1),
                    Press('s', duration=3.6), Wait(.1),
                    Press('d', duration=.5), Wait(.1),
                    Press('w', duration=.75), Wait(.1),
                    Wait(.75),
                ),
                'STAIR3',
            ),
        ),
        'STAIR3': (
            (
                back,
                do(
                    Press('q', duration=.7), Wait(.1),
                    Press('w', duration=1.6), Wait(.1),
                    Press('a', duration=1.3), Wait(.1),
                ),
                'DOWN_UNTIL_ROOM',
            ),
        ),
        'DOWN_UNTIL_ROOM': (
            (
                room_match,
                do(
                    Press('s', duration=.2), Wait(.1),
                    Press('a', duration=.75), Wait(.1),
                    Press('s', duration=1), Wait(.1),
                    Press('d', duration=.3), Wait(.1),
                    Press('s', duration=.2), Wait(.1),
                    Press('d', duration=.4), Wait(.1),
                    Press('s', duration=.75), Wait(.1),
                    Wait(.75),
                ),
                'STAIR4',
            ),
            (
                always_matches,
                do(Press('s', duration=.1), Wait(.1)),
                'DOWN_UNTIL_ROOM',
            ),
        ),
        'STAIR4': (
            (
                region_colorish(
                    Point(y=225, x=625),
                    Point(y=235, x=643),
                    (10, 200, 130),
                    (12, 255, 170),
                    .9,
                ),
                do(
                    Press('a', duration=.5), Wait(.1),
                    Press('w', duration=2.9), Wait(.1),
                    Press('q', duration=.5), Wait(.1),
                    Press('w', duration=.4), Wait(.1),
                    Press('d', duration=.75), Wait(.1),
                    Wait(.75),
                ),
                'TO_ROOM',
            ),
        ),
        'TO_ROOM': (
            (
                region_colorish(
                    Point(y=474, x=602),
                    Point(y=489, x=622),
                    (98, 200, 100),
                    (102, 255, 130),
                    .9,
                ),
                do(
                    Press('s', duration=.4), Wait(.1),
                    Press('z', duration=1), Wait(.1),
                    Press('s', duration=1), Wait(.1),
                    Press('d', duration=.1), Wait(.1),
                    Press('s', duration=2), Wait(.1),
                    Press('z', duration=1), Wait(.1),
                    Wait(.75),
                ),
                'FIND_THEM',
            ),
        ),
        'FIND_THEM': (
            (
                region_colorish(
                    Point(y=457, x=156),
                    Point(y=471, x=170),
                    (0, 0, 200),
                    (255, 20, 255),
                    .9,
                ),
                timeout.after(5),
                'FOUND',
            ),
            (always_matches, find_them, 'FIND_THEM'),
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
