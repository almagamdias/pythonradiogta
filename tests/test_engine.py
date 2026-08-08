from pathlib import Path

from radio.engine import RadioEngine
from radio.library.gen1 import Gen1Loader


def main() -> None:
    library = Gen1Loader().load(
        Path("test_data/GTA IV")
    )

    engine = RadioEngine(library)

    print(f"Stations: {len(engine.stations)}")
    print(f"Station: {engine.current_station.name}")
    print(f"Song: {engine.current_song.title}")
    print(f"Duration: {engine.current_song.duration} ms")

    print("Playing...")
    engine.play()

    input("Press Enter to stop...")

    engine.stop()
    print("Stopped.")


if __name__ == "__main__":
    main()
