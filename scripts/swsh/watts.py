from __future__ import annotations

import argparse
import datetime

import serial

from scripts.engine import always_matches
from scripts.engine import bye
from scripts.engine import do
from scripts.engine import make_vid
from scripts.engine import Press
from scripts.engine import run
from scripts.engine import States
from scripts.engine import Wait
from scripts.switch import SERIAL_DEFAULT
from scripts.swsh._bootup import bootup
from scripts.swsh._bootup import world
from scripts.swsh._mrb_date_skip import MrbDateSkip


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--serial', default=SERIAL_DEFAULT)
    parser.add_argument('--days', type=int)
    args = parser.parse_args()

    skipper = MrbDateSkip()
    end = skipper.dt + datetime.timedelta(days=args.days)

    def is_done(frame: object) -> bool:
        return skipper.dt >= end

    states: States = {
        **bootup('INITIAL', 'COUNTER'),
        'COUNTER': (
            (is_done, do(), 'SAVE'),
            (always_matches, do(), 'SKIP1'),
        ),
        'SAVE': (
            (
                world,
                do(
                    Press('X'), Wait(1),
                    Press('R'), Wait(1),
                    Press('A'), Wait(1),
                    bye,
                ),
                'UNREACHABLE',
            ),
        ),
        **skipper.skip('SKIP1', 'COUNTER'),
    }

    with serial.Serial(args.serial, 9600) as ser:
        run(vid=make_vid(), ser=ser, initial='INITIAL', states=states)


if __name__ == '__main__':
    raise SystemExit(main())
