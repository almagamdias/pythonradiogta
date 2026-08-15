from __future__ import annotations

import random
import time
from pathlib import Path

from radio.engine import RadioEngine
from radio.library.gen1 import Gen1Loader
from radio.model.station_state import StationState


TEST_ROOT = Path("test_data/GTA IV")

SWITCH_WAIT_SECONDS = 2.0

# Количество операций переключения.
OPERATIONS = 100

# Максимальная пауза между операциями.
MAX_DELAY_SECONDS = 0.05


def create_engine() -> RadioEngine:
    library = Gen1Loader().load(TEST_ROOT)
    return RadioEngine(library)


def wait_for_switch(engine: RadioEngine) -> None:
    deadline = time.monotonic() + SWITCH_WAIT_SECONDS

    while time.monotonic() < deadline:
        if engine.state is StationState.ON_AIR:
            return

        time.sleep(0.01)

    raise AssertionError(
        "RadioEngine did not return to ON_AIR "
        "within the expected time."
    )


def main() -> None:
    print("Testing RadioEngine switching stress...")

    random.seed(42)

    engine = create_engine()

    stations = list(engine.stations)

    assert len(stations) == 5

    initial_index = engine._station_index
    expected_index = initial_index

    print(
        f"Stations: {len(stations)}"
    )
    print(
        f"Initial station: "
        f"{engine.current_station.name}"
    )

    print()
    print("Starting playback...")

    engine.play()

    assert engine.state is StationState.ON_AIR

    print(
        f"State: {engine.state.value}"
    )

    player = engine.player

    initial_overlay_count = player.overlay_count

    print(
        f"Initial overlay count: "
        f"{initial_overlay_count}"
    )

    print()
    print(
        f"Running {OPERATIONS} rapid switching operations..."
    )

    next_count = 0
    previous_count = 0
    time.sleep(5)

    for operation in range(1, OPERATIONS + 1):
        if random.choice((True, False)):
            engine.next_station()

            expected_index = (
                expected_index + 1
            ) % len(stations)

            next_count += 1
            operation_name = "next"
        else:
            engine.previous_station()

            expected_index = (
                expected_index - 1
            ) % len(stations)

            previous_count += 1
            operation_name = "previous"

        # During switching the audible/current station must remain
        # the actual station until the timer completes.
        assert engine.state is StationState.SWITCHING

        assert (
            engine._pending_station_index
            == expected_index
        )

        assert (
            engine.pending_station
            is stations[expected_index]
        )

        # The currently audible station must not change yet.
        assert (
            engine._station_index
            == initial_index
        )

        if operation <= 10 or operation % 10 == 0:
            print(
                f"{operation:3d}) "
                f"{operation_name:8s} -> "
                f"pending: "
                f"{engine.pending_station.name}"
            )

        # Tiny delay to make the test closer to real user input.
        time.sleep(
            random.uniform(
                0.0,
                MAX_DELAY_SECONDS,
            )
        )

    print()
    print(
        f"next_station():     {next_count}"
    )
    print(
        f"previous_station(): {previous_count}"
    )

    expected_station = stations[expected_index]

    print()
    print(
        "Expected final station:"
        f" {expected_station.name}"
    )
    print(
        "Pending station:"
        f" {engine.pending_station.name}"
    )

    assert (
        engine.pending_station
        is expected_station
    )

    print()
    print("Checking overlay count...")

    overlay_count_after = player.overlay_count

    print(
        f"Overlay count before: "
        f"{initial_overlay_count}"
    )
    print(
        f"Overlay count after:  "
        f"{overlay_count_after}"
    )

    # All rapid switching operations belong to one switching period.
    # Therefore only the first operation may request the overlay.
    assert (
        overlay_count_after
        == initial_overlay_count + 1
    )

    print(
        "Only one switch overlay was requested."
    )

    print()
    print("Waiting for final switch...")

    wait_for_switch(engine)

    assert engine.state is StationState.ON_AIR

    assert (
        engine._station_index
        == expected_index
    )

    assert (
        engine.current_station
        is expected_station
    )

    print(
        f"State after switch: "
        f"{engine.state.value}"
    )
    print(
        f"Final station: "
        f"{engine.current_station.name}"
    )

    print()
    print(
        "Checking that pending state is cleared..."
    )

    assert engine.pending_station is None
    assert engine._pending_station_index is None

    print(
        "Pending station cleared."
    )
    time.sleep(5)

    print()
    print("Stopping playback...")

    engine.stop()

    assert engine.state is StationState.OFF

    print(
        f"Final state: {engine.state.value}"
    )

    print()
    print(
        "RadioEngine switching stress test passed."
    )


if __name__ == "__main__":
    main()
