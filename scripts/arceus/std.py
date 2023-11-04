from __future__ import annotations

import argparse
import sys
import time

import serial

from scripts.engine import always_matches
from scripts.engine import bye
from scripts.engine import do
from scripts.engine import make_vid
from scripts.engine import match_text
from scripts.engine import Point
from scripts.engine import Press
from scripts.engine import run
from scripts.engine import States
from scripts.engine import Timeout
from scripts.engine import Wait
from scripts.switch import SERIAL_DEFAULT


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

    t0 = time.monotonic()

    def display_time(vid: object, ser: object) -> None:
        taken = (time.monotonic() - t0) / 60
        print(f'found after {taken:.1f} minutes')

    states: States = {
        'INITIAL': (
            (
                match_text(
                    'A space-time distortion seems to be forming!',
                    Point(y=100, x=465),
                    Point(y=126, x=816),
                    invert=True,
                ),
                do(
                    display_time,
                    Press('X'),
                    Wait(200), Press('H'), Wait(1),
                    maybe_sleep,
                    bye,
                ),
                'UNREACHABLE',
            ),
            (nudge.expired, do(Press('X'), nudge.after(180)), 'INITIAL'),
            (always_matches, Wait(1), 'INITIAL'),
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
