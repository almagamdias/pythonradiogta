from __future__ import annotations

import time
from pathlib import Path

from radio.engine import RadioEngine
from radio.model.song import Song
from radio.model.station import Station
from radio.model.station_library import StationLibrary
from radio.model.station_state import StationState


MASSIVEB_FILE = Path(
    "test_data/GTA IV/04_MASSIVEB/MASSIVEB_MIX.ogg"
)

THEBEAT_FILE = Path(
    "test_data/GTA IV/12_THEBEAT/THEBEAT_MIX.ogg"
)


def create_test_library() -> StationLibrary:
    massiveb = Station(
        name="04_MASSIVEB",
        songs=[
            Song(
                title="MASSIVEB_MIX",
                path=MASSIVEB_FILE,
                duration=1_958_361,
            )
        ],
    )

    thebeat = Station(
        name="12_THEBEAT",
        songs=[
            Song(
                title="THEBEAT_MIX",
                path=THEBEAT_FILE,
                duration=2_446_304,
            )
        ],
    )

    return StationLibrary(
        [
            massiveb,
            thebeat,
        ]
    )


def main() -> None:
    print("Testing RadioEngine volume with previous_station()...")

    engine = RadioEngine(create_test_library())

    # Start from THEBEAT.
    engine._station_index = 1

    print(f"Initial station: {engine.current_station.name}")
    print(f"Initial volume: {engine.volume}")

    assert engine.current_station.name == "12_THEBEAT"
    assert engine.volume == 1.0

    print()
    print("Setting volume to 0.35...")
    engine.volume = 0.35

    assert engine.volume == 0.35

    print(f"Engine volume: {engine.volume}")

    print()
    print("Starting playback...")
    engine.play()

    assert engine.state is StationState.ON_AIR
    assert engine._player is not None
    assert engine._player.volume == 0.35

    print(f"State: {engine.state.value}")
    print(f"Player volume: {engine._player.volume}")

    old_player = engine._player
    time.sleep(4)
    print()
    print("Requesting previous station...")
    engine.previous_station()

    assert engine.state is StationState.SWITCHING
    assert engine.current_station.name == "12_THEBEAT"
    assert engine._pending_station_index is not None

    print(f"State: {engine.state.value}")
    print(f"Current station: {engine.current_station.name}")

    print()
    print("Waiting for station switch...")

    time.sleep(1.7)

    assert engine.state is StationState.ON_AIR
    assert engine.current_station.name == "04_MASSIVEB"
    assert engine._pending_station_index is None
    assert engine._player is not None

    print(f"State after switch: {engine.state.value}")
    print(f"New station: {engine.current_station.name}")
    print(f"New player volume: {engine._player.volume}")

    assert engine._player is not old_player
    assert engine.volume == 0.35
    assert engine._player.volume == 0.35

    print()
    print("Testing volume change after previous station switch...")

    engine.volume = 0.6

    assert engine.volume == 0.6
    assert engine._player.volume == 0.6

    print(f"Engine volume: {engine.volume}")
    print(f"Player volume: {engine._player.volume}")

    time.sleep(4)
    print()
    print("Stopping playback...")
    engine.stop()

    assert engine.state is StationState.OFF

    print(f"Final state: {engine.state.value}")
    print()
    print("Engine previous switching volume test passed.")


if __name__ == "__main__":
    main()
