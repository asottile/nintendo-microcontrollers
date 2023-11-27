from __future__ import annotations

import argparse
import concurrent.futures
import enum
import functools
import multiprocessing
import os.path
import sqlite3
from typing import NamedTuple

import cv2
import numpy

from scripts.engine import Color
from scripts.engine import get_text
from scripts.engine import match_px
from scripts.engine import Point
from scripts.engine import tessapi_int

HERE = os.path.dirname(os.path.abspath(__file__))

Gender = enum.IntEnum('Gender', 'MALE FEMALE GENDERLESS')


class Stats(NamedTuple):
    hp: int
    attack: int
    defense: int
    special_attack: int
    special_defense: int
    speed: int


class OT(NamedTuple):
    name: str
    idno: str


class Pokemon(NamedTuple):
    species: int

    level: int
    gender: Gender
    nature: str
    ability: str | None  # None in arceus

    trainer: OT
    language: str
    icon: str | None
    region: str
    ball: str

    stats: Stats
    ivs: Stats | None  # non-arceus
    els: Stats | None  # arceus


@functools.lru_cache
def icons() -> tuple[tuple[str, numpy.ndarray], ...]:
    icons_dir = os.path.join(HERE, 'icons')
    return tuple(
        (name.split('.')[0], cv2.imread(os.path.join(icons_dir, name)))
        for name in os.listdir(icons_dir)
    )


def get_icon(img: numpy.ndarray) -> str | None:
    tl = Point(y=68, x=793).norm(img.shape)
    br = Point(y=107, x=844).norm(img.shape)
    icon = img[tl.y:br.y, tl.x:br.x]

    for name, cand in icons():
        if numpy.array_equal(icon, cand):
            if name == 'none':
                return None
            else:
                return name
    else:
        cv2.imwrite('unknown-icon.png', icon)
        raise AssertionError('unknown icon!')


@functools.lru_cache
def balls() -> tuple[tuple[str, numpy.ndarray], ...]:
    balls_dir = os.path.join(HERE, 'balls')
    return tuple(
        (name.split('.')[0], cv2.imread(os.path.join(balls_dir, name)))
        for name in os.listdir(balls_dir)
    )


def get_ball(img: numpy.ndarray) -> str:
    tl = Point(y=72, x=292).norm(img.shape)
    br = Point(y=102, x=328).norm(img.shape)
    ball = img[tl.y:br.y, tl.x:br.x]

    for name, cand in balls():
        if numpy.array_equal(ball, cand):
            return name
    else:
        cv2.imwrite('unknown-ball.png', ball)
        raise AssertionError('unknown ball!')


def get_region(img: numpy.ndarray) -> str:
    tl = Point(y=565, x=509).norm(img.shape)
    br = Point(y=630, x=1252).norm(img.shape)

    crop = img[tl.y:br.y, tl.x:br.x]
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    thres = cv2.inRange(hsv, (100, 150, 150), (115, 255, 220))

    x, y, w, h = cv2.boundingRect(thres)
    x, y, w, h = x - 5, y - 5, w + 10, h + 10
    tl_t = Point(y=tl.y + y, x=tl.x + x).denorm(img.shape)
    br_t = Point(y=tl.y + y + h, x=tl.x + x + w).denorm(img.shape)

    parts = get_text(img, tl_t, br_t, invert=False).split()
    if len(parts) == 3 and parts[0] == 'the' and parts[2] == 'region':
        return parts[1]
    else:
        return ' '.join(parts)


def get_stats(img: numpy.ndarray) -> Stats:
    hp_s = get_text(
        img,
        Point(y=197, x=230),
        Point(y=217, x=287),
        invert=False,
        tessapi=tessapi_int(),
    )
    attack_s = get_text(
        img,
        Point(y=275, x=390),
        Point(y=303, x=452),
        invert=False,
        tessapi=tessapi_int(),
    )
    defense_s = get_text(
        img,
        Point(y=442, x=390),
        Point(y=470, x=456),
        invert=False,
        tessapi=tessapi_int(),
    )
    special_attack_s = get_text(
        img,
        Point(y=276, x=65),
        Point(y=302, x=130),
        invert=False,
        tessapi=tessapi_int(),
    )
    special_defense_s = get_text(
        img,
        Point(y=444, x=64),
        Point(y=469, x=129),
        invert=False,
        tessapi=tessapi_int(),
    )
    speed_s = get_text(
        img,
        Point(y=464, x=231),
        Point(y=486, x=294),
        invert=False,
        tessapi=tessapi_int(),
    )
    return Stats(
        hp=int(hp_s),
        attack=int(attack_s),
        defense=int(defense_s),
        special_attack=int(special_attack_s),
        special_defense=int(special_defense_s),
        speed=int(speed_s),
    )


