from __future__ import annotations
from radio.model.types import Milliseconds

from dataclasses import dataclass


@dataclass(slots=True)
class StationState:
    """
    Runtime state of a radio station.
    """

    position_ms: Milliseconds = 0

    playing: bool = False

    last_update: float = 0.0
