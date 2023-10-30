from __future__ import annotations

from scripts.engine import do
from scripts.engine import Press
from scripts.engine import Wait


skip_day = do(
    Press('H'), Wait(1),
    Press('s'),
    Press('d', duration=.55),
    Press('A'), Wait(1),
    Press('s', duration=1.3),
    Press('A'), Wait(.75),
    Press('s', duration=.7),
    Press('A'), Wait(.75),
    Press('s'), Press('s'),
    Press('A'), Wait(.75),
    Press('d'), Press('w'),
    Press('d', duration=.6), Wait(.2), Press('A'), Wait(.75),
    Press('H'), Wait(1), Press('H'), Wait(2),
)
