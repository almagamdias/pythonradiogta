from __future__ import annotations
from enum import Enum

class StationState(Enum):
    OFF = "off"
    ON_AIR = "on_air"
    SWITCHING = "switching"
