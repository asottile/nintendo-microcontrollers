from __future__ import annotations

import argparse

import cv2
import serial

from scripts.engine import all_match
from scripts.engine import always_matches
from scripts.engine import bye
from scripts.engine import Color
from scripts.engine import Counter
from scripts.engine import do
from scripts.engine import make_vid
from scripts.engine import match_px
from scripts.engine import match_text
from scripts.engine import Point
from scripts.engine import Press
from scripts.engine import run
from scripts.engine import States
from scripts.engine import Wait
from scripts.switch import SERIAL_DEFAULT


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--serial', default=SERIAL_DEFAULT)
    args = parser.parse_args()

    pos = Counter()

    def _move(vid: cv2.VideoCapture, ser: serial.Serial) -> None:
        if pos.n % 6 == 0:
            go = 's'
        elif (pos.n // 6) % 2 == 0:
            go = 'd'
        else:
            go = 'a'
        do(Press(go), Wait(.5))(vid, ser)

    select = match_text(
        'Select',
        Point(y=11, x=44),
        Point(y=38, x=103),
        invert=True,
    )

    states: States = {
        'INITIAL': (
            (
                all_match(
                    select,
                    match_px(Point(y=118, x=354), Color(b=187, g=218, r=217)),
                ),
                do(),
                'TRADE',
            ),
        ),
        'TRADE': (
            (select, do(Press('A'), Wait(.5), Press('A')), 'WAIT_FOR_TRADE'),
        ),
        'WAIT_FOR_TRADE': (
            (
                match_text(
                    'Trade it',
                    Point(y=389, x=769),
                    Point(y=411, x=842),
                    invert=False,
                ),
                Press('A'),
                'WAIT_FOR_TRADE_START',
            ),
        ),
        'WAIT_FOR_TRADE_START': (
            (select, do(), 'WAIT_FOR_TRADE_START'),
            (always_matches, do(), 'WAIT_FOR_TRADED'),
        ),
        'WAIT_FOR_TRADED': (
            (select, pos.increment, 'MOVE'),
        ),
        'MOVE': (
            (pos.equals(30), do(Press('!'), bye), 'UNREACHABLE'),
            (always_matches, _move, 'TRADE'),
        ),
    }

    with serial.Serial(args.serial, 9600) as ser:
        run(vid=make_vid(),  ser=ser,  initial='INITIAL',   states=states)


if __name__ == '__main__':
    raise SystemExit(main())
