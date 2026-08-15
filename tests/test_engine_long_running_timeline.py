from __future__ import annotations

import time
from pathlib import Path

from radio.engine import RadioEngine
from radio.library.gen1 import Gen1Loader
from radio.model.station_state import StationState


TEST_ROOT = Path("test_data/GTA IV")
WAIT_SECONDS = 5.0
SWITCH_WAIT_SECONDS = 2.0


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


def station_position(
    engine: RadioEngine,
    station_name: str,
) -> int:
    for index, station in enumerate(engine.stations):
        if station.name == station_name:
            return engine._station_position(index)

    raise AssertionError(
        f"Station not found: {station_name}"
    )


def main() -> None:
    print("Testing long-running independent station timelines...")

    engine = create_engine()

    assert len(engine.stations) >= 3

    print(
        f"Stations available: {len(engine.stations)}"
    )
    print(
        f"Initial station: {engine.current_station.name}"
    )

    print()
    print("Starting playback...")

    engine.play()

    assert engine.state is StationState.ON_AIR

    initial_station = engine.current_station.name

    print(f"State: {engine.state.value}")
    print(f"Station: {initial_station}")

    print()
    print(
        f"Playing initial station for "
        f"{WAIT_SECONDS:.0f} seconds..."
    )

    time.sleep(WAIT_SECONDS)

    initial_position = station_position(
        engine,
        initial_station,
    )

    print(
        f"Position of {initial_station}: "
        f"{initial_position} ms"
    )

    assert initial_position > 0

    print()
    print("Switching to next station...")

    engine.next_station()

    assert engine.state is StationState.SWITCHING

    wait_for_on_air(engine)

    second_station = engine.current_station.name

    print(
        f"State after switch: {engine.state.value}"
    )
    print(f"Station: {second_station}")

    assert second_station != initial_station

    print()
    print(
        f"Playing {second_station} for "
        f"{WAIT_SECONDS:.0f} seconds..."
    )

    time.sleep(WAIT_SECONDS)

    second_position = station_position(
        engine,
        second_station,
    )

    print(
        f"Position of {second_station}: "
        f"{second_position} ms"
    )

    assert second_position > 0

    print()
    print(
        "Returning to the initial station..."
    )

    engine.previous_station()

    assert engine.state is StationState.SWITCHING

    wait_for_on_air(engine)

    assert engine.current_station.name == initial_station

    restored_initial_position = station_position(
        engine,
        initial_station,
    )

    print(
        f"Returned station: "
        f"{engine.current_station.name}"
    )
    print(
        f"Restored timeline position: "
        f"{restored_initial_position} ms"
    )

    print()
    print(
        f"Playing restored {initial_station} for "
        f"{WAIT_SECONDS:.0f} seconds..."
    )

    position_before_wait = restored_initial_position

    time.sleep(WAIT_SECONDS)

    position_after_wait = station_position(
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

    print()
    print("Switching through the second station to the third station...")

    # 04_MASSIVEB -> 12_THEBEAT
    engine.next_station()
    wait_for_on_air(engine)

    assert engine.current_station.name == second_station

    print(
        f"Intermediate station: "
        f"{engine.current_station.name}"
    )

    # 12_THEBEAT -> 13_RAMJAM
    engine.next_station()
    wait_for_on_air(engine)

    third_station = engine.current_station.name

    print(f"Third station: {third_station}")

    assert third_station not in {
        initial_station,
        second_station,
    }

    print()
    print(
        f"Playing {third_station} for "
        f"{WAIT_SECONDS:.0f} seconds..."
    )

    time.sleep(WAIT_SECONDS)

    third_position = station_position(
        engine,
        third_station,
    )

    print(
        f"Position of {third_station}: "
        f"{third_position} ms"
    )

    assert third_position > 0

    print()
    print("Returning to the second station...")

    engine.previous_station()
    wait_for_on_air(engine)

    assert engine.current_station.name == second_station

    second_restored_position = station_position(
        engine,
        second_station,
    )

    print(
        f"Returned station: {second_station}"
    )
    print(
        f"Restored timeline position: "
        f"{second_restored_position} ms"
    )

    assert second_restored_position != 0

    time.sleep(5)

    print()
    print("Stopping playback...")

    engine.stop()

    assert engine.state is StationState.OFF

    print(f"Final state: {engine.state.value}")

    print()
    print(
        "Long-running independent station "
        "timeline test passed."
    )


if __name__ == "__main__":
    main()
