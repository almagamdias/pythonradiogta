from __future__ import annotations
from radio.model.types import Milliseconds

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True, frozen=True)
class Song:
    """
    Represents a single audio file.

    For Gen1 this is the only file of the station.
    """

    path: Path
    duration_ms: int