def parse_pokemon(filename: str) -> Pokemon:
    img = cv2.imread(filename)

    species_s = get_text(
        img,
        Point(y=183, x=573),
        Point(y=204, x=628),
        invert=True,
    )
    species = int(species_s)

    level_s = get_text(
        img,
        Point(y=70, x=663),
        Point(y=102, x=757),
        invert=False,
    )
    level = int(level_s.split()[1])

    if match_px(Point(y=80, x=550), Color(b=204, g=71, r=27))(img):
        gender = Gender.MALE
    elif match_px(Point(y=82, x=544), Color(b=34, g=17, r=210))(img):
        gender = Gender.FEMALE
    else:
        gender = Gender.GENDERLESS

    nature = get_text(
        img,
        Point(y=566, x=214),
        Point(y=594, x=326),
        invert=False,
    )

    ability_s = get_text(
        img,
        Point(y=602, x=215),
        Point(y=633, x=473),
        invert=False,
    )
    if not ability_s.strip('—_'):  # arceus has no abilities
        ability = None
    else:
        ability = ability_s

    ot_name = get_text(
        img,
        Point(y=518, x=629),
        Point(y=554, x=841),
        invert=True,
    )
    ot_no = get_text(
        img,
        Point(y=519, x=999),
        Point(y=552, x=1249),
        invert=True,
    )
    ot = OT(ot_name, ot_no)

    lang = get_text(
        img,
        Point(y=128, x=36),
        Point(y=152, x=105),
        invert=False,
    )

    icon = get_icon(img)

    region = get_region(img)

    ball = get_ball(img)

    stats = get_stats(img)

    return Pokemon(
        species=species,

        level=level,
        gender=gender,
        nature=nature,
        ability=ability,

        trainer=ot,
        language=lang,
        icon=icon,
        region=region,

        ball=ball,
        stats=stats,

        # TODO
        ivs=None,
        els=None,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--imgs', default='home_screenshots')
    args = parser.parse_args()

    max_filename = max(
        s
        for s in os.listdir(args.imgs)
        if not s.endswith('_ivs.png')
    )
    max_n = int(os.path.splitext(max_filename)[0])

    fnames = [os.path.join(args.imgs, f'{i:04}.png') for i in range(max_n + 1)]

    cpus = multiprocessing.cpu_count()
    with concurrent.futures.ProcessPoolExecutor(cpus) as exe:
        ret = list(exe.map(parse_pokemon, fnames))

    create = '''\
CREATE TABLE pokemon (
    id INTEGER PRIMARY KEY,
    species INTEGER NOT NULL,
    level INTEGER NOT NULL,
    gender INTEGER NOT NULL,
    nature TEXT NOT NULL,
    ability TEXT NULL,

    trainer_name TEXT NOT NULL,
    trainer_idno TEXT NOT NULL,
    language TEXT NOT NULL,
    icon TEXT NULL,
    region TEXT NOT NULL,
    ball TEXT NOT NULL,

    stats_hp INTEGER NOT NULL,
    stats_attack INTEGER NOT NULL,
    stats_defense INTEGER NOT NULL,
    stats_special_attack INTEGER NOT NULL,
    stats_special_defense INTEGER NOT NULL,
    stats_speed INTEGER NOT NULL
);
'''
    insert = '''\
INSERT INTO pokemon VALUES (
    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
);
'''
    rows = [
        (
            i,
            pokemon.species,
            pokemon.level,
            pokemon.gender,
            pokemon.nature,
            pokemon.ability,
            pokemon.trainer.name,
            pokemon.trainer.idno,
            pokemon.language,
            pokemon.icon,
            pokemon.region,
            pokemon.ball,
            pokemon.stats.hp,
            pokemon.stats.attack,
            pokemon.stats.defense,
            pokemon.stats.special_attack,
            pokemon.stats.special_defense,
            pokemon.stats.speed,
        )
        for i, pokemon in enumerate(ret)
    ]

    with sqlite3.connect('db.db') as db:
        db.execute(create)
        db.executemany(insert, rows)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
