from __future__ import annotations

import time
from pathlib import Path

from radio.engine import RadioEngine
from radio.library.gen1 import Gen1Loader
from radio.model.station_state import StationState


TEST_ROOT = Path("test_data/GTA IV")
SWITCH_WAIT_SECONDS = 2.0


def create_engine() -> RadioEngine:
    library = Gen1Loader().load(TEST_ROOT)
    return RadioEngine(library)


def wait_for_on_air(engine: RadioEngine) -> None:
    deadline = time.monotonic() + SWITCH_WAIT_SECONDS

    while time.monotonic() < deadline:
        if engine.state is StationState.ON_AIR:
            return

        time.sleep(0.05)

    raise AssertionError(
        "Station did not finish switching in time"
    )


def main() -> None:
    print("Testing rapid mixed station switching...")

    engine = create_engine()

    initial = engine.current_station.name

    print(f"Initial station: {initial}")

    engine.play()

    assert engine.state is StationState.ON_AIR

    print()
    print("Starting playback...")
    print(f"State: {engine.state.value}")
    print(f"Station: {engine.current_station.name}")

    time.sleep(5)

    # 04_MASSIVEB -> 12_THEBEAT
    print()
    print("1) next_station()")

    engine.next_station()

    assert engine.state is StationState.SWITCHING
    assert engine.current_station.name == "04_MASSIVEB"
    assert engine.pending_station is not None
    assert engine.pending_station.name == "12_THEBEAT"

    print(f"Current:  {engine.current_station.name}")
    print(f"Pending:  {engine.pending_station.name}")

    # 12_THEBEAT -> 13_RAMJAM
    time.sleep(0.5)

    print()
    print("2) next_station() after 0.5 seconds")

    engine.next_station()

    assert engine.state is StationState.SWITCHING
    assert engine.current_station.name == "04_MASSIVEB"
    assert engine.pending_station is not None
    assert engine.pending_station.name == "13_RAMJAM"

    print(f"Current:  {engine.current_station.name}")
    print(f"Pending:  {engine.pending_station.name}")

    # 13_RAMJAM -> 12_THEBEAT
    print()
    print("3) previous_station() immediately")

    engine.previous_station()

    assert engine.state is StationState.SWITCHING
    assert engine.current_station.name == "04_MASSIVEB"
    assert engine.pending_station is not None
    assert engine.pending_station.name == "12_THEBEAT"

    print(f"Current:  {engine.current_station.name}")
    print(f"Pending:  {engine.pending_station.name}")

    # 12_THEBEAT -> 13_RAMJAM
    print()
    print("4) next_station() immediately")

    engine.next_station()

    assert engine.state is StationState.SWITCHING
    assert engine.current_station.name == "04_MASSIVEB"
    assert engine.pending_station is not None
    assert engine.pending_station.name == "13_RAMJAM"

    print(f"Current:  {engine.current_station.name}")
    print(f"Pending:  {engine.pending_station.name}")

    # 13_RAMJAM -> 18_ELECTROCHOC
    print()
    print("5) next_station() immediately")

    engine.next_station()

    assert engine.state is StationState.SWITCHING
    assert engine.current_station.name == "04_MASSIVEB"
    assert engine.pending_station is not None
    assert engine.pending_station.name == "18_ELECTROCHOC"

    print(f"Current:  {engine.current_station.name}")
    print(f"Pending:  {engine.pending_station.name}")

    print()
    print("Waiting for final station switch...")

    wait_for_on_air(engine)

    assert engine.state is StationState.ON_AIR
    assert engine.current_station.name == "18_ELECTROCHOC"
    assert engine.pending_station is None

    print(f"State after switch: {engine.state.value}")
    print(f"Final station:      {engine.current_station.name}")
    print()
    print(
        "Mixed switching sequence:"
    )
    print(
        "04_MASSIVEB"
        " -> 12_THEBEAT"
        " -> 13_RAMJAM"
        " -> 12_THEBEAT"
        " -> 13_RAMJAM"
        " -> 18_ELECTROCHOC"
    )

    print()
    print("Final station is 18_ELECTROCHOC.")
    time.sleep(5)

    engine.stop()

    assert engine.state is StationState.OFF

    print()
    print("Rapid mixed station switching test passed.")


if __name__ == "__main__":
    main()
