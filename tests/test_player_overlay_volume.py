from __future__ import annotations

from array import array
from pathlib import Path

from radio.audio.player import AudioPlayer


MAIN_FILE = Path(
    "test_data/GTA IV/04_MASSIVEB/MASSIVEB_MIX.ogg"
)

OVERLAY_FILE = Path(
    "assets/sounds/switch_noise.ogg"
)


def main() -> None:
    print("Testing AudioPlayer overlay + volume...")

    player = AudioPlayer(MAIN_FILE)

    print(f"Initial volume: {player.volume}")
    assert player.volume == 1.0

    print()
    print("Setting volume to 0.5...")
    player.volume = 0.5

    assert player.volume == 0.5
    print(f"Volume: {player.volume}")

    print()
    print("Testing overlay request...")

    before = player.overlay_count

    player.play_overlay(OVERLAY_FILE)

    after = player.overlay_count

    print(f"Overlay count before: {before}")
    print(f"Overlay count after:  {after}")

    assert after == before + 1

    print("Overlay request registered.")

    print()
    print("Testing PCM volume with overlay enabled...")

    source = array(
        "h",
        [
            1000,
            -1000,
            20000,
            -20000,
            30000,
            -30000,
        ],
    )

    original = array("h", source)

    result = player._apply_volume(source)

    expected = array(
        "h",
        [
            500,
            -500,
            10000,
            -10000,
            15000,
            -15000,
        ],
    )

    print(f"Source:   {source}")
    print(f"Result:   {result}")
    print(f"Expected: {expected}")

    assert result == expected
    assert source == original

    print("Main PCM volume is correct.")
    print("Source PCM remains unchanged.")

    print()
    print("Testing volume = 1.0 with overlay request...")

    player.volume = 1.0

    source = array(
        "h",
        [
            1000,
            -1000,
            20000,
            -20000,
        ],
    )

    original = array("h", source)

    result = player._apply_volume(source)

    print(f"Result: {result}")

    assert result == source
    assert source == original

    print("Volume 1.0 leaves PCM unchanged.")

    print()
    print("Testing volume = 0.0 with overlay request...")

    player.volume = 0.0

    source = array(
        "h",
        [
            1000,
            -1000,
            20000,
            -20000,
        ],
    )

    original = array("h", source)

    result = player._apply_volume(source)

    expected = array(
        "h",
        [
            0,
            0,
            0,
            0,
        ],
    )

    print(f"Result:   {result}")
    print(f"Expected: {expected}")

    assert result == expected
    assert source == original

    print("Volume 0.0 produces silence.")

    print()
    print("Testing overlay request count...")

    player.play_overlay(OVERLAY_FILE)

    assert player.overlay_count == before + 2

    print(f"Overlay count: {player.overlay_count}")

    print()
    print("AudioPlayer overlay + volume test passed.")


if __name__ == "__main__":
    main()
