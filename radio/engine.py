from __future__ import annotations

from radio.audio.player import AudioPlayer
from radio.model.song import Song
from radio.model.station import Station
from radio.model.station_library import StationLibrary


class RadioEngine:
    """Main public API of the radio simulator."""

    def __init__(self, library: StationLibrary) -> None:
        self._library = library
        self._station_index = 0
        self._player: AudioPlayer | None = None

    @property
    def stations(self) -> StationLibrary:
        return self._library

    @property
    def current_station(self) -> Station:
        return self._library[self._station_index]

    @property
    def current_song(self) -> Song:
        return self.current_station.songs[0]

    def play(self) -> None:
        if self._player is not None:
            return

        self._player = AudioPlayer(self.current_song.path)
        self._player.play()

    def stop(self) -> None:
        if self._player is None:
            return

        self._player.stop()
        self._player = None
