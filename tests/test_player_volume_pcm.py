from __future__ import annotations

from array import array
from pathlib import Path

from radio.audio.player import AudioPlayer


TEST_FILE = Path(
    "test_data/GTA IV/04_MASSIVEB/MASSIVEB_MIX.ogg"
)


def main() -> None:
    print("Testing AudioPlayer real PCM volume...")

    player = AudioPlayer(TEST_FILE)

    source = array(
        "h",
        [
            1000,
            -1000,
            20000,
            -20000,
            32767,
            -32768,
            500,
            -500,
        ],
    )

    original = array("h", source)

    print(f"Source PCM: {source}")

    print()
    print("Testing volume = 1.0...")

    player.volume = 1.0
    result = player._apply_volume(source)

    print(f"Result: {result}")

    assert result == original

    print("Volume 1.0 leaves PCM unchanged.")

    print()
    print("Testing volume = 0.5...")

    player.volume = 0.5
    result = player._apply_volume(source)

    expected = array(
        "h",
        [
            500,
            -500,
            10000,
            -10000,
            16383,
            -16384,
            250,
            -250,
        ],
    )

    print(f"Result:   {result}")
    print(f"Expected: {expected}")

    assert result == expected

    print("Volume 0.5 scales PCM correctly.")

    print()
    print("Testing volume = 0.0...")

    player.volume = 0.0
    result = player._apply_volume(source)

    expected = array("h", [0] * len(source))

    print(f"Result:   {result}")
    print(f"Expected: {expected}")

    assert result == expected

    print("Volume 0.0 produces silence.")

    print()
    print("Testing source PCM integrity...")

    assert source == original

    print("Source PCM remains unchanged.")

    print()
    print("Testing negative PCM values...")

    player.volume = 0.5

    negative_source = array(
        "h",
        [
            -100,
            -1000,
            -10000,
            -30000,
        ],
    )

    result = player._apply_volume(negative_source)

    expected = array(
        "h",
        [
            -50,
            -500,
            -5000,
            -15000,
        ],
    )

    print(f"Result:   {result}")
    print(f"Expected: {expected}")

    assert result == expected

    print("Negative PCM values scale correctly.")

    print()
    print("AudioPlayer real PCM volume test passed.")


if __name__ == "__main__":
    main()
