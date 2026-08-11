from __future__ import annotations

from radio.audio.player import AudioPlayer
from radio.model.song import Song
from radio.model.station import Station
from radio.model.station_library import StationLibrary
from radio.model.station_state import StationState
from radio.util.timer import SwitchTimer
from radio.constants import SWITCH_NOISE_PATH

from pathlib import Path

import random

class RadioEngine:
    """Main public API of the radio simulator."""

    def __init__(self, library: StationLibrary) -> None:
        self._library = library
        self._station_index = 0
        self._player: AudioPlayer | None = None
        self._state = StationState.OFF
        self._switch_timer: SwitchTimer | None = None
        self._pending_station_index: int | None = None

    @property
    def stations(self) -> StationLibrary:
        return self._library

    @property
    def current_station(self) -> Station:
        return self._library[self._station_index]

    @property
    def current_song(self) -> Song:
        return self.current_station.songs[0]

    @property
    def state(self) -> StationState:
        return self._state

    @property
    def is_switching(self) -> bool:
        return self._state is StationState.SWITCHING

    @property
    def pending_station(self) -> Station | None:
        if self._pending_station_index is None:
            return None

        return self._library[self._pending_station_index]

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
        self._state = StationState.ON_AIR
        self._player.play()

    def stop(self) -> None:
        if self._player is None:
            self._state = StationState.OFF
            return

        self._player.stop()
        self._player = None
        self._state = StationState.OFF

    def _random_start_position(self, duration_ms: int) -> int:
        margin_ms = min(10_000, duration_ms // 10)

        if duration_ms <= margin_ms:
            return 0

        return random.randrange(
            0,
            duration_ms - margin_ms,
        )

    def next_station(self) -> None:
        base_index = (
            self._pending_station_index
            if self._pending_station_index is not None
            else self._station_index
        )

        next_index = (
            base_index + 1
        ) % len(self._library)

        if self._state is StationState.OFF:
            self._station_index = next_index
            return

        self._begin_switch(next_index)

    def previous_station(self) -> None:
        base_index = (
            self._pending_station_index
            if self._pending_station_index is not None
            else self._station_index
        )

        previous_index = (
            base_index - 1
        ) % len(self._library)

        if self._state is StationState.OFF:
            self._station_index = previous_index
            return

        self._begin_switch(previous_index)

    def _begin_switch(self, station_index: int) -> None:
        self._pending_station_index = station_index
        self._state = StationState.SWITCHING

        if self._player is not None:
            self._player.play_overlay(SWITCH_NOISE_PATH)

        if self._switch_timer is None:
            self._switch_timer = SwitchTimer(
                delay=1.1,
                callback=self._complete_switch,
            )

        self._switch_timer.start()

    def _complete_switch(self) -> None:
        station_index = self._pending_station_index

        if station_index is None:
            return

        self._station_index = station_index
        self._pending_station_index = None

        self.stop()
        self.play()
