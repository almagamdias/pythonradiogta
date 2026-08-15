from __future__ import annotations

import time
from pathlib import Path

from radio.audio.player import AudioPlayer
from radio.engine import RadioEngine
from radio.library.gen1 import Gen1Loader
from radio.model.station_state import StationState


TEST_ROOT = Path("test_data/GTA IV")

SWITCH_WAIT_SECONDS = 1.8
EOF_START_MARGIN_MS = 3_000
EOF_PLAY_SECONDS = 5.0
STATION_PLAY_SECONDS = 5.0


def create_engine() -> RadioEngine:
    library = Gen1Loader().load(TEST_ROOT)
    return RadioEngine(library)


def wait_for_on_air(
    engine: RadioEngine,
    timeout: float = SWITCH_WAIT_SECONDS,
) -> None:
    deadline = time.monotonic() + timeout

    while engine.state is StationState.SWITCHING:
        if time.monotonic() >= deadline:
            raise AssertionError(
                "Station did not switch within the expected time"
            )

        time.sleep(0.05)

    assert engine.state is StationState.ON_AIR


def get_position(
    engine: RadioEngine,
    station_name: str,
) -> int:
    for index, station in enumerate(engine.stations):
        if station.name == station_name:
            return engine._station_position(index)

    raise AssertionError(
        f"Station not found: {station_name}"
    )


def find_station_index(
    engine: RadioEngine,
    station_name: str,
) -> int:
    for index, station in enumerate(engine.stations):
        if station.name == station_name:
            return index

    raise AssertionError(
        f"Station not found: {station_name}"
    )


def test_real_player_eof_loop() -> None:
    print()
    print("=== Real AudioPlayer EOF boundary test ===")

    engine = create_engine()

    station = engine.stations[0]
    song = station.songs[0]

    assert song.duration > EOF_START_MARGIN_MS

    start_position = (
        song.duration - EOF_START_MARGIN_MS
    )

    print(f"Station: {station.name}")
    print(f"Song:    {song.title}")
    print(f"Duration: {song.duration} ms")
    print(
        f"Starting position: "
        f"{start_position} ms"
    )

    player = AudioPlayer(
        song.path,
        start_position_ms=start_position,
    )

    player.volume = 1.0

    print()
    print("Starting real AudioPlayer...")

    player.play()

    try:
        print(
            f"Playing for {EOF_PLAY_SECONDS:.1f} seconds "
            "to cross EOF..."
        )

        time.sleep(EOF_PLAY_SECONDS)

        assert player._device is not None

        print("AudioPlayer remained alive after EOF.")
        print("Real EOF loop completed successfully.")

    finally:
        player.stop()


