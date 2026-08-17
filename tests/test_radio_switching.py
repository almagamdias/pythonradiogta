from __future__ import annotations

from pathlib import Path

import radio.engine as engine_module
from radio.engine import RadioEngine
from radio.model.song import Song
from radio.model.station import Station
from radio.model.station_library import StationLibrary
from radio.model.station_state import StationState


class FakePlayer:
    """Fake AudioPlayer for engine switching tests."""

    def __init__(
        self,
        path: Path,
        *,
        start_position_ms: int = 0,
    ) -> None:
        self.path = path
        self.start_position_ms = start_position_ms

        self.volume = 1.0

        self.overlay_calls: list[
            tuple[Path, bool]
        ] = []

        self.stop_overlay_calls = 0

        self.change_song_calls: list[
            tuple[Path, int]
        ] = []

        self.play_called = False
        self.stop_called = False

    def play(self) -> None:
        self.play_called = True

    def stop(self) -> None:
        self.stop_called = True

    def play_overlay(
        self,
        path: Path,
        *,
        loop: bool = False,
    ) -> None:
        self.overlay_calls.append(
            (
                path,
                loop,
            )
        )

    def stop_overlay(self) -> None:
        self.stop_overlay_calls += 1

    def change_song(
        self,
        path: Path,
        start_position_ms: int = 0,
    ) -> None:
        self.change_song_calls.append(
            (
                path,
                start_position_ms,
            )
        )


class FakeSwitchTimer:
    """Fake SwitchTimer that can be completed manually."""

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
        self.started = False

        self.instances.append(self)

    def start(self) -> None:
        self.start_calls += 1
        self.started = True

    def cancel(self) -> None:
        self.cancel_calls += 1
        self.started = False

    def fire(self) -> None:
        """Manually fire the timer callback."""
        self.started = False
        self.callback()


def _install_fakes() -> tuple[object, object]:
    """
    Replace the real AudioPlayer and SwitchTimer.

    Returns the original classes so they can be restored.
    """
    original_player = engine_module.AudioPlayer
    original_timer = engine_module.SwitchTimer

    engine_module.AudioPlayer = FakePlayer
    engine_module.SwitchTimer = FakeSwitchTimer

    FakeSwitchTimer.instances.clear()

    return (
        original_player,
        original_timer,
    )


def _restore_fakes(
    original_player: object,
    original_timer: object,
) -> None:
    """Restore the real AudioPlayer and SwitchTimer."""
    engine_module.AudioPlayer = original_player
    engine_module.SwitchTimer = original_timer

def _make_station(name: str) -> Station:
    song = Song(
        title=f"{name} Song",
        path=Path(f"{name.lower().replace(' ', '_')}.ogg"),
        duration=120_000,
    )

    return Station(
        name=name,
        songs=[song],
    )


def _make_engine() -> RadioEngine:
    """Create an engine with five fake stations."""
    library = StationLibrary(
        [
            _make_station("Station A"),
            _make_station("Station B"),
            _make_station("Station C"),
            _make_station("Station D"),
            _make_station("Station E"),
        ]
    )

    return RadioEngine(library)


def test_single_switch() -> None:
    """One station switch reaches the requested destination."""
    original_player, original_timer = _install_fakes()

    try:
        engine = _make_engine()
        engine.play()

        player = engine.player

        assert engine.current_station.name == "Station A"
        assert engine.state is StationState.ON_AIR

        engine.next_station()

        assert engine.pending_station is not None
        assert (
            engine.pending_station.name
            == "Station B"
        )

        assert engine.state is StationState.SWITCHING

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

        timer.fire()

        assert (
            engine.current_station.name
            == "Station B"
        )

        assert engine.pending_station is None
        assert engine.state is StationState.ON_AIR

        assert player.stop_overlay_calls == 1

        assert len(player.change_song_calls) == 1

        change_path, start_position = (
            player.change_song_calls[0]
        )

        assert change_path == Path("station_b.ogg")

        assert 0 <= start_position < 120_000

    finally:
        _restore_fakes(
            original_player,
            original_timer,
        )


