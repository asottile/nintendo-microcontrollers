from __future__ import annotations

import argparse
import functools
import math
import os.path
import sys
import time

import cv2
import numpy
import serial

from scripts.engine import always_matches
from scripts.engine import bye
from scripts.engine import do
from scripts.engine import getframe
from scripts.engine import make_vid
from scripts.engine import match_text
from scripts.engine import Point
from scripts.engine import Press
from scripts.engine import run
from scripts.engine import States
from scripts.engine import Timeout
from scripts.engine import Wait
from scripts.switch import SERIAL_DEFAULT


@functools.lru_cache(maxsize=1)
def _std_mask() -> tuple[numpy.ndarray, numpy.ndarray]:
    here = os.path.dirname(__file__)
    tmpl = cv2.imread(os.path.join(here, 'templates', 'std-icon.png'))
    mask = 255 - cv2.inRange(tmpl, tmpl[0][0], tmpl[0][0])
    return tmpl, mask


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--serial', default=SERIAL_DEFAULT)
    parser.add_argument('--sleep-after', action='store_true')
    args = parser.parse_args()

    if args.sleep_after:
        maybe_sleep = do(Press('H', duration=1), Press('A'))
    else:
        maybe_sleep = Press('!')

    nudge = Timeout()

    t0 = time.monotonic()

    def display_time(vid: object, ser: object) -> None:
        taken = (time.monotonic() - t0) / 60
        print(f'found after {taken:.1f} minutes')

    def wait(vid: cv2.VideCapture, ser: serial.Serial) -> None:
        do(
            Press('l'), Wait(1),
            Press('w', duration=1.5), Wait(.5),
            Press('-'), Wait(1),
            Press('w', duration=1), Wait(.5),
        )(vid, ser)

        frame = getframe(vid)

        tmpl, mask = _std_mask()
        match = cv2.matchTemplate(frame, tmpl, cv2.TM_CCOEFF_NORMED, mask=mask)
        _, _, _, (std_x, std_y) = cv2.minMaxLoc(match)
        print(f'std at: {std_x}, {std_y}')

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        thres1 = cv2.inRange(hsv, (174, 110, 160), (180, 180, 255))
        thres2 = cv2.inRange(hsv, (0, 110, 160), (6, 180, 255))
        thres = cv2.bitwise_or(thres1, thres2)

        contours, _ = cv2.findContours(
            thres, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE,
        )
        contour, = contours
        player_x, player_y, player_w, player_h = cv2.boundingRect(contour)
        print(f'player at {player_x}, {player_y}')

        dist = math.dist((player_x, player_y), (std_x, std_y))
        wait = 60 + dist * frame.shape[0] / 1024
        print(f'wait for: {wait:.2f}')

        poly = cv2.approxPolyDP(contour, 5, True)
        p1, p2, p3 = ((int(x), int(y)) for x, y in numpy.squeeze(poly))

        d1 = math.dist(p1, p2)
        d2 = math.dist(p2, p3)
        d3 = math.dist(p3, p1)

        def avg(p1: tuple[int, int], p2: tuple[int, int]) -> tuple[int, int]:
            p1_x, p1_y = p1
            p2_x, p2_y = p2
            return ((p1_x + p2_x) // 2, (p1_y + p2_y) // 2)

        if d1 < d2 and d1 < d3:
            base, point = avg(p1, p2), p3
        elif d2 < d1 and d2 < d3:
            base, point = avg(p2, p3), p1
        else:
            base, point = avg(p1, p3), p2

        dx = point[0] - base[0]
        dy = point[1] - base[1]

        mid_std = avg(
            (std_x, std_y),
            (std_x + tmpl.shape[1], std_y + tmpl.shape[0]),
        )

        std_dx = mid_std[0] - base[0]
        std_dy = mid_std[1] - base[1]

        zz = (0, 0)
        angle = math.acos(
            (std_dx * dx + std_dy * dy) /
            (math.dist(zz, (dx, dy)) * math.dist(zz, (std_dx, std_dy))),
        )

        # determine left or right
        mat = [
            [point[0] - base[0], mid_std[0] - base[0]],
            [point[1] - base[1], mid_std[1] - base[1]],
        ]
        det = mat[0][0] * mat[1][1] - mat[1][0] * mat[0][1]
        if det < 0:
            c = 'h'
        else:
            c = 'k'

        do(
            Press('B'), Wait(1),
            # conveniently, pi seconds gives us about a full rotation!
            Press(c, duration=angle / 2),
            Press('w', duration=.2), Wait(.5),
            Press('l'), Wait(1),
            Wait(wait),
        )(vid, ser)

    states: States = {
        'INITIAL': (
            (
                match_text(
                    'A space-time distortion seems to be forming!',
                    Point(y=100, x=465),
                    Point(y=126, x=816),
                    invert=True,
                ),
                do(
                    display_time,
                    wait,
                    Press('H'), Wait(1),
                    maybe_sleep,
                    bye,
                ),
                'UNREACHABLE',
            ),
            (nudge.expired, do(Press('X'), nudge.after(180)), 'INITIAL'),
            (always_matches, Wait(1), 'INITIAL'),
        ),
    }

    with serial.Serial(args.serial, 9600) as ser:
        run(
            vid=make_vid(),
            ser=ser,
            initial='INITIAL',
            states=states,
            transition_timeout=sys.maxsize,
        )


if __name__ == '__main__':
    raise SystemExit(main())
