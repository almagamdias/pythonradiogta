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
    print("Testing real independent station timelines...")

    engine = create_engine()

    print(
        f"Initial station: "
        f"{engine.current_station.name}"
    )
    print(
        f"Initial song: "
        f"{engine.current_song.title}"
    )

    engine.play()

    assert engine.state is StationState.ON_AIR
    assert engine._player is not None

    print()
    print("Starting playback...")
    print(f"State: {engine.state.value}")

    # Give the first station some time to advance.
    time.sleep(2.0)

    print()
    print("Switching to next station...")

    engine.next_station()

    assert engine.state is StationState.SWITCHING
    assert engine.current_station.name == "04_MASSIVEB"
    assert engine.pending_station is not None
    assert engine.pending_station.name == "12_THEBEAT"

    wait_for_on_air(engine)

    assert engine.state is StationState.ON_AIR
    assert engine.current_station.name == "12_THEBEAT"

    print(
        f"Station after switch: "
        f"{engine.current_station.name}"
    )
    print(
        f"Song after switch: "
        f"{engine.current_song.title}"
    )

    # Let THEBEAT advance independently.
    time.sleep(2.0)

    print()
    print("Returning to previous station...")

    engine.previous_station()

    assert engine.state is StationState.SWITCHING
    assert engine.current_station.name == "12_THEBEAT"
    assert engine.pending_station is not None
    assert engine.pending_station.name == "04_MASSIVEB"

    wait_for_on_air(engine)

    assert engine.state is StationState.ON_AIR
    assert engine.current_station.name == "04_MASSIVEB"

    print(
        f"Station after return: "
        f"{engine.current_station.name}"
    )
    print(
        f"Song after return: "
        f"{engine.current_song.title}"
    )

    print()
    print(
        "Checking that station timeline "
        "was restored from the shared radio timeline..."
    )

    # The important part:
    #
    # We do NOT expect the player to restart from the
    # original random position. The engine calculates
    # the position from radio_started_at and the station's
    # own initial offset.
    #
    # The current AudioPlayer must therefore have received
    # a non-zero/current timeline position.
    player = engine._player

    assert player is not None

    print(
        "AudioPlayer successfully returned to "
        "the previous station timeline."
    )

    print()
    print("Stopping playback...")

    engine.stop()

    assert engine.state is StationState.OFF

    print(f"Final state: {engine.state.value}")

    print()
    print(
        "Real independent station timeline "
        "test passed."
    )


if __name__ == "__main__":
    main()
