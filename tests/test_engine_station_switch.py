from pathlib import Path

from radio.engine import RadioEngine
from radio.library.gen1 import Gen1Loader


TEST_ROOT = Path("test_data/GTA IV")


def main() -> None:
    library = Gen1Loader().load(TEST_ROOT)
    engine = RadioEngine(library)

    print(f"Initial: {engine.current_station.name}")

    engine.next_station()
    print(f"Next:    {engine.current_station.name}")

    engine.next_station()
    print(f"Next:    {engine.current_station.name}")

    engine.previous_station()
    print(f"Previous:{engine.current_station.name}")

    print("Station switching test passed.")


if __name__ == "__main__":
    main()
