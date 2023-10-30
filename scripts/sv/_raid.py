from __future__ import annotations

import functools
import os.path

import cv2
import numpy

from scripts.engine import Point


def _type(im: numpy.array, dims: tuple[int, int, int]) -> numpy.array:
    im = cv2.resize(im, (dims[1], dims[0]))

    top_left = Point(y=102, x=1006).norm(dims)
    bottom_right = Point(y=196, x=1095).norm(dims)
    crop = im[top_left.y:bottom_right.y, top_left.x:bottom_right.x]

    color = numpy.array([71, 51, 39])
    t = numpy.array([1, 1, 1])
    return cv2.inRange(crop, color - t * 20, color + t * 20)


@functools.lru_cache
def _types(dims: tuple[int, int, int]) -> tuple[tuple[str, numpy.array], ...]:
    types_dir = os.path.join(os.path.dirname(__file__), 'types')

    return tuple(
        (tp, _type(cv2.imread(os.path.join(types_dir, tp)), dims))
        for tp in os.listdir(types_dir)
    )


def raid_type(frame: numpy.array) -> str:
    types = _types(frame.shape)

    tp_im = _type(frame, frame.shape)
    _, tp = max(((im == tp_im).mean(), fname) for fname, im in types)
    return tp.split('.')[0]
