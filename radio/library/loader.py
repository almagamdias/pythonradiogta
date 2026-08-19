from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from radio.model.station_library import StationLibrary


class Loader(ABC):
    """Base class for all GTA radio library loaders."""

    @abstractmethod
    def load(self, root: Path) -> StationLibrary:
        """Load a station library."""
        raise NotImplementedError
