from __future__ import annotations

import argparse

import cv2
import serial

from scripts.engine import always_matches
from scripts.engine import do
from scripts.engine import get_text
from scripts.engine import getframe
from scripts.engine import make_vid
from scripts.engine import Point
from scripts.engine import Press
from scripts.engine import run
from scripts.engine import States
from scripts.engine import Wait
from scripts.switch import alarm
from scripts.switch import reset
from scripts.switch import SERIAL_DEFAULT
from scripts.swsh._bootup import bootup
from scripts.swsh._bootup import world
from scripts.swsh._dialog_shiny_check import dialog
from scripts.swsh._dialog_shiny_check import dialog_shiny_check
from scripts.swsh._mrb_date_skip import invite_others
from scripts.swsh._mrb_date_skip import MrbDateSkip
from scripts.swsh._mrb_date_skip import try_ore


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--serial', default=SERIAL_DEFAULT)
    parser.add_argument('--quiet', action='store_true')
    args = parser.parse_args()

    skipper = MrbDateSkip()

    pokemon = ''

    def record_pokemon(vid: cv2.VideoCapture, ser: serial.Serial) -> None:
        nonlocal pokemon

        while True:
            text = get_text(
                getframe(vid),
                Point(y=592, x=108),
                Point(y=640, x=497),
                invert=True,
            )
            print(f'raw text: {text}')
            if text.endswith(' appeared!'):
                break

        pokemon = text.removesuffix(' appeared!').lower()

    def is_2_75(frame: object) -> bool:
        return pokemon in {'dragapult', 'frosmoth'}

    def is_2_5(frame: object) -> bool:
        return pokemon in {'dusknoir', 'togekiss', 'gourgeist', 'palossand'}

    def is_2_0(frame: object) -> bool:
        return pokemon in {'aromatisse', 'dottler', 'drampa'}

    def is_1_75(frame: object) -> bool:
        return pokemon in {
            'ribombee', 'shiinotic', 'golisopod', 'sliggoo', 'drakloak',
            'exeggutor', 'sylveon', 'grapploct', 'falinks', 'mamoswine',
            'sandygast',
        }

    states: States = {
        **bootup('INITIAL', 'INCREMENT1'),
        **skipper.skip('INCREMENT1', 'SAVE'),
        'SAVE': (
            (
                world,
                do(
                    Press('X'), Wait(1),
                    Press('R'), Wait(1),
                    Press('A'), Wait(1),
                ),
                'SKIP1',
            ),
        ),
        **skipper.skip('SKIP1', 'SKIP2'),
        **skipper.skip('SKIP2', 'SKIP3'),
        **skipper.skip('SKIP3', 'ENCOUNTER'),
        'ENCOUNTER': (
            (try_ore, do(Press('A'), Wait(.75)), 'ENCOUNTER'),
            (
                invite_others,
                do(
                    Press('s'), Wait(.5),
                    Press('A'), Wait(.75),
                    Press('A'), Wait(5),
                ),
                'WAIT_FOR_DIALOG',
            ),
        ),
        'WAIT_FOR_DIALOG': (
            (dialog, record_pokemon, 'CHOOSE_DIALOG'),
        ),
        'CHOOSE_DIALOG': (
            (is_2_75, do(), 'DIALOG_2_75'),
            (is_2_5, do(), 'DIALOG_2_5'),
            (is_2_0, do(), 'DIALOG_2_0'),
            (is_1_75, do(), 'DIALOG_1_75'),
            (always_matches, do(), 'DIALOG'),
        ),
        **dialog_shiny_check('DIALOG_2_75', 'RESET', 'ALARM', cutoff=2.75),
        **dialog_shiny_check('DIALOG_2_5', 'RESET', 'ALARM', cutoff=2.5),
        **dialog_shiny_check('DIALOG_2_0', 'RESET', 'ALARM', cutoff=2.0),
        **dialog_shiny_check('DIALOG_1_75', 'RESET', 'ALARM', cutoff=1.75),
        **dialog_shiny_check('DIALOG', 'RESET', 'ALARM', cutoff=1.25),
        'RESET': (
            (always_matches, reset, 'INITIAL'),
        ),
        **alarm('ALARM', quiet=args.quiet),
    }

    with serial.Serial(args.serial, 9600) as ser:
        run(vid=make_vid(), ser=ser, initial='INITIAL', states=states)


if __name__ == '__main__':
    raise SystemExit(main())
