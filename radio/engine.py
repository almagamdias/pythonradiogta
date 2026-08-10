from __future__ import annotations

from radio.audio.player import AudioPlayer
from radio.model.song import Song
from radio.model.station import Station
from radio.model.station_library import StationLibrary

import random

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

        start_position = self._random_start_position(
            self.current_song.duration
        )

        self._player = AudioPlayer(
            self.current_song.path,
            start_position_ms=start_position,
        )
        self._player.play()

    def stop(self) -> None:
        if self._player is None:
            return

        self._player.stop()
        self._player = None

    def _random_start_position(self, duration_ms: int) -> int:
        margin_ms = min(10_000, duration_ms // 10)

        if duration_ms <= margin_ms:
            return 0

        return random.randrange(
            0,
            duration_ms - margin_ms,
        )

    def next_station(self) -> None:
        was_playing = self._player is not None

        if was_playing:
            self.stop()

        self._station_index = (
            self._station_index + 1
        ) % len(self._library)

        if was_playing:
            self.play()

    def previous_station(self) -> None:
        was_playing = self._player is not None

        if was_playing:
            self.stop()

        self._station_index = (
            self._station_index - 1
        ) % len(self._library)

        if was_playing:
            self.play()
