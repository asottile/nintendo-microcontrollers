from __future__ import annotations

import argparse

import cv2
import serial

from scripts.engine import all_match
from scripts.engine import always_matches
from scripts.engine import any_match
from scripts.engine import Color
from scripts.engine import do
from scripts.engine import getframe
from scripts.engine import make_vid
from scripts.engine import match_px
from scripts.engine import match_text
from scripts.engine import Point
from scripts.engine import Press
from scripts.engine import run
from scripts.engine import Wait
from scripts.sv._bootup import world
from scripts.sv._raid import raid_appeared
from scripts.sv._raid import raid_communication_error
from scripts.sv._raid import raid_type
from scripts.switch import SERIAL_DEFAULT


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--serial', default=SERIAL_DEFAULT)
    args = parser.parse_args()

    def _raid_appeared(vid: cv2.VideoCapture, ser: serial.Serial) -> None:
        Wait(1)(vid, ser)

        frame = getframe(vid)

        tp = raid_type(frame)
        print(f'the type is {tp}')

        if tp in {
                'electric', 'grass', 'ground', 'dragon',
                'normal', 'ice', 'rock', 'steel', 'dark',
        }:
            do(
                Press('s'), Wait(1),
                Press('A'), Wait(5),
                Press('s'), Wait(1), Press('a'), Wait(1),
                Press('A'), Wait(1), Press('A'), Wait(5),
                Press('w'), Wait(1), Press('A'),
            )(vid, ser)
        else:
            Press('A')(vid, ser)

    states = {
        'INITIAL': (
            (
                world,
                do(Wait(1), Press('X'), Wait(1), Press('d'), Wait(.5)),
                'MENU',
            ),
        ),
        'MENU': (
            (
                match_px(Point(y=345, x=1166), Color(b=29, g=184, r=210)),
                do(Wait(1), Press('A')),
                'WAIT_FOR_PORTAL',
            ),
            (always_matches, do(Press('s'), Wait(.5)), 'MENU'),
        ),
        'WAIT_FOR_PORTAL': (
            (
                match_px(Point(y=676, x=191), Color(b=29, g=163, r=217)),
                # model takes a while to load
                Wait(5),
                'PORTAL',
            ),
        ),
        'PORTAL': (
            (
                match_px(Point(y=315, x=333), Color(b=22, g=198, r=229)),
                do(Wait(1), Press('A')),
                'WAIT_FOR_RAID_SELECT',
            ),
            (always_matches, do(Press('s'), Wait(.5)), 'PORTAL'),
        ),
        'WAIT_FOR_RAID_SELECT': (
            (
                match_px(
                    Point(y=676, x=191),
                    Color(b=156, g=43, r=133),  # violet
                    Color(b=33, g=98, r=197),  # scarlet
                ),
                Wait(1),
                'RAID_SELECT',
            ),
        ),
        'RAID_SELECT': (
            # TODO: later we can select based on disabled button
            (
                always_matches,
                do(
                    Press('a'), Wait(.4),
                    Press('s'), Wait(.4),
                    Press('A'), Wait(.4),
                ),
                'WAIT_FOR_RAID',
            ),
        ),
        'WAIT_FOR_RAID': (
            (
                all_match(
                    match_px(Point(y=597, x=656), Color(b=49, g=43, r=30)),
                    match_text(
                        "You weren't able to join.",
                        Point(y=528, x=351),
                        Point(y=597, x=656),
                        invert=True,
                    ),
                ),
                do(Wait(.5), Press('A'), Wait(.5), Press('A')),
                'WAIT_FOR_RAID',
            ),
            (
                match_text(
                    'If you join a random Tera Raid Battle but then',
                    Point(y=543, x=346),
                    Point(y=586, x=885),
                    invert=True,
                ),
                do(
                    Wait(1), Press('A'),
                    Wait(1), Press('A'),
                    Wait(1), Press('A'),
                ),
                'WAIT_FOR_RAID_SELECT',
            ),

            (
                raid_communication_error,
                do(
                    Wait(1), Press('A'),
                    Wait(2), Press('A'),
                    Wait(1), Press('A'),
                ),
                'WAIT_FOR_RAID',
            ),
            (
                all_match(
                    match_text(
                        'Even if you are victorious in this Tera Raid Battle,',
                        Point(y=547, x=351),
                        Point(y=580, x=918),
                        invert=True,
                    ),
                ),
                do(Wait(3), Press('A')),
                'WAIT_FOR_RAID',
            ),
            (
                raid_appeared,
                _raid_appeared,
                'RAID_ACCEPTED',
            ),
        ),
        'RAID_ACCEPTED': (
            (
                all_match(
                    match_px(Point(y=589, x=720), Color(b=49, g=43, r=30)),
                    match_text(
                        'The raid has been abandoned!',
                        Point(y=544, x=350),
                        Point(y=589, x=720),
                        invert=True,
                    ),
                ),
                do(Press('B'), Wait(1), Press('A')),
                'WAIT_FOR_RAID',
            ),
            (raid_appeared, Wait(.5), 'RAID_ACCEPTED'),
            (always_matches, Wait(5), 'RAID'),
        ),
        'RAID': (
            (
                all_match(
                    match_px(Point(y=529, x=1050), Color(b=31, g=196, r=221)),
                    match_text(
                        'Battle',
                        Point(y=529, x=1048),
                        Point(y=565, x=1123),
                        invert=False,
                    ),
                ),
                do(Press('A'), Wait(.2)),
                'RAID',
            ),
            (
                all_match(
                    match_px(Point(y=534, x=813), Color(b=244, g=237, r=220)),
                    match_px(Point(y=406, x=1188), Color(b=31, g=183, r=200)),
                ),
                do(Wait(.3), Press('R'), Wait(.3), Press('A'), Wait(.3)),
                'RAID',
            ),
            (
                any_match(
                    match_text(
                        'Collision Course',
                        Point(y=400, x=985),
                        Point(y=435, x=1155),
                        invert=False,
                    ),
                    match_text(
                        'Electro Drift',
                        Point(y=402, x=985),
                        Point(y=433, x=1115),
                        invert=False,
                    ),
                ),
                do(Press('A'), Wait(.2)),
                'RAID',
            ),
            (
                all_match(
                    match_px(Point(y=147, x=725), Color(b=26, g=188, r=212)),
                    match_px(Point(y=223, x=720), Color(b=34, g=181, r=213)),
                ),
                do(Press('A'), Wait(.2)),
                'RAID',
            ),
            (
                all_match(
                    match_px(Point(y=589, x=1045), Color(b=28, g=181, r=208)),
                    match_text(
                        'Catch',
                        Point(y=589, x=1045),
                        Point(y=622, x=1120),
                        invert=False,
                    ),
                ),
                do(Wait(.5), Press('s'), Wait(.5), Press('A'), Wait(8)),
                'WAIT_FOR_SUCCESS',
            ),
            (
                all_match(
                    match_px(Point(y=571, x=858), Color(b=152, g=152, r=146)),
                    match_px(Point(y=7, x=8), Color(b=234, g=234, r=234)),
                    match_text(
                        'You and the others were blown out of the cavern!',
                        Point(y=529, x=185),
                        Point(y=570, x=761),
                        invert=True,
                    ),
                ),
                Wait(10),
                'INITIAL',
            ),
        ),
        'WAIT_FOR_SUCCESS': (
            (
                match_text(
                    'Next',
                    Point(y=681, x=1219),
                    Point(y=703, x=1260),
                    invert=True,
                ),
                do(Wait(1), Press('A'), Wait(10)),
                'INITIAL',
            ),
        ),
    }

    with serial.Serial(args.serial, 9600) as ser:
        run(vid=make_vid(), ser=ser, initial='INITIAL', states=states)


if __name__ == '__main__':
    raise SystemExit(main())
