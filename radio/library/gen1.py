from __future__ import annotations

from pathlib import Path

from radio.audio.metadata_reader import read_duration
from radio.library.loader import Loader
from radio.model.song import Song
from radio.model.station import Station
from radio.model.station_library import StationLibrary
from radio.util.filesystem import (
    find_audio_files,
    find_logo,
    list_directories,
)


class Gen1Loader(Loader):
    """Loader for Gen1 radio stations."""

    def load(self, root: Path) -> StationLibrary:
        stations: list[Station] = []

        for station_dir in list_directories(root):
            audio_files = find_audio_files(station_dir)

            if not audio_files:
                continue

            stations.append(
                self._load_station(
                    station_dir,
                    audio_files,
                )
            )

        return StationLibrary(
            stations=tuple(stations),
        )

    def _load_station(
        self,
        station_dir: Path,
        audio_files: list[Path],
    ) -> Station:

        if len(audio_files) != 1:
            raise ValueError(
                f"Gen1 station must contain exactly one audio file: {station_dir}"
            )

        song = self._load_song(audio_files[0])

        return Station(
            name=station_dir.name,
            songs=(song,),
            logo=find_logo(station_dir),
        )

    def _load_song(self, audio_file: Path) -> Song:
        return Song(
            title=audio_file.stem,
            path=audio_file,
            duration=read_duration(audio_file),
        )
