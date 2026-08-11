from __future__ import annotations

from pathlib import Path

from radio.audio.player import AudioPlayer


TEST_FILE = Path(
    "test_data/GTA IV/04_MASSIVEB/MASSIVEB_MIX.ogg"
)


def main() -> None:
    print("Testing AudioPlayer volume API...")

    player = AudioPlayer(TEST_FILE)

    print(f"Initial volume: {player.volume}")
    assert player.volume == 1.0

    print("Setting volume to 0.5...")
    player.volume = 0.5

    assert player.volume == 0.5
    print(f"Volume: {player.volume}")

    print("Setting volume to 0.0...")
    player.volume = 0.0

    assert player.volume == 0.0
    print(f"Volume: {player.volume}")

    print("Setting volume to 1.0...")
    player.volume = 1.0

    assert player.volume == 1.0
    print(f"Volume: {player.volume}")

    print("Testing volume limits...")

    try:
        player.volume = -0.1
    except ValueError:
        print("Negative volume rejected.")
    else:
        raise AssertionError(
            "Negative volume must raise ValueError"
        )

    try:
        player.volume = 1.1
    except ValueError:
        print("Volume above 1.0 rejected.")
    else:
        raise AssertionError(
            "Volume above 1.0 must raise ValueError"
        )

    print()
    print("AudioPlayer volume test passed.")


if __name__ == "__main__":
    main()
