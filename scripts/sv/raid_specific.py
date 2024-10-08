from __future__ import annotations

import argparse
import enum
import os
import sys

import cv2
import numpy
import serial

from scripts.engine import all_match
from scripts.engine import always_matches
from scripts.engine import Color
from scripts.engine import do
from scripts.engine import get_text
from scripts.engine import getframe
from scripts.engine import make_vid
from scripts.engine import match_px
from scripts.engine import match_text
from scripts.engine import Point
from scripts.engine import Press
from scripts.engine import run
from scripts.engine import States
from scripts.engine import Timeout
from scripts.engine import Wait
from scripts.sv._raid import attack_position
from scripts.sv._raid import raid_appeared
from scripts.sv._raid import raid_communication_error
from scripts.sv._raid import raid_type
from scripts.sv._raid import select_pokemon
from scripts.sv._raid import to_raid_select
from scripts.switch import SERIAL_DEFAULT

Choice = enum.Enum('Choice', 'ATT_0 ATT_1')


def bellibolt(turn: int) -> Choice:
    if turn > 5:
        return Choice.ATT_1
    elif turn % 2 == 0:
        return Choice.ATT_0
    else:
        return Choice.ATT_1


def arceus_flying(turn: int) -> Choice:
    if turn > 5:
        return Choice.ATT_1
    elif turn % 2 == 0:
        return Choice.ATT_0
    else:
        return Choice.ATT_1


def arceus_dark(turn: int) -> Choice:
    return arceus_flying(turn)


def arceus_fairy(turn: int) -> Choice:
    return arceus_flying(turn)


def serperior(turn: int) -> Choice:
    if turn > 3:
        return Choice.ATT_1
    else:
        return Choice.ATT_0


def zapdos(turn: int) -> Choice:
    return Choice.ATT_0


