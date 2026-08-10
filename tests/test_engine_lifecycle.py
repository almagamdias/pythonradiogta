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

    print(f"Initial state: {engine.state.value}")

    assert engine.state is StationState.OFF

    print()
    print("Starting playback...")

    engine.play()

    print(f"State after play: {engine.state.value}")

    assert engine.state is StationState.ON_AIR
    assert engine._player is not None

    first_player = engine._player

    print("Calling play() again...")

    engine.play()

    print(f"State after second play: {engine.state.value}")

    assert engine.state is StationState.ON_AIR
    assert engine._player is first_player

    print("Second play() did not create another player.")

    time.sleep(2)

    print()
    print("Stopping playback...")

    engine.stop()

    print(f"State after stop: {engine.state.value}")

    assert engine._player is None
    assert engine.state is StationState.OFF

    print("Calling stop() again...")

    engine.stop()

    assert engine._player is None
    assert engine.state is StationState.OFF

    print("Second stop() is safe.")

    print()
    print("Starting playback again...")

    engine.play()

    print(f"State after restart: {engine.state.value}")

    assert engine.state is StationState.ON_AIR
    assert engine._player is not None

    second_player = engine._player

    assert second_player is not first_player

    print("New AudioPlayer created after restart.")

    time.sleep(2)

    engine.stop()

    print(f"Final state: {engine.state.value}")

    assert engine._player is None
    assert engine.state is StationState.OFF

    print()
    print("Engine lifecycle test passed.")


if __name__ == "__main__":
    main()
