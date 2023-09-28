from __future__ import annotations

import subprocess

import cv2
import numpy

from scripts.engine import always_matches
from scripts.engine import do
from scripts.engine import Matcher
from scripts.engine import Point
from scripts.engine import Press
from scripts.engine import States
from scripts.engine import Wait

SERIAL_DEFAULT = '/dev/ttyACM0'


def region_colorish(
        top_left: Point,
        bottom_right: Point,
        hsv_low: tuple[int, int, int],
        hsv_high: tuple[int, int, int],
        ratio: float,
        *,
        quiet: bool = True,
) -> Matcher:
    def region_colorish_impl(frame: numpy.ndarray) -> bool:
        tl = top_left.norm(frame.shape)
        br = bottom_right.norm(frame.shape)

        crop = frame[tl.y:br.y, tl.x:br.x]
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, hsv_low, hsv_high)
        got_ratio = numpy.count_nonzero(mask) / mask.size
        if not quiet and got_ratio >= .001:
            print(f'{got_ratio=}')
        return got_ratio >= ratio
    return region_colorish_impl


def get_text_rotated(
        frame: numpy.ndarray,
        tl: Point,
        br: Point,
        *,
        invert: bool,
) -> str:
    crop = frame[tl.y:br.y, tl.x:br.x]
    crop = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    _, crop = cv2.threshold(
        crop, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU,
    )
    crop = cv2.rotate(crop, cv2.ROTATE_90_CLOCKWISE)
    if invert:
        crop = cv2.bitwise_not(crop)

    return subprocess.check_output(
        ('tesseract', '-', '-', '--psm', '7'),
        input=cv2.imencode('.png', crop)[1].tobytes(),
        stderr=subprocess.DEVNULL,
    ).strip().decode()


def alarm(name: str) -> States:
    return {
        name: (
            (
                always_matches,
                do(Press('!'), Wait(.25), Press('.'), Wait(.25)),
                name,
            ),
        ),
    }