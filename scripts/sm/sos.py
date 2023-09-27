from __future__ import annotations

import argparse
import time

import cv2
import numpy
import serial

from scripts._alarm import alarm
from scripts.engine import all_match
from scripts.engine import always_matches
from scripts.engine import any_match
from scripts.engine import do
from scripts.engine import getframe
from scripts.engine import make_vid
from scripts.engine import Point
from scripts.engine import Press
from scripts.engine import run
from scripts.engine import States
from scripts.engine import Wait
from scripts.engine import Write
from scripts.thrids import get_text_rotated
from scripts.thrids import region_colorish
from scripts.thrids import SERIAL_DEFAULT


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--serial', default=SERIAL_DEFAULT)
    parser.add_argument('--pp', type=int, required=True)
    parser.add_argument('--max-pp', type=int, required=True)
    args = parser.parse_args()

    pp = args.pp
    max_pp = args.max_pp
    fight_menu = True
    bag_adrenaline = True

    def fight_selected(frame: object) -> bool:
        return fight_menu

    def bag_selected(frame: object) -> bool:
        return not fight_menu

    def toggle_fight(vid: object, ser: object) -> None:
        nonlocal fight_menu
        fight_menu = not fight_menu

    def adrenaline_selected(frame: object) -> bool:
        return bag_adrenaline

    def leppa_selected(frame: object) -> bool:
        return not bag_adrenaline

    def toggle_adrenaline(vid: object, ser: object) -> None:
        nonlocal bag_adrenaline
        bag_adrenaline = not bag_adrenaline

    def can_leppa(frame: object) -> bool:
        return max_pp - pp >= 10

    def used_leppa(vid: object, ser: object) -> None:
        nonlocal pp
        pp += 10
        print(f'pp => {pp} (leppa)')

    def used_move(vid: object, ser: object) -> None:
        nonlocal pp
        pp -= 1
        print(f'pp => {pp} (move)')

    def appeared_text(frame: numpy.ndarray) -> bool:
        s = get_text_rotated(
            frame,
            Point(y=454, x=576),
            Point(y=611, x=602),
            invert=True,
        )
        return s.endswith('appeared!')

    pokemon = 'unknown'

    def detect_pokemon(vid: cv2.VideoCapture, ser: object) -> None:
        nonlocal pokemon

        frame = getframe(vid)
        cv2.imwrite('pkmn.png', frame)

        tl = Point(y=305, x=398)
        br = Point(y=349, x=441)

        crop = frame[tl.y:br.y, tl.x:br.x]
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)

        reds = cv2.inRange(hsv, (150, 70, 140), (165, 160, 200))
        reds_ct = numpy.count_nonzero(reds)
        oranges = cv2.inRange(hsv, (5, 20, 110), (15, 60, 200))
        oranges_ct = numpy.count_nonzero(oranges)

        if reds_ct > 0:
            pokemon = 'floette red'
        elif oranges_ct > 0:
            pokemon = 'floette orange'
        else:
            pokemon = 'floette white'

        print(f'pokemon: {pokemon}')

    t0 = delay = 0.

    def dialog_stop(vid: object, ser: object) -> None:
        nonlocal t0
        t0 = time.monotonic()

    def time_end(vid: object, ser: object) -> None:
        nonlocal delay
        delay = time.monotonic() - t0

    def is_shiny_target(frame: object) -> bool:
        return pokemon == 'floette white' and is_shiny(frame)

    def is_shiny(frame: object) -> bool:
        print(f'delay: {delay:.03f}')
        return delay >= .5

    begin = any_match(
        region_colorish(
            Point(y=307, x=826),
            Point(y=331, x=853),
            (0, 130, 150),
            (2, 160, 220),
            .05,
        ),
        region_colorish(
            Point(y=307, x=826),
            Point(y=331, x=853),
            (176, 130, 150),
            (180, 160, 220),
            .05,
        ),
    )

    dialog = region_colorish(
        Point(y=136, x=592),
        Point(y=189, x=607),
        (110, 200, 60),
        (115, 255, 160),
        .5,
    )

    hp_bar = region_colorish(
        Point(y=291, x=311),
        Point(y=325, x=315),
        (57, 130, 100),
        (65, 255, 255),
        .15,
    )

    states: States = {
        'INITIAL': (
            (begin, do(), 'CHOOSE'),
        ),
        'CHOOSE': (
            (hp_bar, do(), 'ATTACK'),
            (always_matches, do(), 'ITEM'),
        ),
        'ATTACK': (
            (
                bag_selected,
                do(Press('d'), Wait(.25), toggle_fight),
                'ATTACK',
            ),
            (
                always_matches,
                do(
                    Press('A'), Wait(.75),
                    Press('A'), Wait(.75),
                    Press('A'), Wait(3),
                    used_move,
                ),
                'WAIT',
            ),
        ),
        'ITEM': (
            (
                fight_selected,
                do(Press('a'), Wait(.25), Press('s'), Wait(.25), toggle_fight),
                'ITEM',
            ),
            (can_leppa, do(Press('A'), Wait(1)), 'LEPPA'),
            (always_matches, do(Press('A'), Wait(1)), 'ORB'),
        ),
        'LEPPA': (
            (
                adrenaline_selected,
                do(
                    Press('d'), Wait(.5),
                    Press('d'), Wait(.5),
                    toggle_adrenaline,
                ),
                'LEPPA',
            ),
            (
                always_matches,
                do(
                    Press('A'), Wait(.5),
                    Press('A'), Wait(.5),
                    Press('A'), Wait(.5),
                    Press('A'), Wait(3),
                    used_leppa,
                ),
                'WAIT',
            ),
        ),
        'ORB': (
            (
                leppa_selected,
                do(
                    Press('a'), Wait(.5),
                    Press('a'), Wait(.5),
                    toggle_adrenaline,
                ),
                'ORB',
            ),
            (
                always_matches,
                do(
                    Press('A'), Wait(.5),
                    Press('A'), Wait(3),
                ),
                'WAIT',
            ),
        ),
        'WAIT': (
            (
                all_match(dialog, appeared_text),
                detect_pokemon,
                'WAIT_FOR_DIALOG_GONE',
            ),
            (begin, do(), 'INITIAL'),
            (always_matches, do(Write('B'), Wait(.025), Write('.')), 'WAIT'),
        ),
        'WAIT_FOR_DIALOG_GONE': (
            (any_match(dialog, appeared_text), do(), 'WAIT_FOR_DIALOG_GONE'),
            (always_matches, dialog_stop, 'WAIT_FOR_BAR'),
        ),
        'WAIT_FOR_BAR': (
            (hp_bar, time_end, 'CHECK'),
        ),
        'CHECK': (
            (is_shiny_target, do(), 'ALARM'),
            (is_shiny, Press('!', duration=.5), 'INITIAL'),
            (always_matches, do(), 'INITIAL'),
        ),
        **alarm('ALARM', quiet=False),
    }

    with serial.Serial(args.serial, 9600) as ser:
        run(vid=make_vid(), ser=ser, initial='INITIAL', states=states)


if __name__ == '__main__':
    raise SystemExit(main())
