from __future__ import annotations

import argparse
import time

import numpy
import serial

from scripts.engine import all_match
from scripts.engine import always_matches
from scripts.engine import Color
from scripts.engine import do
from scripts.engine import make_vid
from scripts.engine import match_px
from scripts.engine import Matcher
from scripts.engine import Point
from scripts.engine import Press
from scripts.engine import run
from scripts.engine import States
from scripts.engine import Wait
from scripts.switch import reset
from scripts.switch import SERIAL_DEFAULT
from scripts.swsh._bootup import bootup
from scripts.swsh._mrb_date_skip import invite_others
from scripts.swsh._mrb_date_skip import MrbDateSkip
from scripts.swsh._mrb_date_skip import try_ore


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--serial', default=SERIAL_DEFAULT)
    parser.add_argument('--quiet', action='store_true')
    parser.add_argument(
        '--stars',
        choices=(3, 4, 5),
        type=int,
        required=True,
        action='append',
    )
    args = parser.parse_args()

    skipper = MrbDateSkip()

    star_matchers = (
        match_px(Point(y=58, x=70), Color(b=234, g=234, r=234)),
        match_px(Point(y=60, x=130), Color(b=234, g=233, r=235)),
        match_px(Point(y=60, x=191), Color(b=234, g=236, r=230)),
        match_px(Point(y=59, x=254), Color(b=236, g=235, r=231)),
        match_px(Point(y=60, x=314), Color(b=234, g=234, r=234)),
    )

    def stars(n: int) -> Matcher:
        def stars_impl(frame: numpy.ndarray) -> bool:
            return all_match(*star_matchers[:n])(frame)
        return stars_impl

    def requested(n: int) -> Matcher:
        def requested_impl(frame: numpy.ndarray) -> bool:
            return n in args.stars
        return requested_impl

    first = True
    seen: list[numpy.ndarray] = []

    def check(frame: numpy.ndarray) -> bool:
        nonlocal first

        if first:
            print('skipping first!')
            first = False
            return False

        tl = Point(y=287, x=207)
        br = Point(y=476, x=408)
        crop = frame[tl.y:br.y, tl.x:br.x]

        for img in seen:
            if numpy.array_equal(img, crop):
                print('already seen!')
                return False

        ser.write(b'!')
        time.sleep(.1)
        ser.write(b'.')
        try:
            input('is this the right raid? (enter to skip, ^D to exit)')
        except (EOFError, KeyboardInterrupt):
            print('\nbye!')
            raise SystemExit(0)
        else:
            seen.append(crop)
            return False

    states: States = {
        **bootup('INITIAL', 'SKIP1'),
        **skipper.skip('SKIP1', 'SKIP2'),
        **skipper.skip('SKIP2', 'SKIP3'),
        **skipper.skip('SKIP3', 'TO_DEN'),
        'TO_DEN': (
            (try_ore, do(Press('A'), Wait(.75)), 'TO_DEN'),
            (invite_others, do(), 'CHECK'),
        ),
        'CHECK': (
            (all_match(stars(5), requested(5), check), do(), 'UNREACHABLE'),
            (stars(5), do(), 'RESET'),
            (all_match(stars(4), requested(4), check), do(), 'UNREACHABLE'),
            (stars(4), do(), 'RESET'),
            (all_match(stars(3), requested(3), check), do(), 'UNREACHABLE'),
            (stars(3), do(), 'RESET'),
        ),
        'RESET': (
            (always_matches, reset, 'INITIAL'),
        ),
    }

    with serial.Serial(args.serial, 9600) as ser:
        run(vid=make_vid(), ser=ser, initial='INITIAL', states=states)


if __name__ == '__main__':
    raise SystemExit(main())