POSITIONS = (
    bellibolt,
    arceus_flying,
    arceus_dark,
    arceus_fairy,
    serperior,
    zapdos,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--serial', default=SERIAL_DEFAULT)
    parser.add_argument('--targets-file', default='sv-targets')
    args = parser.parse_args()

    with open(args.targets_file) as f:
        targets = f.read().splitlines()

    tera_debounce = Timeout()

    chosen = ''
    chosen_pos = (-1, -1)

    def detect(vid: cv2.VideoCapture, ser: object) -> None:
        nonlocal chosen, chosen_pos

        pokemon = select_pokemon(getframe(vid))

        for i, pokes in enumerate(pokemon):
            joined = ', '.join(p or '(none)' for p in pokes)
            print(f'row{i}: {joined}')

        chosen = ''
        chosen_pos = (-1, -1)
        best = sys.maxsize
        for y, row in enumerate(pokemon):
            for x, poke in enumerate(row):
                if poke is None:
                    continue
                try:
                    rank = targets.index(poke)
                except ValueError:
                    continue
                else:
                    if rank < best:
                        chosen = poke
                        chosen_pos = (y, x)
                        best = rank

        if chosen:
            print(f'choosing {chosen} @ {chosen_pos}')
        else:
            print('no raid targets found')

    def navigate_to_raid(vid: cv2.VideoCapture, ser: serial.Serial) -> None:
        for _ in range(chosen_pos[1] + 1):
            do(Press('d'), Wait(.25))(vid, ser)
        for _ in range(chosen_pos[0]):
            do(Press('s'), Wait(.25))(vid, ser)

    tp = ''
    strategy = bellibolt
    turn = 0

    def increment_turn(vid: object, ser: object) -> None:
        nonlocal turn
        turn += 1

    def choose_strategy(vid: cv2.VideoCapture, ser: serial.Serial) -> None:
        nonlocal tp, strategy, turn
        tp = raid_type(getframe(vid))
        print(f'type is: {tp}')

        _, poke = chosen.split()

        if tp in {'steel', 'dark', 'rock', 'ice', 'normal'}:
            strategy = zapdos
        elif tp == 'ground':
            strategy = serperior
        elif tp in {'flying', 'water'}:
            strategy = bellibolt
        elif tp in {'grass', 'fighting', 'bug'}:
            strategy = arceus_flying
        elif tp in {'psychic', 'ghost', 'electric'}:
            strategy = arceus_dark
        elif tp == 'dragon':
            strategy = arceus_fairy
        elif tp in {'fire', 'poison', 'fairy'}:
            strategy = bellibolt
        else:
            print('!!! did not select a strategy?')
            strategy = bellibolt

        print(f'strategy chosen: {strategy.__name__}')

        turn = 0

    def select_attacker(vid: cv2.VideoCapture, ser: serial.Serial) -> None:
        pos = POSITIONS.index(strategy)
        if pos > 0:
            do(
                Press('s'), Wait(1), Press('A'), Wait(5),
                Press('a'), Wait(1),
            )(vid, ser)
            for _ in range(pos):
                do(Press('s'), Wait(.25))(vid, ser)
            do(
                Press('A'), Wait(1),
                Press('A'), Wait(5),
                Press('w'), Wait(1),
            )(vid, ser)

        Press('A')(vid, ser)

    def sent_to_box(frame: numpy.ndarray) -> bool:
        if not match_px(Point(y=539, x=343), Color(b=49, g=43, r=30))(frame):
            return False

        text = get_text(
            frame,
            Point(y=535, x=339),
            Point(y=602, x=945),
            invert=False,
        )
        return text.endswith('has been sent to your Boxes!')

    def screen(vid: cv2.VideoCapture, ser: object) -> None:
        frame = getframe(vid)
        os.makedirs('caught', exist_ok=True)
        n = len(os.listdir('caught'))
        cv2.imwrite(f'caught/{n:04}.png', frame)

    move_select = all_match(
        match_px(Point(y=681, x=571), Color(b=247, g=241, r=242)),
        match_text(
            'Move Info',
            Point(y=669, x=620),
            Point(y=691, x=701),
            invert=True,
        ),
    )

    states: States = {
        **to_raid_select('INITIAL', 'RAID_SELECT'),
        'RAID_SELECT': (
            (
                match_text(
                    'Connect to Internet',
                    Point(y=680, x=1031),
                    Point(y=706, x=1176),
                    invert=True,
                ),
                lambda *a: sys.exit(25),
                'UNREACHABLE',
            ),
            (
                always_matches,
                do(Wait(1), Press('a'), Wait(.25), detect),
                'RAID_CHOOSE',
            ),
        ),
        'RAID_CHOOSE': (
            (lambda _: chosen == '', do(), 'WAIT_FOR_NEW'),
            (
                always_matches,
                do(navigate_to_raid, Press('A')),
                'WAIT_FOR_RAID',
            ),
        ),
        'WAIT_FOR_NEW': (
            (
                match_px(Point(y=659, x=1007), Color(b=185, g=121, r=56)),
                do(Wait(1), Press('X'), Wait(2)),
                'RAID_SELECT',
            ),
            (always_matches, Wait(1), 'WAIT_FOR_NEW'),
        ),
        'WAIT_FOR_RAID': (
            (
                match_text(
                    "You weren't able to join.",
                    Point(y=545, x=356),
                    Point(y=588, x=645),
                    invert=True,
                ),
                do(Wait(2), Press('A')),
                'WAIT_FOR_NEW',
            ),
            (
                raid_communication_error,
                do(Wait(2), Press('A'), Wait(2), Press('A')),
                'WAIT_FOR_NEW',
            ),
            (
                raid_appeared,
                do(Wait(1), choose_strategy, select_attacker),
                'WAIT_FOR_START',
            ),
        ),
        'WAIT_FOR_START': (
            (
                match_text(
                    'The raid has been abandoned!',
                    Point(y=544, x=350),
                    Point(y=589, x=720),
                    invert=True,
                ),
                do(Press('B'), Wait(1)),
                'WAIT_FOR_NEW',
            ),
            (
                raid_communication_error,
                do(Wait(2), Press('A'), Wait(2), Press('A')),
                'WAIT_FOR_NEW',
            ),
            (raid_appeared, Wait(.5), 'WAIT_FOR_START'),
            (always_matches, do(), 'RAID'),
        ),
        'RAID': (
            (
                all_match(
                    match_px(Point(y=532, x=1048), Color(b=21, g=180, r=208)),
                    match_text(
                        'Battle',
                        Point(y=532, x=1049),
                        Point(y=562, x=1117),
                        invert=False,
                    ),
                ),
                do(Press('A'), Wait(.75)),
                'RAID',
            ),
            (
                all_match(
                    tera_debounce.expired,
                    move_select,
                    match_px(Point(y=637, x=806), Color(b=232, g=233, r=231)),
                    match_px(Point(y=555, x=800), Color(b=232, g=232, r=232)),
                    match_px(Point(y=556, x=825), Color(b=233, g=235, r=223)),
                ),
                do(Press('R'), Wait(.5), tera_debounce.after(10)),
                'RAID',
            ),
            (
                all_match(
                    lambda _: strategy(turn) == Choice.ATT_0,
                    move_select,
                    lambda frame: attack_position(frame) == 0,
                ),
                do(Press('A'), Wait(.3)),
                'RAID',
            ),
            (
                all_match(
                    lambda _: strategy(turn) == Choice.ATT_1,
                    move_select,
                    lambda frame: attack_position(frame) == 1,
                ),
                do(Press('A'), Wait(.3)),
                'RAID',
            ),
            (
                all_match(
                    lambda _: strategy(turn) == Choice.ATT_0,
                    move_select,
                    lambda frame: attack_position(frame) != 0,
                ),
                do(Press('w'), Wait(.3)),
                'RAID',
            ),
            (
                all_match(
                    lambda _: strategy(turn) == Choice.ATT_1,
                    move_select,
                    lambda frame: attack_position(frame) != 1,
                ),
                do(Press('s'), Wait(.3)),
                'RAID',
            ),
            (
                all_match(
                    match_px(Point(y=690, x=1185), Color(b=239, g=234, r=235)),
                    match_text(
                        'Back',
                        Point(y=683, x=1221),
                        Point(y=704, x=1257),
                        invert=True,
                    ),
                    match_px(Point(y=309, x=723), Color(b=23, g=212, r=227)),
                ),
                do(Press('A'), Wait(1), increment_turn),
                'RAID',
            ),
            (
                all_match(
                    match_px(Point(y=589, x=1049), Color(b=32, g=184, r=215)),
                    match_text(
                        'Catch',
                        Point(y=587, x=1050),
                        Point(y=622, x=1115),
                        invert=False,
                    ),
                ),
                do(Wait(.5), Press('A'), Wait(.5)),
                'CATCH_SELECT_BALL',
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
            (always_matches, Wait(.25), 'RAID'),
        ),
        'CATCH_SELECT_BALL': (
            (
                match_text(
                    'Dusk Ball',
                    Point(y=498, x=587),
                    Point(y=529, x=689),
                    invert=True,
                ),
                do(Press('A'), Wait(.5)),
                'WAIT_FOR_CAUGHT',
            ),
            (always_matches, do(Press('d'), Wait(.5)), 'CATCH_SELECT_BALL'),
        ),
        'WAIT_FOR_CAUGHT': (
            (
                match_text(
                    'Next',
                    Point(y=681, x=1219),
                    Point(y=703, x=1260),
                    invert=True,
                ),
                do(Wait(3), screen, Press('A')),
                'WAIT_FOR_BOX',
            ),
            (always_matches, Wait(1), 'WAIT_FOR_CAUGHT'),
        ),
        'WAIT_FOR_BOX': (
            (sent_to_box, do(Wait(1), Press('A'), Wait(2)), 'INITIAL'),
            (always_matches, Wait(1), 'WAIT_FOR_BOX'),
        ),
    }

    with serial.Serial(args.serial, 9600) as ser:
        run(vid=make_vid(), ser=ser, initial='INITIAL', states=states)


if __name__ == '__main__':
    raise SystemExit(main())
