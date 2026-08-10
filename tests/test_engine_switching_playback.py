from __future__ import annotations

import time
from pathlib import Path

from radio.engine import RadioEngine
from radio.library.gen1 import Gen1Loader


TEST_ROOT = Path("test_data/GTA IV")


def main() -> None:
    library = Gen1Loader().load(TEST_ROOT)
    engine = RadioEngine(library)

    print(f"Playing: {engine.current_station.name}")
    print(f"Song:    {engine.current_song.title}")

    engine.play()

    print("Playing first station for 2 seconds...")
    time.sleep(2)

    print()
    print("Requesting next station...")
    engine.next_station()

    print(f"State immediately: {engine.state.value}")
    print(f"Current station:   {engine.current_station.name}")

    print()
    print("Waiting 0.5 seconds...")
    time.sleep(0.5)

    print(f"State after 0.5s: {engine.state.value}")
    print(f"Still playing:    {engine.current_station.name}")

    print()
    print("Waiting for station switch...")
    time.sleep(0.8)

    print(f"State after switch: {engine.state.value}")
    print(f"New station:        {engine.current_station.name}")
    print(f"Song:               {engine.current_song.title}")

    print()
    print("Playing new station for 3 seconds...")
    time.sleep(3)

    engine.stop()

    print("Station switching playback test finished.")


if __name__ == "__main__":
    main()
