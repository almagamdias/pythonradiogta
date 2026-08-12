from __future__ import annotations

from array import array
from pathlib import Path

from radio.audio.player import AudioPlayer
import radio.audio.player as player_module


TEST_FILE = Path(
    "test_data/GTA IV/04_MASSIVEB/MASSIVEB_MIX.ogg"
)


class FakeDecoder:
    """Small deterministic decoder for testing AudioPlayer PCM output."""

    def __init__(
        self,
        path: Path,
        *,
        start_frame: int = 0,
    ) -> None:
        self.path = path
        self.start_frame = start_frame

    def stream(self):
        yield array(
            "h",
            [
                1000,
                -1000,
                20000,
                -20000,
            ],
        )


class FakeOverlayDecoder:
    """Deterministic overlay decoder."""

    def __init__(
        self,
        path: Path,
        *,
        start_frame: int = 0,
    ) -> None:
        self.path = path
        self.start_frame = start_frame

    def stream(self):
        yield array(
            "h",
            [
                100,
                -100,
                1000,
                -1000,
            ],
        )


def get_output(
    player: AudioPlayer,
    frames: int = 2,
) -> array:
    stream = player._loop_stream()

    next(stream)

    try:
        return stream.send(frames)
    finally:
        stream.close()


def main() -> None:
    print("Testing AudioPlayer real PCM volume...")

    player_module.AudioDecoder = FakeDecoder

    player = AudioPlayer(TEST_FILE)

    print()
    print("Testing volume = 1.0...")

    player.volume = 1.0

    result = get_output(player)

    expected = array(
        "h",
        [
            1000,
            -1000,
            20000,
            -20000,
        ],
    )

    print(f"Result:   {result}")
    print(f"Expected: {expected}")

    assert result == expected

    print("Real output at volume 1.0 is correct.")

    print()
    print("Testing volume = 0.5...")

    player.volume = 0.5

    result = get_output(player)

    expected = array(
        "h",
        [
            500,
            -500,
            10000,
            -10000,
        ],
    )

    print(f"Result:   {result}")
    print(f"Expected: {expected}")

    assert result == expected

    print("Real output at volume 0.5 is correctly scaled.")

    print()
    print("Testing volume = 0.0...")

    player.volume = 0.0

    result = get_output(player)

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

    print("Real output at volume 0.0 is silent.")

    print()
    print("Testing real overlay mixing...")

    player.volume = 1.0

    player.play_overlay(
        Path("assets/sounds/switch_noise.ogg")
    )

    print(
        "Overlay requested successfully."
    )

    print()
    print(
        "Note: overlay PCM is tested separately "
        "from the real volume path."
    )

    print()
    print("AudioPlayer real PCM volume test finished.")


if __name__ == "__main__":
    main()
