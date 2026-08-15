from __future__ import annotations

import time
from pathlib import Path

from radio.engine import RadioEngine
from radio.library.gen1 import Gen1Loader
from radio.model.station_state import StationState


TEST_ROOT = Path("test_data/GTA IV")

SWITCH_DELAY_SECONDS = 1.5
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
                "Station did not finish switching in time"
            )

        time.sleep(0.05)

    assert engine.state is StationState.ON_AIR


def main() -> None:
    engine = create_engine()

    print("Testing rapid multiple station switching...")

    initial_station = engine.current_station

    print(f"Initial station: {initial_station.name}")

    assert initial_station.name == "04_MASSIVEB"

    print()
    print("Starting playback...")

    engine.play()

    assert engine.state is StationState.ON_AIR

    print(f"State: {engine.state.value}")
    print(f"Station: {engine.current_station.name}")

    # ---------------------------------------------------------
    # 1. First switch:
    #
    # 04_MASSIVEB -> 12_THEBEAT
    # ---------------------------------------------------------

    time.sleep(5)
    print()
    print("1) next_station()")

    engine.next_station()

    assert engine.state is StationState.SWITCHING
    assert engine.current_station.name == "04_MASSIVEB"
    assert engine.pending_station is not None
    assert engine.pending_station.name == "12_THEBEAT"

    print(f"State: {engine.state.value}")
    print(f"Current station: {engine.current_station.name}")
    print(f"Pending station: {engine.pending_station.name}")

    # ---------------------------------------------------------
    # 2. Wait only 0.5 sec and switch again:
    #
    # 12_THEBEAT -> 13_RAMJAM
    #
    # The switch must NOT restart from MASSIVEB.
    # ---------------------------------------------------------

    print()
    print("Waiting 0.5 seconds...")
    time.sleep(0.5)

    print("2) next_station()")

    engine.next_station()

    assert engine.state is StationState.SWITCHING
    assert engine.current_station.name == "04_MASSIVEB"
    assert engine.pending_station is not None
    assert engine.pending_station.name == "13_RAMJAM"

    print(f"State: {engine.state.value}")
    print(f"Current station: {engine.current_station.name}")
    print(f"Pending station: {engine.pending_station.name}")

    # ---------------------------------------------------------
    # 3. Immediately switch again:
    #
    # 13_RAMJAM -> 18_ELECTROCHOC
    # ---------------------------------------------------------

    print()
    print("3) next_station() immediately")

    engine.next_station()

    assert engine.state is StationState.SWITCHING
    assert engine.current_station.name == "04_MASSIVEB"
    assert engine.pending_station is not None
    assert engine.pending_station.name == "18_ELECTROCHOC"

    print(f"State: {engine.state.value}")
    print(f"Current station: {engine.current_station.name}")
    print(f"Pending station: {engine.pending_station.name}")

    # ---------------------------------------------------------
    # The timer must be reset by the latest request.
    #
    # We therefore wait for the final switch.
    # ---------------------------------------------------------

    print()
    print("Waiting for final station switch...")

    wait_for_on_air(engine)

    print(f"State after switch: {engine.state.value}")
    print(f"Final station: {engine.current_station.name}")

    # ---------------------------------------------------------
    # Final expectation:
    #
    # 04_MASSIVEB
    #      ↓ next
    # 12_THEBEAT
    #      ↓ next
    # 13_RAMJAM
    #      ↓ next
    # 18_ELECTROCHOC
    # ---------------------------------------------------------

    assert engine.current_station.name == "18_ELECTROCHOC"

    assert engine.pending_station is None
    assert engine.state is StationState.ON_AIR

    print()
    print(
        "Rapid switching sequence:"
    )
    print(
        "04_MASSIVEB -> "
        "12_THEBEAT -> "
        "13_RAMJAM -> "
        "18_ELECTROCHOC"
    )

    print()
    print(
        "Final station is 18_ELECTROCHOC."
    )

    print()
    print(
        "Rapid multiple station switching test passed."
    )
    time.sleep(5)

    engine.stop()

    assert engine.state is StationState.OFF


if __name__ == "__main__":
    main()
