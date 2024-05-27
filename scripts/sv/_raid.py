from __future__ import annotations

import functools
import os.path

import cv2
import numpy

from scripts.engine import always_matches
from scripts.engine import any_match
from scripts.engine import Color
from scripts.engine import do
from scripts.engine import match_px
from scripts.engine import match_text
from scripts.engine import Point
from scripts.engine import Press
from scripts.engine import States
from scripts.engine import Wait
from scripts.sv._bootup import world

_HERE = os.path.dirname(os.path.abspath(__file__))

raid_appeared = match_text(
    'Remaining Time',
    Point(y=97, x=179),
    Point(y=129, x=333),
    invert=False,
)

raid_communication_error = any_match(
    match_text(
        'An error has occurred.',
        Point(y=239, x=329),
        Point(y=276, x=614),
        invert=True,
    ),
    match_text(
        'Please try again later.',
        Point(y=362, x=272),
        Point(y=397, x=1012),
        invert=True,
    ),
    match_text(
        'Please start again from the beginning.',
        Point(y=355, x=388),
        Point(y=385, x=861),
        invert=True,
    ),
    match_text(
        'Communication with the other Trainer was',
        Point(y=315, x=373),
        Point(y=349, x=906),
        invert=True,
    ),
    match_text(
        'Communication ended due to an error.',
        Point(y=331, x=393),
        Point(y=368, x=884),
        invert=True,
    ),
)


def to_raid_select(start: str, end: str) -> States:
    portal_open = match_text(
        'Mystery Gift',
        Point(y=535, x=122),
        Point(y=566, x=241),
        invert=True,
    )

    return {
        start: (
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
            (portal_open, Wait(5), 'PORTAL'),
        ),
        'PORTAL': (
            (
                match_px(Point(y=315, x=333), Color(b=22, g=198, r=229)),
                do(),
                'PRESS_RAID',
            ),
            (always_matches, do(Press('s'), Wait(.5)), 'PORTAL'),
        ),
        'PRESS_RAID': (
            (portal_open, do(Press('A'), Wait(1)), 'PRESS_RAID'),
            (always_matches, do(), 'WAIT_FOR_RAID_SELECT'),
        ),
        'WAIT_FOR_RAID_SELECT': (
            (
                match_text(
                    'TERA RAID BATTLE SEARCH',
                    Point(y=12, x=75),
                    Point(y=42, x=374),
                    invert=True,
                ),
                do(),
                end,
            ),
        ),
    }


def _imgs(d: str) -> list[tuple[str, numpy.ndarray]]:
    return [
        (
            os.path.splitext(f)[0],
            cv2.imread(os.path.join(d, f), flags=cv2.IMREAD_UNCHANGED),
        )
        for f in os.listdir(d)
    ]


def _extract_type(
        im: numpy.ndarray,
        dims: tuple[int, int, int],
) -> numpy.ndarray:
    im = cv2.resize(im, (dims[1], dims[0]))

    top_left = Point(y=102, x=1006).norm(dims)
    bottom_right = Point(y=196, x=1095).norm(dims)
    crop = im[top_left.y:bottom_right.y, top_left.x:bottom_right.x]

    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    return cv2.inRange(hsv, (99, 50, 50), (115, 180, 80))


@functools.lru_cache
def _types(dims: tuple[int, int, int]) -> list[tuple[str, numpy.ndarray]]:
    return [
        (name, _extract_type(img, dims))
        for name, img in _imgs(os.path.join(_HERE, 'types'))
    ]


def raid_type(frame: numpy.ndarray) -> str:
    return _best(_extract_type(frame, frame.shape), _types(frame.shape))


@functools.lru_cache
def _sprites(size: tuple[int, int]) -> list[tuple[str, numpy.ndarray]]:
    return [
        (name, cv2.resize(img[:, :, 3], size))
        for name, img in _imgs(os.path.join(_HERE, '../../sv-sprites'))
    ]


@functools.lru_cache
def _select_stars() -> list[tuple[str, numpy.ndarray]]:
    return _imgs(os.path.join(_HERE, 'select-stars'))


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


def _poke_mask(crop: numpy.ndarray) -> numpy.ndarray:
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, (100, 80, 55), (125, 160, 80))
    kernel = numpy.ones((3, 3), numpy.uint8)
    return cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)


def select_pokemon(frame: numpy.ndarray) -> list[list[str | None]]:
    if match_text(
        'No new postings',
        Point(y=343, x=420),
        Point(y=383, x=619),
        invert=False,
    )(frame):
        return [[None] * 4, [None] * 4]

    mask = _poke_mask(frame)

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
                star = _best(star_crop, _select_stars())
                poke = _best(poke_crop, _sprites((120, 120)))
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
