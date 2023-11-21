from __future__ import annotations

import contextlib
import datetime

import cv2
import serial

from scripts.engine import all_match
from scripts.engine import always_matches
from scripts.engine import any_match
from scripts.engine import Color
from scripts.engine import do
from scripts.engine import match_px
from scripts.engine import match_text
from scripts.engine import Point
from scripts.engine import Press
from scripts.engine import run
from scripts.engine import States
from scripts.engine import Wait
from scripts.switch import clock
from scripts.swsh._bootup import world

try_ore = any_match(
    world,
    all_match(
        match_px(Point(y=10, x=1083), Color(b=47, g=175, r=218)),
        match_px(Point(y=10, x=1104), Color(b=18, g=164, r=200)),
    ),
)

invite_others = all_match(
    match_px(Point(y=457, x=1180), Color(b=16, g=16, r=16)),
    match_text(
        'Invite Others',
        Point(y=440, x=931),
        Point(y=472, x=1093),
        invert=True,
    ),
)


class Done(RuntimeError):
    pass


def done(vid: object, ser: object) -> None:
    raise Done


class MrbDateSkip:
    def __init__(self) -> None:
        self.dt = datetime.datetime(2020, 1, 1, 1, 0)

    def _increment(self, vid: cv2.VideoCapture, ser: serial.Serial) -> None:
        self.dt += datetime.timedelta(days=1)

        states: States = {
            **clock(self.dt, 'CLOCK_INITIAL', 'CLOCK_END'),
            'CLOCK_END': ((always_matches, done, 'UNREACHABLE'),),
        }

        with contextlib.suppress(Done):
            run(vid=vid, ser=ser, initial='CLOCK_INITIAL', states=states)

    def skip(self, start: str, end: str) -> States:
        ready_to_battle = all_match(
            match_px(Point(y=568, x=1150), Color(b=16, g=16, r=16)),
            match_text(
                'Ready to Battle!',
                Point(y=494, x=902),
                Point(y=531, x=1114),
                invert=False,
            ),
        )

        return {
            start: (
                (try_ore, do(Press('A'), Wait(.75)), start),
                (invite_others, do(Press('A'), Wait(1)), f'{start}__WAIT'),
            ),
            f'{start}__WAIT': (
                (
                    ready_to_battle,
                    do(Wait(1), Press('H'), Wait(1), self._increment),
                    f'{start}__WAIT_FOR_HOME',
                ),
            ),
            f'{start}__WAIT_FOR_HOME': (
                (
                    all_match(
                        match_px(
                            Point(y=705, x=13),
                            Color(b=217, g=217, r=217),
                        ),
                        match_text(
                            'Continue',
                            Point(y=668, x=1113),
                            Point(y=703, x=1224),
                            invert=False,
                        ),
                    ),
                    do(Press('A'), Wait(.5)),
                    f'{start}__WAIT_FOR_RETURN',
                ),
            ),
            f'{start}__WAIT_FOR_RETURN': (
                (
                    ready_to_battle,
                    do(Wait(1), Press('B'), Wait(.75), Press('A'), Wait(1)),
                    end,
                ),
            ),
        }
