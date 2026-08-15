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
        f"Initial station: "
        f"{engine.current_station.name}"
    )

    engine.play()

    assert engine.state is StationState.ON_AIR

    print("Playing for 2 seconds...")
    time.sleep(2)

    player = engine.player

    overlay_before = player.overlay_count

    print()
    print("Requesting next station...")

    engine.next_station()

    assert engine.state is StationState.SWITCHING

    print(
        f"State: {engine.state.value}"
    )

    print(
        f"Station: "
        f"{engine.current_station.name}"
    )

    overlay_after = player.overlay_count

    print()
    print(
        f"Overlay count before: "
        f"{overlay_before}"
    )

    print(
        f"Overlay count after:  "
        f"{overlay_after}"
    )

    assert (
        overlay_after
        == overlay_before + 1
    )

    print(
        "Overlay request registered."
    )

    print()
    print("Waiting for station switch...")

    wait_for_on_air(engine)

    assert engine.state is StationState.ON_AIR
    assert engine.current_station.name == "12_THEBEAT"

    print(
        f"State after switch: "
        f"{engine.state.value}"
    )

    print(
        f"Station after switch: "
        f"{engine.current_station.name}"
    )

    # The same player remains alive.
    assert engine.player is player

    # No second overlay was created during completion.
    assert player.overlay_count == overlay_after

    print()
    print(
        "Old overlay cancelled during "
        "station change."
    )

    print()
    print(
        "Engine switching overlay test passed."
    )

    engine.stop()

    assert engine.state is StationState.OFF


if __name__ == "__main__":
    main()
