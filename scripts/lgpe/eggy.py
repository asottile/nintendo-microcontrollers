from __future__ import annotations

import argparse
import time

import cv2
import numpy
import serial

from scripts.engine import Action
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
from scripts.switch import alarm
from scripts.switch import game_start
from scripts.switch import reset
from scripts.thrids import SERIAL_DEFAULT


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--serial', default=SERIAL_DEFAULT)
    parser.add_argument('--quiet', action='store_true')
    parser.add_argument('-n', type=int, required=True)
    args = parser.parse_args()

    debounce = Timeout()

    n = args.n

    def out(frame: object) -> bool:
        return n == 0

    def trade_one(vid: object, ser: object) -> None:
        nonlocal n
        n -= 1

    def reset_n(vid: object, ser: object) -> None:
        nonlocal n
        n = args.n

    def press(s: str) -> Action:
        def press_impl(vid: object, ser: serial.Serial) -> None:
            print(s, end='', flush=True)
            ser.write(s.encode())
            time.sleep(.1)
            ser.write(b'.')
        return press_impl

    def nl(vid: object, ser: object) -> None:
        print()

    def is_shiny(frame: numpy.ndarray) -> bool:
        tl = Point(y=340, x=629).norm(frame.shape)
        br = Point(y=364, x=653).norm(frame.shape)

        crop = frame[tl.y:br.y, tl.x:br.x]
        crop = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)

        thres = cv2.inRange(crop, (0, 0, 210), (40, 40, 235))
        n = int(numpy.count_nonzero(thres))
        print(f'count: {n}')
        if n < 1000:
            cv2.imwrite('shiny.png', frame)
        return n / thres.size < .75

    states: States = {
        'INITIAL': (
            (game_start, do(Press('A'), Wait(1), reset_n), 'TRADE'),
        ),
        'TRADE': (
            (out, reset, 'INITIAL'),
            (
                all_match(
                    debounce.expired,
                    match_px(Point(y=503, x=599), Color(b=250, g=255, r=23)),
                    match_text(
                        'Exemann sent over Exeggutor.',
                        Point(y=608, x=258),
                        Point(y=666, x=708),
                        invert=True,
                    ),
                ),
                do(nl, Wait(.25)),
                'CHECK',
            ),
            (always_matches, do(press('A'), Wait(.2)), 'TRADE'),
        ),
        'CHECK': (
            (is_shiny, do(), 'ALARM'),
            (always_matches, do(debounce.after(5), trade_one), 'TRADE'),
        ),
        **alarm('ALARM', quiet=args.quiet),
    }

    with serial.Serial(args.serial, 9600) as ser:
        run(vid=make_vid(), ser=ser, initial='INITIAL', states=states)


if __name__ == '__main__':
    raise SystemExit(main())