def test_engine_eof_switch_boundaries() -> None:
    print()
    print(
        "=== Engine EOF + station switching "
        "boundary test ==="
    )

    engine = create_engine()

    print(
        f"Stations available: "
        f"{len(engine.stations)}"
    )

    initial_station = engine.current_station.name

    print(
        f"Initial station: {initial_station}"
    )

    engine.play()

    assert engine.state is StationState.ON_AIR

    print()
    print("Starting playback...")
    print(f"State: {engine.state.value}")

    print()
    print(
        f"Playing {initial_station} for "
        f"{STATION_PLAY_SECONDS:.1f} seconds..."
    )

    time.sleep(STATION_PLAY_SECONDS)

    initial_position_before_switch = (
        get_position(
            engine,
            initial_station,
        )
    )

    print(
        f"Position before switch: "
        f"{initial_position_before_switch} ms"
    )

    # ---------------------------------------------------------
    # Switch to THEBEAT
    # ---------------------------------------------------------

    engine.next_station()

    assert engine.state is StationState.SWITCHING

    wait_for_on_air(engine)

    assert engine.current_station.name == "12_THEBEAT"

    print()
    print("Switched to:")
    print(f"Station: {engine.current_station.name}")
    print(f"State:   {engine.state.value}")

    print(
        f"Playing {engine.current_station.name} "
        f"for {STATION_PLAY_SECONDS:.1f} seconds..."
    )

    time.sleep(STATION_PLAY_SECONDS)

    thebeat_position = get_position(
        engine,
        "12_THEBEAT",
    )

    print(
        f"THEBEAT position: "
        f"{thebeat_position} ms"
    )

    # ---------------------------------------------------------
    # Return to MASSIVEB
    # ---------------------------------------------------------

    print()
    print(
        f"Returning to {initial_station}..."
    )

    engine.previous_station()

    assert engine.state is StationState.SWITCHING

    wait_for_on_air(engine)

    assert engine.current_station.name == initial_station

    restored_position = get_position(
        engine,
        initial_station,
    )

    print(
        f"Returned station: "
        f"{engine.current_station.name}"
    )

    print(
        f"Restored position: "
        f"{restored_position} ms"
    )

    assert restored_position > (
        initial_position_before_switch
    )

    print(
        "Initial station timeline continued "
        "independently."
    )

    # ---------------------------------------------------------
    # Let MASSIVEB continue, then switch to RAMJAM.
    # ---------------------------------------------------------

    print()
    print(
        f"Playing {initial_station} for "
        f"{STATION_PLAY_SECONDS:.1f} seconds..."
    )

    position_before_wait = get_position(
        engine,
        initial_station,
    )

    time.sleep(STATION_PLAY_SECONDS)

    position_after_wait = get_position(
        engine,
        initial_station,
    )

    print(
        f"Position before wait: "
        f"{position_before_wait} ms"
    )

    print(
        f"Position after wait:  "
        f"{position_after_wait} ms"
    )

    assert position_after_wait != position_before_wait

    print(
        "Timeline advanced while station was "
        "audible."
    )

    # ---------------------------------------------------------
    # Move through THEBEAT to RAMJAM.
    # ---------------------------------------------------------

    print()
    print(
        "Switching through THEBEAT to RAMJAM..."
    )

    engine.next_station()

    wait_for_on_air(engine)

    assert engine.current_station.name == "12_THEBEAT"

    print(
        f"Intermediate station: "
        f"{engine.current_station.name}"
    )

    engine.next_station()

    wait_for_on_air(engine)

    assert engine.current_station.name == "13_RAMJAM"

    print(
        f"Third station: "
        f"{engine.current_station.name}"
    )

    print(
        f"Playing {engine.current_station.name} "
        f"for {STATION_PLAY_SECONDS:.1f} seconds..."
    )

    time.sleep(STATION_PLAY_SECONDS)

    ramjam_position = get_position(
        engine,
        "13_RAMJAM",
    )

    print(
        f"RAMJAM position: "
        f"{ramjam_position} ms"
    )

    assert ramjam_position > 0

    # ---------------------------------------------------------
    # Return to THEBEAT and verify its timeline.
    # ---------------------------------------------------------

    print()
    print("Returning to THEBEAT...")

    engine.previous_station()

    wait_for_on_air(engine)

    assert engine.current_station.name == "12_THEBEAT"

    restored_thebeat_position = get_position(
        engine,
        "12_THEBEAT",
    )

    print(
        f"Returned station: "
        f"{engine.current_station.name}"
    )

    print(
        f"Restored THEBEAT position: "
        f"{restored_thebeat_position} ms"
    )

    assert (
        restored_thebeat_position
        > thebeat_position
    )

    print(
        "THEBEAT timeline continued "
        "independently."
    )

    # ---------------------------------------------------------
    # Final state.
    # ---------------------------------------------------------

    print()
    print("Stopping playback...")

    engine.stop()

    assert engine.state is StationState.OFF

    print(
        f"Final state: {engine.state.value}"
    )


def main() -> None:
    print(
        "Testing real EOF boundaries during "
        "long station switching..."
    )

    test_real_player_eof_loop()
    test_engine_eof_switch_boundaries()

    print()
    print(
        "Real EOF + switching boundary test passed."
    )


if __name__ == "__main__":
    main()
