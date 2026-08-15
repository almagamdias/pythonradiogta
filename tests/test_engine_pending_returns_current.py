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


def wait_for_on_air(
    engine: RadioEngine,
    timeout: float = SWITCH_WAIT_SECONDS,
) -> None:
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        if engine.state is StationState.ON_AIR:
            return

        time.sleep(0.05)

    raise AssertionError(
        "Engine did not return to ON_AIR"
    )


def main() -> None:
    print(
        "Testing pending station returning to current station..."
    )

    engine = create_engine()

    initial_station = engine.current_station

    print(
        f"Initial station: {initial_station.name}"
    )

    engine.play()

    assert engine.state is StationState.ON_AIR
    assert engine._player is not None

    player = engine._player
    initial_overlay_count = player.overlay_count

    time.sleep(5)

    # ---------------------------------------------------------
    # next -> next -> previous -> previous
    # ---------------------------------------------------------

    print()
    print("1) next_station()")

    engine.next_station()

    assert engine.state is StationState.SWITCHING
    assert engine.pending_station is not None

    print(
        f"Current:  {engine.current_station.name}"
    )
    print(
        f"Pending:  {engine.pending_station.name}"
    )

    print()
    print("2) next_station()")

    engine.next_station()

    assert engine.state is StationState.SWITCHING
    assert engine.pending_station is not None

    print(
        f"Current:  {engine.current_station.name}"
    )
    print(
        f"Pending:  {engine.pending_station.name}"
    )

    print()
    print("3) previous_station()")

    engine.previous_station()

    assert engine.state is StationState.SWITCHING
    assert engine.pending_station is not None

    print(
        f"Current:  {engine.current_station.name}"
    )
    print(
        f"Pending:  {engine.pending_station.name}"
    )

    print()
    print("4) previous_station()")

    engine.previous_station()

    print(
        f"Current:  {engine.current_station.name}"
    )
    print(
        f"Pending:  "
        f"{engine.pending_station.name if engine.pending_station else None}"
    )

    # Конечный pending должен совпасть с current.
    assert engine.current_station is initial_station

    # ---------------------------------------------------------
    # Ждём окончания первоначального switch timer.
    # Никакого фактического переключения произойти не должно.
    # ---------------------------------------------------------

    print()
    print(
        "Waiting for the pending switch timer..."
    )

    time.sleep(2.0)

    assert engine.state is StationState.ON_AIR
    assert engine.current_station is initial_station
    assert engine.pending_station is None

    print(
        "No station change occurred."
    )

    print(
        f"Final station: {engine.current_station.name}"
    )
    print(
        f"Final state:   {engine.state.value}"
    )

    # ---------------------------------------------------------
    # Overlay должен быть только один.
    # ---------------------------------------------------------

    print()
    print("Checking overlay count...")

    final_overlay_count = player.overlay_count

    print(
        f"Initial overlay count: {initial_overlay_count}"
    )
    print(
        f"Final overlay count:   {final_overlay_count}"
    )

    assert (
        final_overlay_count
        == initial_overlay_count + 1
    )

    print(
        "No additional overlay was requested."
    )

    # ---------------------------------------------------------
    # Убедимся, что после истечения timer ничего не произошло.
    # ---------------------------------------------------------

    time.sleep(0.5)

    assert engine.state is StationState.ON_AIR
    assert engine.current_station is initial_station
    assert engine.pending_station is None

    print(
        "No delayed station switch occurred."
    )
    time.sleep(5)

    engine.stop()

    assert engine.state is StationState.OFF

    print()
    print(
        "Pending return-to-current test passed."
    )


if __name__ == "__main__":
    main()
