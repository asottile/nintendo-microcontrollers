from __future__ import annotations

from scripts.engine import do
from scripts.engine import match_text
from scripts.engine import Point
from scripts.engine import Press
from scripts.engine import States
from scripts.engine import Wait
from scripts.thrids import region_colorish


def bootup(start: str, end: str) -> States:
    return {
        start: (
            (
                region_colorish(
                    Point(y=15, x=462),
                    Point(y=24, x=490),
                    (109, 220, 120),
                    (113, 255, 140),
                    .9,
                ),
                do(Press('A'), Wait(.25)),
                f'{start}__PRESS_START',
            ),
        ),
        f'{start}__PRESS_START': (
            (
                match_text(
                    'PRESS START',
                    Point(y=429, x=387),
                    Point(y=477, x=871),
                    invert=False,
                ),
                do(Press('A'), Wait(.25)),
                f'{start}__MEMORY_CARD',
            ),
        ),
        f'{start}__MEMORY_CARD': (
            (
                match_text(
                    'The Memory Card in',
                    Point(y=450, x=136),
                    Point(y=493, x=547),
                    invert=True,
                ),
                do(Press('A'), Wait(.25)),
                f'{start}__CONTINUE',
            ),
        ),
        f'{start}__CONTINUE': (
            (
                region_colorish(
                    Point(y=312, x=542),
                    Point(y=325, x=563),
                    (127, 160, 170),
                    (130, 200, 200),
                    .9,
                ),
                do(Press('A'), Wait(.5), Press('w'), Press('A')),
                f'{start}__WAIT_FOR_PC',
            ),
        ),
        f'{start}__WAIT_FOR_PC': (
            (
                region_colorish(
                    Point(y=138, x=515),
                    Point(y=201, x=693),
                    (55, 110, 150),
                    (75, 230, 230),
                    .1,
                ),
                do(),
                end,
            ),
        ),
    }
