from __future__ import annotations

import time
from pathlib import Path

from radio.engine import RadioEngine
from radio.library.gen1 import Gen1Loader
from radio.model.station_state import StationState


TEST_ROOT = Path("test_data/GTA IV")


def create_engine() -> RadioEngine:
    library = Gen1Loader().load(TEST_ROOT)
    return RadioEngine(library)


def main() -> None:
    print("Testing independent station timelines...")

    engine = create_engine()

    initial_station = engine.current_station

    print(f"Initial station: {initial_station.name}")
    print(f"Initial song: {engine.current_song.title}")

    assert engine.state is StationState.OFF

    print()
    print("Starting playback...")

    engine.play()

    assert engine.state is StationState.ON_AIR

    print(f"State: {engine.state.value}")

    # Let the radio timeline advance.
    time.sleep(1.0)

    print()
    print("Requesting next station...")

    engine.next_station()

    assert engine.state is StationState.SWITCHING

    print(f"State: {engine.state.value}")
    print(f"Current station: {engine.current_station.name}")

    # The station switch delay in the current engine is about 1.5 s.
    time.sleep(1.7)

    assert engine.state is StationState.ON_AIR

    second_station = engine.current_station

    print()
    print("After next station:")
    print(f"State: {engine.state.value}")
    print(f"Station: {second_station.name}")

    assert second_station is not initial_station

    print()
    print("Waiting while second station remains off the audible output...")

    time.sleep(1.0)

    print()
    print("Returning to previous station...")

    engine.previous_station()

    assert engine.state is StationState.SWITCHING

    print(f"State: {engine.state.value}")
    print(f"Current station: {engine.current_station.name}")

    time.sleep(1.7)

    assert engine.state is StationState.ON_AIR

    returned_station = engine.current_station

    print()
    print("After returning:")
    print(f"State: {engine.state.value}")
    print(f"Station: {returned_station.name}")

    assert returned_station is initial_station

    print()
    print("Stopping playback...")

    engine.stop()

    assert engine.state is StationState.OFF

    print(f"Final state: {engine.state.value}")

    print()
    print("Independent station timeline test passed.")


if __name__ == "__main__":
    main()
