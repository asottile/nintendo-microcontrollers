from __future__ import annotations

import argparse
import time

import cv2
import numpy
import serial

from scripts._alarm import alarm
from scripts._timeout import Timeout
from scripts.engine import Action
from scripts.engine import always_matches
from scripts.engine import do
from scripts.engine import getframe
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

    def press(s: str, t: float) -> Action:
        def press_impl(vid: cv2.VideoCapture, ser: serial.Serial) -> None:
            print(s, end='', flush=True)
            ser.write(s.encode())
            time.sleep(t)
            ser.write(b'.')
        return press_impl

    shaky: tuple[tuple[str, int], ...] | None = None

    def record_shaky(vid: cv2.VideoCapture, ser: serial.Serial) -> None:
        nonlocal shaky

        frame1 = getframe(vid)
        Wait(.25)(vid, ser)
        frame2 = getframe(vid)

        def crop(frame: numpy.ndarray) -> numpy.ndarray:
            tl = Point(y=133, x=603).norm(frame.shape)
            br = Point(y=307, x=739).norm(frame.shape)
            height = br.y - tl.y
            width = br.x - tl.x

            crop = frame[tl.y:br.y, tl.x:br.x]
            # cover up bottom left corner
            cv2.fillConvexPoly(
                crop,
                numpy.array([
                    (0, height),
                    (0, 70),
                    (35, 70),
                    (35, 100),
                    (70, 100),
                    (70, 135),
                    (105, 135),
                    (110, height),
                ]),
                (0, 0, 0),
            )
            # cover up the top right corner
            cv2.fillConvexPoly(
                crop,
                numpy.array([
                    (70, 0),
                    (70, 60),
                    (110, 60),
                    (110, 90),
                    (width, 90),
                    (width, 0),
                ]),
                (0, 0, 0),
            )

            # make a grid
            for i in range(6):
                cv2.rectangle(
                    crop,
                    (max(35 * i - 8, 0), 0),
                    (35 * i + 5, height),
                    (0, 0, 0),
                    -1,
                )
                cv2.rectangle(
                    crop,
                    (0, 35 * (i + 1) - 15),
                    (width, 35 * (i + 1)),
                    (0, 0, 0),
                    -1,
                )
            return crop

        crop1 = crop(frame1)
        crop2 = crop(frame2)

        diff = cv2.absdiff(crop1, crop2)
        mask = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(mask, 20, 255, type=cv2.THRESH_BINARY)

        kernel = numpy.ones((10, 10), numpy.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        possible = {
            (0, 0), (0, 1),
            (1, 0), (1, 1),
            (2, 1), (2, 2),
            (3, 2), (3, 3),
            (4, 3),
        }
        highlighted = set()
        for cy, cx in possible:
            tl_g = Point(x=35 * cx + 5, y=35 * cy)
            br_g = Point(x=35 * (cx + 1) - 8, y=35 * (cy + 1) - 15)

            crop_g = mask[tl_g.y:br_g.y, tl_g.x:br_g.x]
            if numpy.count_nonzero(crop_g) / crop_g.size > .3:
                highlighted.add((cy, cx))

        if len(highlighted) == 1:
            (dy, dx), = highlighted
            md, ms = 6 - dy, 2 + dx
            # avoid the npc
            if md == 2:
                shaky = (('s', ms), ('d', md))
            else:
                shaky = (('d', md), ('s', ms))
            print()
            print(f'moving {shaky}')

    def is_shaky(frame: object) -> bool:
        return bool(shaky)

    def move_shaky(vid: cv2.VideoCapture, ser: serial.Serial) -> None:
        nonlocal shaky

        assert shaky is not None

        ops = [
            do(Press(c, duration=.2), Wait(.05))
            for c, n in shaky
            for _ in range(n)
        ]
        do(
            Press('Y'), Wait(.75), Press('Y'), Wait(.75),
            *ops,
        )(vid, ser)

        shaky = None

    encounter_timeout = Timeout()

    t0 = duration = 0.

    def encounter_start(vid: object, ser: object) -> None:
        nonlocal t0
        t0 = time.monotonic()

    def animation_end(vid: object, ser: object) -> None:
        nonlocal duration
        duration = time.monotonic() - t0

    def is_shiny(frame: object) -> bool:
        print(f'delay: {duration:.2f}')

        return duration >= 9

    world = region_colorish(
        Point(y=218, x=886),
        Point(y=242, x=900),
        (95, 175, 125),
        (105, 255, 255),
        .75,
    )

    states: States = {
        'INITIAL': (
            (
                world,
                # this will ensure we are in the top right
                do(
                    Press('w', duration=.5), Wait(.1),
                    Press('a', duration=.6), Wait(.1),
                    Press('w', duration=.5), Wait(.1),
                ),
                'RL',
            ),
        ),
        'RL': (
            (
                is_shaky,
                do(move_shaky, encounter_timeout.after(10)),
                'WAIT_FOR_ENCOUNTER',
            ),
            (
                always_matches,
                do(
                    press('d', .5),  # Wait(.1),
                    press('a', .6), Wait(.1),
                    record_shaky,
                ),
                'RL',
            ),
        ),
        'WAIT_FOR_ENCOUNTER': (
            (encounter_timeout.expired, do(), 'ON_BIKE'),
            (
                region_colorish(
                    Point(y=329, x=983),
                    Point(y=353, x=1007),
                    (170, 130, 20),
                    (180, 170, 60),
                    .75,
                ),
                encounter_start,
                'WAIT_FOR_FIGHT',
            ),
        ),
        'WAIT_FOR_FIGHT': (
            (
                region_colorish(
                    Point(y=248, x=947),
                    Point(y=274, x=965),
                    (173, 220, 130),
                    (180, 255, 180),
                    .75,
                ),
                animation_end,
                'DECIDE',
            ),
        ),
        'DECIDE': (
            (is_shiny, do(), 'ALARM'),
            (always_matches, do(), 'RUN'),
        ),
        'RUN': (
            (
                always_matches,
                do(Press('s'), Wait(.25), Press('d'), Wait(.25), Press('A')),
                'ON_BIKE',
            ),
        ),
        'ON_BIKE': (
            (
                world,
                do(Press('Y'), Wait(.75), Press('Y'), Wait(1)),
                'INITIAL',
            ),
        ),
        **alarm('ALARM', quiet=False),
    }

    with serial.Serial(args.serial, 9600) as ser:
        run(vid=make_vid(), ser=ser, initial='INITIAL', states=states)


if __name__ == '__main__':
    raise SystemExit(main())
