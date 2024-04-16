from __future__ import annotations

import functools
import os.path

import cv2
import numpy

from scripts.engine import match_text
from scripts.engine import Point

_HERE = os.path.dirname(os.path.abspath(__file__))


def _extract_type(
        im: numpy.ndarray,
        dims: tuple[int, int, int],
) -> numpy.ndarray:
    im = cv2.resize(im, (dims[1], dims[0]))

    top_left = Point(y=102, x=1006).norm(dims)
    bottom_right = Point(y=196, x=1095).norm(dims)
    crop = im[top_left.y:bottom_right.y, top_left.x:bottom_right.x]

    color = numpy.array([71, 51, 39])
    t = numpy.array([1, 1, 1])
    return cv2.inRange(crop, color - t * 20, color + t * 20)


@functools.lru_cache
def _types(dims: tuple[int, int, int]) -> list[tuple[str, numpy.ndarray]]:
    types_dir = os.path.join(_HERE, 'types')

    return [
        (
            os.path.splitext(tp)[0],
            _extract_type(cv2.imread(os.path.join(types_dir, tp)), dims),
        )
        for tp in os.listdir(types_dir)
    ]


def raid_type(frame: numpy.ndarray) -> str:
    return _best(_extract_type(frame, frame.shape), _types(frame.shape))


@functools.lru_cache
def _sprites() -> list[tuple[str, numpy.ndarray]]:
    sprites_dir = os.path.join(_HERE, '../../sv-sprites')
    return [
        (
            os.path.splitext(fname)[0],
            cv2.resize(
                cv2.imread(
                    os.path.join(sprites_dir, fname),
                    flags=cv2.IMREAD_UNCHANGED,
                )[:, :, 3],
                (120, 120),
            ),
        )
        for fname in os.listdir(sprites_dir)
    ]


@functools.lru_cache
def _stars() -> list[tuple[str, numpy.ndarray]]:
    stars_dir = os.path.join(_HERE, 'stars')
    return [
        (
            os.path.splitext(fname)[0],
            cv2.imread(os.path.join(stars_dir, fname)),
        )
        for fname in os.listdir(stars_dir)
    ]


def _best(
        crop: numpy.ndarray,
        candidates: list[tuple[str, numpy.ndarray]],
) -> str:
    best_name = ''
    best_diff = 1e9
    for name, img in candidates:
        diff = numpy.average(cv2.absdiff(crop, img))
        if diff < best_diff:
            best_name = name
            best_diff = diff
    return best_name


def raid_pokemon(frame: numpy.ndarray) -> list[list[str | None]]:
    if match_text(
        'No new postings',
        Point(y=343, x=420),
        Point(y=383, x=619),
        invert=False,
    )(frame):
        return [[None] * 4, [None] * 4]

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, (100, 80, 55), (125, 160, 80))
    kernel = numpy.ones((3, 3), numpy.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    ret: list[list[str | None]] = [[], []]

    for p_y in range(2):
        star_y = 312 + 267 * p_y
        poke_y = 168 + 267 * p_y

        for p_x in range(4):
            star_x = 60 + 240 * p_x
            poke_x = 100 + 240 * p_x

            star_crop = frame[star_y:star_y + 24, star_x:star_x + 200]
            poke_crop = mask[poke_y:poke_y + 120, poke_x:poke_x + 120]

            if numpy.count_nonzero(poke_crop) == 0:
                ret[p_y].append(None)
            else:
                star = _best(star_crop, _stars())
                poke = _best(poke_crop, _sprites())
                ret[p_y].append(f'{star} {poke}')

    return ret


@functools.lru_cache(maxsize=1)
def _arrow_mask() -> tuple[numpy.ndarray, numpy.ndarray]:
    tmpl = cv2.imread(os.path.join(_HERE, 'templates', 'move_arrow.png'))
    mask = 255 - cv2.inRange(tmpl, tmpl[0][0], tmpl[0][0])
    return tmpl, mask


def attack_position(frame: numpy.ndarray) -> int:
    crop = frame[390:699, 889:987]
    arrow, mask = _arrow_mask()
    match = cv2.matchTemplate(crop, arrow, cv2.TM_CCOEFF_NORMED, mask=mask)
    _, _, _, (_, arrow_y) = cv2.minMaxLoc(match)
    return int(arrow_y / len(crop) * 4)
