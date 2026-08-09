from pathlib import Path

from radio.engine import RadioEngine
from radio.library.gen1 import Gen1Loader

TEST_ROOT = Path("test_data/GTA IV")

def main() -> None:
    library = Gen1Loader().load(TEST_ROOT)
    engine = RadioEngine(library)

    duration = engine.current_song.duration

    positions = [
        engine._random_start_position(duration)
        for _ in range(100)
    ]

    minimum = min(positions)
    maximum = max(positions)

    print(f"Duration : {duration} ms")
    print(f"Minimum  : {minimum} ms")
    print(f"Maximum  : {maximum} ms")

    assert all(
        0 <= position < duration - 10_000
        for position in positions
    )

    assert len(set(positions)) > 1

    print("Random start test passed.")

if __name__ == "__main__":
    main()
