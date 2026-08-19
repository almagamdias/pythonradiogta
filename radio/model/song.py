from dataclasses import dataclass
from pathlib import Path

from radio.model.types import Milliseconds


@dataclass(slots=True, frozen=True)
class Song:
    """Audio track."""

    title: str
    path: Path
    duration: Milliseconds
