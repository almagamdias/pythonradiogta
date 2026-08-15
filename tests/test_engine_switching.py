from __future__ import annotations

import time
from pathlib import Path

from radio.engine import RadioEngine
from radio.library.gen1 import Gen1Loader
from radio.model.station_library import StationLibrary
from radio.model.station_state import StationState


TEST_ROOT = Path("test_data/GTA IV")


def create_engine() -> RadioEngine:
    library = Gen1Loader().load(TEST_ROOT)
    assert isinstance(library, StationLibrary)
    return RadioEngine(library)


def wait_for_on_air(
    engine: RadioEngine,
    timeout: float = 2.5,
) -> None:
    deadline = time.monotonic() + timeout

    while engine.state is StationState.SWITCHING:
        if time.monotonic() >= deadline:
            break

        time.sleep(0.05)

    assert engine.state is StationState.ON_AIR


def main() -> None:
    engine = create_engine()

    print(
        f"Playing: {engine.current_station.name}"
    )
    print(
        f"Song:    {engine.current_song.title}"
    )

    engine.play()

    assert engine.state is StationState.ON_AIR

    print("Playing first station for 2 seconds...")
    time.sleep(2)

    initial_station = engine.current_station

    print()
    print("Requesting next station...")

    engine.next_station()

    assert engine.state is StationState.SWITCHING

    print(
        f"State immediately: {engine.state.value}"
    )
    print(
        f"Current station:   {engine.current_station.name}"
    )

    time.sleep(0.5)

    assert engine.state is StationState.SWITCHING
    assert engine.current_station is initial_station

    print()
    print("Waiting for station switch...")

    wait_for_on_air(engine)

    assert engine.current_station is not initial_station

    print(
        f"State after switch: {engine.state.value}"
    )
    print(
        f"New station:        {engine.current_station.name}"
    )
    print(
        f"Song:               {engine.current_song.title}"
    )

    print()
    print("Playing new station for 3 seconds...")
    time.sleep(3)

    engine.stop()

    assert engine.state is StationState.OFF

    print("Station switching playback test finished.")


if __name__ == "__main__":
    main()