def test_repeated_switches_keep_one_overlay() -> None:
    """
    Repeated inputs during one switch sequence only
    change the pending destination.

    They must not start additional switch overlays.
    """
    original_player, original_timer = _install_fakes()

    try:
        engine = _make_engine()
        engine.play()

        player = engine.player

        engine.next_station()
        engine.next_station()
        engine.next_station()
        engine.previous_station()

        # A -> B -> C -> D -> C
        assert engine.pending_station is not None
        assert (
            engine.pending_station.name
            == "Station C"
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

        assert timer.start_calls == 4

        timer.fire()

        assert (
            engine.current_station.name
            == "Station C"
        )

        assert engine.pending_station is None

        assert player.stop_overlay_calls == 1

        assert len(
            player.change_song_calls
        ) == 1

        assert (
            player.change_song_calls[0][0]
            == Path("station_c.ogg")
        )

    finally:
        _restore_fakes(
            original_player,
            original_timer,
        )


def test_last_selected_station_wins() -> None:
    """
    When several stations are selected during the delay,
    the last selected station must become active.
    """
    original_player, original_timer = _install_fakes()

    try:
        engine = _make_engine()
        engine.play()

        player = engine.player

        engine.next_station()  # B
        engine.next_station()  # C
        engine.next_station()  # D
        engine.next_station()  # E

        assert engine.pending_station is not None
        assert (
            engine.pending_station.name
            == "Station E"
        )

        timer = FakeSwitchTimer.instances[0]

        timer.fire()

        assert (
            engine.current_station.name
            == "Station E"
        )

        assert engine.pending_station is None

        assert (
            player.change_song_calls[-1][0]
            == Path("station_e.ogg")
        )

        assert player.stop_overlay_calls == 1

    finally:
        _restore_fakes(
            original_player,
            original_timer,
        )


def test_switch_back_to_original_station() -> None:
    """A -> B -> A must finish on station A."""
    original_player, original_timer = _install_fakes()

    try:
        engine = _make_engine()
        engine.play()

        player = engine.player

        engine.next_station()
        engine.previous_station()

        assert engine.pending_station is not None
        assert (
            engine.pending_station.name
            == "Station A"
        )

        timer = FakeSwitchTimer.instances[0]

        timer.fire()

        assert (
            engine.current_station.name
            == "Station A"
        )

        assert engine.pending_station is None
        assert engine.state is StationState.ON_AIR

        assert player.stop_overlay_calls == 1

        assert (
            player.change_song_calls[-1][0]
            == Path("station_a.ogg")
        )

    finally:
        _restore_fakes(
            original_player,
            original_timer,
        )


def test_overlay_is_looping() -> None:
    """
    The switch noise must be started with loop=True.
    """
    original_player, original_timer = _install_fakes()

    try:
        engine = _make_engine()
        engine.play()

        player = engine.player

        engine.next_station()

        assert len(
            player.overlay_calls
        ) == 1

        overlay_path, loop = (
            player.overlay_calls[0]
        )

        assert (
            overlay_path
            == engine_module.SWITCH_NOISE_PATH
        )

        assert loop is True

    finally:
        _restore_fakes(
            original_player,
            original_timer,
        )


def test_overlay_stops_after_switch() -> None:
    """
    Completing the station switch must stop the
    looping switch overlay.
    """
    original_player, original_timer = _install_fakes()

    try:
        engine = _make_engine()
        engine.play()

        player = engine.player

        engine.next_station()

        assert player.stop_overlay_calls == 0

        timer = FakeSwitchTimer.instances[0]

        timer.fire()

        assert player.stop_overlay_calls == 1

        assert engine.pending_station is None

        assert engine.state is StationState.ON_AIR

    finally:
        _restore_fakes(
            original_player,
            original_timer,
        )


def test_off_air_station_selection_does_not_start_overlay() -> None:
    """
    When the radio is OFF, station selection happens
    immediately and no switch overlay is created.
    """
    original_player, original_timer = _install_fakes()

    try:
        engine = _make_engine()

        assert engine.state is StationState.OFF
        assert (
            engine.current_station.name
            == "Station A"
        )

        engine.next_station()

        assert (
            engine.current_station.name
            == "Station B"
        )

        assert engine.pending_station is None

        assert FakeSwitchTimer.instances == []

    finally:
        _restore_fakes(
            original_player,
            original_timer,
        )


def test_stop_cancels_pending_switch() -> None:
    """
    Stopping the radio during a switch must cancel
    the timer and stop the player.
    """
    original_player, original_timer = _install_fakes()

    try:
        engine = _make_engine()
        engine.play()

        player = engine.player

        engine.next_station()

        assert engine.pending_station is not None
        assert (
            engine.pending_station.name
            == "Station B"
        )

        assert engine.is_switching

        timer = FakeSwitchTimer.instances[0]

        engine.stop()

        assert engine.state is StationState.OFF
        assert engine.pending_station is None

        assert timer.cancel_calls == 1
        assert player.stop_called is True

    finally:
        _restore_fakes(
            original_player,
            original_timer,
        )


def test_switch_timer_is_reused() -> None:
    """
    Repeated switching must reuse the same SwitchTimer
    instead of creating a new timer for every input.
    """
    original_player, original_timer = _install_fakes()

    try:
        engine = _make_engine()
        engine.play()

        engine.next_station()
        engine.next_station()
        engine.previous_station()
        engine.next_station()

        assert len(
            FakeSwitchTimer.instances
        ) == 1

        timer = FakeSwitchTimer.instances[0]

        assert timer.start_calls == 4

    finally:
        _restore_fakes(
            original_player,
            original_timer,
        )


def test_switch_overlay_starts_only_once() -> None:
    """
    Even after many inputs during one switch sequence,
    switch_noise.ogg must only be requested once.
    """
    original_player, original_timer = _install_fakes()

    try:
        engine = _make_engine()
        engine.play()

        player = engine.player

        for _ in range(20):
            engine.next_station()

        for _ in range(10):
            engine.previous_station()

        assert len(
            player.overlay_calls
        ) == 1

        assert (
            player.overlay_calls[0][0]
            == engine_module.SWITCH_NOISE_PATH
        )

        assert (
            player.overlay_calls[0][1]
            is True
        )

    finally:
        _restore_fakes(
            original_player,
            original_timer,
        )


def run_all_tests() -> None:
    """Run all radio switching tests."""
    tests = [
        test_single_switch,
        test_repeated_switches_keep_one_overlay,
        test_last_selected_station_wins,
        test_switch_back_to_original_station,
        test_overlay_is_looping,
        test_overlay_stops_after_switch,
        test_off_air_station_selection_does_not_start_overlay,
        test_stop_cancels_pending_switch,
        test_switch_timer_is_reused,
        test_switch_overlay_starts_only_once,
    ]

    for test in tests:
        test()

        print(
            f"{test.__name__}: passed"
        )


if __name__ == "__main__":
    run_all_tests()

    print()
    print("Radio switching tests passed.")
