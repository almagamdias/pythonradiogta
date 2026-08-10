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

    print("Playing for 5 seconds...")
    time.sleep(5)

    engine.next_station()

    print(f"Switched to: {engine.current_station.name}")
    print(f"Song:        {engine.current_song.title}")

    print("Playing new station for 5 seconds...")
    time.sleep(5)

    engine.stop()

    print("Station playback test finished.")


if __name__ == "__main__":
    main()
