from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from radio.model.song import Song


@dataclass(slots=True, frozen=True)
class Station:
    """
    Immutable radio station description.
    """

    name: str
    logo: Path | None
    song: Song
