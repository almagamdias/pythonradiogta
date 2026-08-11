from __future__ import annotations

import time
from pathlib import Path

from radio.engine import RadioEngine
from radio.library.gen1 import Gen1Loader
from radio.model.station_state import StationState


TEST_ROOT = Path("test_data/GTA IV")


def main() -> None:
    library = Gen1Loader().load(TEST_ROOT)
    engine = RadioEngine(library)

    # Move from the first station to the second station
    engine.next_station()

    initial_station = engine.current_station

    assert initial_station.name == "12_THEBEAT"

    print(f"Initial station: {initial_station.name}")

    engine.play()

    assert engine.state is StationState.ON_AIR
    assert engine.is_switching is False
    assert engine.pending_station is None

    print(f"State: {engine.state.value}")

    print()
    print("Requesting previous station...")

    engine.previous_station()

    assert engine.state is StationState.SWITCHING
    assert engine.is_switching is True
    assert engine.pending_station is not None
    assert engine.current_station is initial_station
    assert engine.pending_station.name == "04_MASSIVEB"

    print(f"State: {engine.state.value}")
    print(f"is_switching: {engine.is_switching}")
    print(f"Current station: {engine.current_station.name}")
    print(f"Pending station: {engine.pending_station.name}")

    time.sleep(1.3)

    assert engine.state is StationState.ON_AIR
    assert engine.is_switching is False
    assert engine.pending_station is None
    assert engine.current_station.name == "04_MASSIVEB"

    print()
    print(f"State after switch: {engine.state.value}")
    print(f"is_switching: {engine.is_switching}")
    print(f"Current station: {engine.current_station.name}")
    print(f"Pending station: {engine.pending_station}")

    engine.stop()

    assert engine.state is StationState.OFF
    assert engine.is_switching is False
    assert engine.pending_station is None

    print()
    print("Engine previous switch state test passed.")


if __name__ == "__main__":
    main()
