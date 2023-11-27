from __future__ import annotations

import argparse
import os.path

import cv2
import serial

from scripts.engine import always_matches
from scripts.engine import bye
from scripts.engine import do
from scripts.engine import getframe
from scripts.engine import make_vid
from scripts.engine import match_text
from scripts.engine import Point
from scripts.engine import Press
from scripts.engine import run
from scripts.engine import States
from scripts.engine import Wait
from scripts.switch import SERIAL_DEFAULT
from scripts.thrids import region_colorish


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--serial', default=SERIAL_DEFAULT)
    parser.add_argument('--imgs', default='home_screenshots')
    args = parser.parse_args()

    os.makedirs(args.imgs, exist_ok=True)

    i = 0

    def main(vid: cv2.VideoCapture, ser: serial.Serial) -> None:
        cv2.imwrite(os.path.join(args.imgs, f'{i:04}.png'), getframe(vid))

    def ivs(vid: cv2.VideoCapture, ser: serial.Serial) -> None:
        cv2.imwrite(os.path.join(args.imgs, f'{i:04}_ivs.png'), getframe(vid))

    def increment(vid: object, ser: object) -> None:
        nonlocal i
        i += 1

    states: States = {
        'INITIAL': (
            (
                # non shiny
                region_colorish(
                    Point(y=70, x=908),
                    Point(y=103, x=940),
                    (0, 0, 200),
                    (255, 255, 255),
                    .97,
                ),
                bye,
                'UNREACHABLE',
            ),
            (
                match_text(
                    'View Stats',
                    Point(y=692, x=943),
                    Point(y=716, x=1037),
                    invert=False,
                ),
                do(Press('Y'), Wait(.25)),
                'SCREENSHOT_MAIN',
            ),
            (
                match_text(
                    'Condition',
                    Point(y=691, x=943),
                    Point(y=717, x=1035),
                    invert=False,
                ),
                do(Press('Y'), Wait(.25), Press('Y'), Wait(.25)),
                'SCREENSHOT_MAIN',
            ),
            (always_matches, do(), 'SCREENSHOT_MAIN'),
        ),
        'SCREENSHOT_MAIN': (
            (always_matches, main, 'MAYBE_SCREENSHOT_IVS'),
        ),
        'MAYBE_SCREENSHOT_IVS': (
            (
                match_text(
                    'Base Points',
                    Point(y=691, x=900),
                    Point(y=717, x=1003),
                    invert=False,
                ),
                do(Press('Y'), Wait(.25), Press('Y'), Wait(.25), ivs),
                'NEXT',
            ),
            (always_matches, do(), 'NEXT'),
        ),
        'NEXT': (
            (always_matches, do(Press('d'), Wait(.5), increment), 'INITIAL'),
        ),
    }

    with serial.Serial(args.serial, 9600) as ser:
        run(vid=make_vid(), ser=ser, initial='INITIAL', states=states)


if __name__ == '__main__':
    raise SystemExit(main())
