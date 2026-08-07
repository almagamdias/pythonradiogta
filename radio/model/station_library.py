from __future__ import annotations

from dataclasses import dataclass

from radio.model.station import Station


@dataclass(slots=True, frozen=True)
class StationLibrary:
    """
    Collection of loaded radio stations.
    """

    stations: tuple[Station, ...]

    def __len__(self) -> int:
        return len(self.stations)

    def __iter__(self):
        return iter(self.stations)

    def __getitem__(self, index: int) -> Station:
        return self.stations[index]
