from dataclasses import dataclass
from pathlib import Path

from radio.model.song import Song


@dataclass(slots=True, frozen=True)
class Station:
    """Radio station."""

    name: str
    songs: tuple[Song, ...]
    logo: Path | None = None
