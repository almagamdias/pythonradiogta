from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import radio.engine as engine_module
from radio.engine import RadioEngine
from radio.model.station_state import StationState


class FakeAudioPlayer:
    def __init__(self) -> None:
        self.overlay_calls: list[
            tuple[Path, bool]
        ] = []

        self.change_song_calls: list[
            tuple[Path, int]
        ] = []

        self.stop_overlay_calls = 0

    def play_overlay(
        self,
        path: Path,
        *,
        loop: bool = False,
    ) -> None:
        self.overlay_calls.append(
            (path, loop)
        )

    def change_song(
        self,
        path: Path,
        *,
        start_position_ms: int = 0,
    ) -> None:
        self.change_song_calls.append(
            (
                path,
                start_position_ms,
            )
        )

    def stop_overlay(self) -> None:
        self.stop_overlay_calls += 1


class FakeSwitchTimer:
    instances: list[FakeSwitchTimer] = []

    def __init__(
        self,
        *,
        delay: float,
        callback,
    ) -> None:
        self.delay = delay
        self.callback = callback
        self.start_calls = 0
        self.cancel_calls = 0

        self.instances.append(self)

    def start(self) -> None:
        self.start_calls += 1

    def cancel(self) -> None:
        self.cancel_calls += 1

    def fire(self) -> None:
        """Manually execute the timer callback."""
        self.callback()


def make_library():
    return [
        SimpleNamespace(
            name="Station 0",
            songs=[
                SimpleNamespace(
                    path=Path("station0.ogg"),
                    duration=100_000,
                )
            ],
        ),
        SimpleNamespace(
            name="Station 1",
            songs=[
                SimpleNamespace(
                    path=Path("station1.ogg"),
                    duration=100_000,
                )
            ],
        ),
        SimpleNamespace(
            name="Station 2",
            songs=[
                SimpleNamespace(
                    path=Path("station2.ogg"),
                    duration=100_000,
                )
            ],
        ),
    ]


def make_engine() -> tuple[
    RadioEngine,
    FakeAudioPlayer,
]:
    engine = RadioEngine(
        make_library()
    )

    player = FakeAudioPlayer()

    # Prepare the engine as if the radio is already playing.
    engine._player = player
    engine._state = StationState.ON_AIR

    engine._station_index = 0

    engine._radio_started_at = 0.0

    engine._station_start_positions = {
        0: 0,
        1: 0,
        2: 0,
    }

    # Avoid depending on real monotonic time.
    engine._station_position = (
        lambda station_index: 1234
    )

    return engine, player


def test_switch_starts_looping_overlay() -> None:
    FakeSwitchTimer.instances.clear()

    original_timer = engine_module.SwitchTimer
    engine_module.SwitchTimer = FakeSwitchTimer

    try:
        engine, player = make_engine()

        engine.next_station()

        assert engine.state is StationState.SWITCHING

        assert engine.pending_station is (
            engine.stations[1]
        )

        assert player.overlay_calls == [
            (
                engine_module.SWITCH_NOISE_PATH,
                True,
            )
        ]

        assert len(
            FakeSwitchTimer.instances
        ) == 1

        timer = FakeSwitchTimer.instances[0]

        assert timer.delay == 1.5
        assert timer.start_calls == 1

    finally:
        engine_module.SwitchTimer = original_timer


def test_repeated_switch_input_does_not_restart_overlay() -> None:
    FakeSwitchTimer.instances.clear()

    original_timer = engine_module.SwitchTimer
    engine_module.SwitchTimer = FakeSwitchTimer

    try:
        engine, player = make_engine()

        # 0 -> 1
        engine.next_station()

        # 1 -> 2
        engine.next_station()

        # 2 -> 1
        engine.previous_station()

        assert engine.state is StationState.SWITCHING

        assert engine.pending_station is (
            engine.stations[1]
        )

        # switch_noise must still be the same
        # single overlay for the whole switch sequence.
        assert player.overlay_calls == [
            (
                engine_module.SWITCH_NOISE_PATH,
                True,
            )
        ]

        # Timer is restarted on every new input.
        timer = FakeSwitchTimer.instances[0]

        assert timer.start_calls == 3

    finally:
        engine_module.SwitchTimer = original_timer


def test_completed_switch_stops_overlay() -> None:
    FakeSwitchTimer.instances.clear()

    original_timer = engine_module.SwitchTimer
    engine_module.SwitchTimer = FakeSwitchTimer

    try:
        engine, player = make_engine()

        engine.next_station()

        timer = FakeSwitchTimer.instances[0]

        assert engine.state is StationState.SWITCHING

        assert engine.pending_station is (
            engine.stations[1]
        )

        assert player.overlay_calls == [
            (
                engine_module.SWITCH_NOISE_PATH,
                True,
            )
        ]

        # Simulate the timer expiring.
        timer.fire()

        assert engine.state is StationState.ON_AIR

        assert engine.pending_station is None

        assert engine.current_station is (
            engine.stations[1]
        )

        assert player.change_song_calls == [
            (
                Path("station1.ogg"),
                1234,
            )
        ]

        assert player.stop_overlay_calls == 1

    finally:
        engine_module.SwitchTimer = original_timer


if __name__ == "__main__":
    test_switch_starts_looping_overlay()
    test_repeated_switch_input_does_not_restart_overlay()
    test_completed_switch_stops_overlay()

    print("Engine overlay tests passed.")
