from __future__ import annotations

import sys
import time

import numpy

from scripts.engine import always_matches
from scripts.engine import bye
from scripts.engine import do
from scripts.engine import match_text
from scripts.engine import Point
from scripts.engine import Press
from scripts.engine import States
from scripts.engine import Wait

SERIAL_DEFAULT = 'COM1' if sys.platform == 'win32' else '/dev/ttyUSB0'

reset = do(Press('H'), Wait(1), Press('X'), Wait(.5), Press('A'), Wait(2.5))


class GameCrash:
    def __init__(self) -> None:
        self.check_after = 0.
        self.matcher = match_text(
            'The software was closed because an error occurred.',
            Point(y=307, x=306),
            Point(y=351, x=971),
            invert=True,
        )

    def record(self, vid: object, ser: object) -> None:
        self.check_after = time.time() + 30

    def check(self, frame: numpy.ndarray) -> bool:
        return time.time() > self.check_after and self.matcher(frame)


def alarm(name: str, *, quiet: bool) -> States:
    if quiet:
        return {
            name: (
                (
                    always_matches,
                    do(
                        Press('H'), Wait(1),
                        Press('H', duration=1), Wait(.5),
                        Press('A'),
                        bye,
                    ),
                    'UNREACHABLE',
                ),
            ),
        }
    else:
        return {
            name: (
                (
                    always_matches,
                    do(Press('!'), Wait(.25), Press('.'), Wait(.25)),
                    name,
                ),
            ),
        }
