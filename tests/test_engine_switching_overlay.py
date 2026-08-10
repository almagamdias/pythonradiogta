from __future__ import annotations

import time
from pathlib import Path

from radio.engine import RadioEngine
from radio.library.gen1 import Gen1Loader


TEST_ROOT = Path("test_data/GTA IV")


def main() -> None:
    library = Gen1Loader().load(TEST_ROOT)
    engine = RadioEngine(library)

    print(f"Initial station: {engine.current_station.name}")

    engine.play()

    print("Playing for 2 seconds...")
    time.sleep(2)

    player = engine._player

    assert player is not None

    before = player.overlay_count

    print()
    print("Requesting next station...")

    engine.next_station()

    print(f"State: {engine.state.value}")
    print(f"Station: {engine.current_station.name}")

    time.sleep(0.2)

    after = player.overlay_count

    print()
    print(f"Overlay count before: {before}")
    print(f"Overlay count after:  {after}")

    assert after == before + 1

    print()
    print("Waiting for station switch...")
    time.sleep(1.1)

    print(f"State after switch: {engine.state.value}")
    print(
        f"Station after switch: "
        f"{engine.current_station.name}"
    )

    assert engine.state.value == "on_air"
    assert engine.current_station.name == "12_THEBEAT"

    engine.stop()

    print()
    print("Engine switching overlay test passed.")


if __name__ == "__main__":
    main()
