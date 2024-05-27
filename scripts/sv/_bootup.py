from __future__ import annotations

from scripts.engine import Color
from scripts.engine import do
from scripts.engine import match_px
from scripts.engine import match_text
from scripts.engine import Point
from scripts.engine import Press
from scripts.engine import States
from scripts.engine import Wait
from scripts.switch import game_start
from scripts.switch import GameCrash

world = match_px(Point(y=598, x=1160), Color(b=17, g=203, r=244))


def bootup(start: str, success: str, fail: str) -> States:
    game_crash = GameCrash()

    return {
        start: (
            (game_start, do(Wait(1), Press('A')), f'{start}__CONTINUE'),
        ),
        f'{start}__CONTINUE': (
            (
                match_text(
                    'PRESS',
                    Point(y=489, x=802),
                    Point(y=530, x=898),
                    invert=True,
                ),
                do(Wait(2.5), Press('A'), Wait(1), game_crash.record),
                f'{start}__WORLD',
            ),
        ),
        f'{start}__WORLD': (
            (world, do(), success),
            (game_crash.check, do(Press('A'), Wait(1)), fail),
        ),
    }
