from __future__ import annotations

import argparse
from typing import NamedTuple

import cv2
import numpy
import serial

from scripts.engine import always_matches
from scripts.engine import do
from scripts.engine import Matcher
from scripts.engine import Point
from scripts.engine import Press
from scripts.engine import States
from scripts.engine import tess_text_u8
from scripts.engine import Wait

SERIAL_DEFAULT = '/dev/ttyACM0'


def region_colorish(
        top_left: Point,
        bottom_right: Point,
        hsv_low: tuple[int, int, int],
        hsv_high: tuple[int, int, int],
        ratio: float,
        *,
        quiet: bool = True,
) -> Matcher:
    def region_colorish_impl(frame: numpy.ndarray) -> bool:
        tl = top_left.norm(frame.shape)
        br = bottom_right.norm(frame.shape)

        crop = frame[tl.y:br.y, tl.x:br.x]
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, hsv_low, hsv_high)
        got_ratio = numpy.count_nonzero(mask) / mask.size
        if not quiet and got_ratio >= .001:
            print(f'{got_ratio=}')
        return got_ratio >= ratio
    return region_colorish_impl


def get_text_rotated(
        frame: numpy.ndarray,
        tl: Point,
        br: Point,
        *,
        invert: bool,
) -> str:
    crop = frame[tl.y:br.y, tl.x:br.x]
    crop = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    _, crop = cv2.threshold(
        crop, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU,
    )
    crop = cv2.rotate(crop, cv2.ROTATE_90_CLOCKWISE)
    if invert:
        crop = cv2.bitwise_not(crop)

    return tess_text_u8(crop)


def alarm(name: str) -> States:
    return {
        name: (
            (
                always_matches,
                do(Press('!'), Wait(.25), Press('.'), Wait(.25)),
                name,
            ),
        ),
    }


_POS = 1 << 7
_X = 1 << 6
_HIGH = 1 << 5
_MASK = _HIGH - 1


def touch(ser: serial.Serial, *, x: int, y: int) -> None:
    assert 0 <= x < 320 and 0 <= y < 240, (x, y)
    print(f'touch({x=}, {y=})')
    bts = bytes([
        _POS | _X | _HIGH | (((_MASK << 5) & x) >> 5),
        _POS | _X | 0 | (_MASK & x),
        _POS | 0 | _HIGH | (((_MASK << 5) & y) >> 5),
        _POS | 0 | 0 | (_MASK & y),
        *b't',
    ])
    ser.write(bts)


class Touch(NamedTuple):
    x: int
    y: int

    def __call__(self, vid: object, ser: serial.Serial) -> None:
        touch(ser, x=self.x, y=self.y)


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command', required=True)

    touch_parser = subparsers.add_parser('touch')
    touch_parser.add_argument('--serial', default=SERIAL_DEFAULT)
    touch_parser.add_argument('x', type=int)
    touch_parser.add_argument('y', type=int)
    args = parser.parse_args()

    if args.command == 'touch':
        with serial.Serial(args.serial, 9600) as ser:
            touch(ser, x=args.x, y=args.y)
    else:
        raise AssertionError(f'unreachable: {args.command=}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
