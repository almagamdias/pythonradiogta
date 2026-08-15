from __future__ import annotations

import random
from pathlib import Path
from time import monotonic

from radio.audio.player import AudioPlayer
from radio.constants import SWITCH_NOISE_PATH
from radio.model.song import Song
from radio.model.station import Station
from radio.model.station_library import StationLibrary
from radio.model.station_state import StationState
from radio.util.timer import SwitchTimer


class RadioEngine:
    """Main public API of the radio simulator."""

    def __init__(self, library: StationLibrary) -> None:
        self._volume = 1.0

        self._library = library
        self._station_index = 0

        self._player: AudioPlayer | None = None

        self._state = StationState.OFF

        self._switch_timer: SwitchTimer | None = None
        self._pending_station_index: int | None = None

        self._radio_started_at: float | None = None

        self._station_start_positions: dict[
            int,
            int,
        ] = {}

        self._switch_overlay_active = False

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

        return self._library[
            self._pending_station_index
        ]

    @property
    def player(self) -> AudioPlayer:
        if self._player is None:
            raise RuntimeError(
                "RadioEngine is not playing"
            )

        return self._player

    @property
    def volume(self) -> float:
        return self._volume

    @volume.setter
    def volume(self, value: float) -> None:
        if not 0.0 <= value <= 1.0:
            raise ValueError(
                "Volume must be between 0.0 and 1.0"
            )

        self._volume = float(value)

        if self._player is not None:
            self._player.volume = self._volume

    def play(self) -> None:
        """
        Start the radio.

        Every station receives its own random initial position.
        Station timelines then advance independently from the same
        radio start time.
        """
        if self._player is not None:
            return

        self._initialize_station_timelines()

        start_position = self._station_position(
            self._station_index
        )

        self._player = AudioPlayer(
            self.current_song.path,
            start_position_ms=start_position,
        )

        self._player.volume = self._volume

        self._state = StationState.ON_AIR

        self._player.play()

    def stop(self) -> None:
        """Stop the radio and reset station timelines."""
        if self._switch_timer is not None:
            self._switch_timer.cancel()
            self._switch_timer = None

        if self._player is not None:
            self._player.stop()
            self._player = None

        self._pending_station_index = None
        self._switch_overlay_active = False

        self._radio_started_at = None
        self._station_start_positions.clear()

        self._state = StationState.OFF

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

    def _initialize_station_timelines(self) -> None:
        self._radio_started_at = monotonic()

        self._station_start_positions.clear()

        for index, station in enumerate(self._library):
            song = station.songs[0]

            self._station_start_positions[index] = (
                self._random_start_position(
                    song.duration
                )
            )

    def _random_start_position(
        self,
        duration_ms: int,
    ) -> int:
        margin_ms = min(
            10_000,
            duration_ms // 10,
        )

        if duration_ms <= margin_ms:
            return 0

        return random.randrange(
            0,
            duration_ms - margin_ms,
        )

    def _station_position(
        self,
        station_index: int,
    ) -> int:
        start_position = (
            self._station_start_positions[
                station_index
            ]
        )

        station = self._library[station_index]
        duration = station.songs[0].duration

        if self._radio_started_at is None:
            return start_position

        elapsed_ms = int(
            (
                monotonic()
                - self._radio_started_at
            ) * 1000
        )

        if duration <= 0:
            return 0

        return (
            start_position + elapsed_ms
        ) % duration

    def _begin_switch(
        self,
        station_index: int,
    ) -> None:
        self._pending_station_index = station_index
        self._state = StationState.SWITCHING

        # One overlay per actual switch sequence.
        #
        # Repeated next/previous presses while the timer is running
        # only replace the pending destination. They do not create
        # additional switch noises.
        if (
            self._player is not None
            and not self._switch_overlay_active
        ):
            self._player.play_overlay(
                SWITCH_NOISE_PATH
            )

            self._switch_overlay_active = True

        if self._switch_timer is None:
            self._switch_timer = SwitchTimer(
                delay=1.5,
                callback=self._complete_switch,
            )

        self._switch_timer.start()

    def _complete_switch(self) -> None:
        station_index = (
            self._pending_station_index
        )

        if station_index is None:
            return

        self._station_index = station_index
        self._pending_station_index = None

        self._switch_overlay_active = False

        if self._player is None:
            self._state = StationState.OFF
            return

        position = self._station_position(
            station_index
        )

        # change_song() keeps the existing audio device alive and,
        # importantly, cancels the old switch overlay.
        self._player.change_song(
            self.current_song.path,
            start_position_ms=position,
        )

        self._state = StationState.ON_AIR
