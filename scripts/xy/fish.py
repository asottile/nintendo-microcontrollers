from __future__ import annotations

import argparse
import time

import serial

from scripts._alarm import alarm
from scripts._timeout import Timeout
from scripts.engine import all_match
from scripts.engine import always_matches
from scripts.engine import do
from scripts.engine import make_vid
from scripts.engine import Point
from scripts.engine import Press
from scripts.engine import run
from scripts.engine import States
from scripts.engine import Wait
from scripts.thrids import region_colorish
from scripts.thrids import SERIAL_DEFAULT


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--serial', default=SERIAL_DEFAULT)
    args = parser.parse_args()

    encounter_timeout = Timeout()

    t0 = duration = 0.

    def record_start(vid: object, ser: object) -> None:
        nonlocal t0
        t0 = time.monotonic()

    def battle_started(vid: object, ser: object) -> None:
        nonlocal duration
        duration = time.monotonic() - t0

    def is_shiny(frame: object) -> bool:
        print(f'delay: {duration:.2f}')
        return duration >= 12

    states: States = {
        'INITIAL': (
            (
                region_colorish(
                    Point(y=268, x=760),
                    Point(y=288, x=778),
                    (24, 100, 130),
                    (28, 150, 255),
                    .75,
                ),
                Press('Y'),
                'WAIT',
            ),
        ),
        'WAIT': (
            (
                region_colorish(
                    Point(y=339, x=289),
                    Point(y=380, x=326),
                    (2, 140, 160),
                    (12, 190, 250),
                    .001,
                ),
                do(Press('A'), encounter_timeout.after(3)),
                'WAIT_FOR_BATTLE',
            ),
        ),
        'WAIT_FOR_BATTLE': (
            (
                region_colorish(
                    Point(y=194, x=725),
                    Point(y=216, x=749),
                    (0, 0, 0),
                    (255, 25, 25),
                    .9,
                ),
                record_start,
                'WAIT_FOR_FIGHT',
            ),
            (
                all_match(
                    encounter_timeout.expired,
                    region_colorish(
                        Point(y=165, x=488),
                        Point(y=180, x=504),
                        (101, 130, 30),
                        (106, 160, 60),
                        .9,
                    ),
                ),
                do(Press('B'), Wait(2)),
                'INITIAL',
            ),
        ),
        'WAIT_FOR_FIGHT': (
            (
                region_colorish(
                    Point(y=298, x=844),
                    Point(y=313, x=859),
                    (2, 200, 200),
                    (5, 255, 255),
                    .7,
                ),
                battle_started,
                'DECIDE',
            ),
        ),
        'DECIDE': (
            (is_shiny, do(), 'ALARM'),
            (
                always_matches,
                do(Press('s'), Wait(.25), Press('d'), Wait(.25), Press('A')),
                'INITIAL',
            ),
        ),
        **alarm('ALARM', quiet=False),
    }

    with serial.Serial(args.serial, 9600) as ser:
        run(vid=make_vid(), ser=ser, initial='INITIAL', states=states)


if __name__ == '__main__':
    raise SystemExit(main())
