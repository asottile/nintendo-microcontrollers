from __future__ import annotations

import sys

from scripts.engine import do
from scripts.engine import Press
from scripts.engine import Wait

SERIAL_DEFAULT = 'COM1' if sys.platform == 'win32' else '/dev/ttyUSB0'

reset = do(Press('H'), Wait(1), Press('X'), Wait(.5), Press('A'), Wait(2.5))
