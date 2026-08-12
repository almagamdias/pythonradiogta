from __future__ import annotations

from array import array
from pathlib import Path

import radio.audio.player as player_module
from radio.audio.player import AudioPlayer


MAIN_FILE = Path("tests/fake_main.ogg")
OVERLAY_FILE = Path("tests/fake_overlay.ogg")


MAIN_PCM = array(
    "h",
    [
        1000,
        -1000,
        20000,
        -20000,
    ],
)

OVERLAY_PCM = array(
    "h",
    [
        100,
        -100,
        1000,
        -1000,
    ],
)


class FakeDecoder:
    """Deterministic decoder used by the real AudioPlayer stream."""

    def __init__(
        self,
        path: Path,
        *,
        start_frame: int = 0,
    ) -> None:
        self._path = path
        self._start_frame = start_frame

    def stream(self):
        if self._path == MAIN_FILE:
            yield array("h", MAIN_PCM)

        elif self._path == OVERLAY_FILE:
            yield array("h", OVERLAY_PCM)

        else:
            raise AssertionError(
                f"Unexpected decoder path: {self._path}"
            )


def read_output(
    player: AudioPlayer,
    frames: int = 2,
) -> array:
    stream = player._loop_stream()

    next(stream)

    try:
        return stream.send(frames)
    finally:
        stream.close()


def expected_mix() -> array:
    """
    Expected result of MAIN_PCM + OVERLAY_PCM.

    The values are intentionally far from int16 overflow.
    """

    return array(
        "h",
        [
            1100,
            -1100,
            21000,
            -21000,
        ],
    )


def main() -> None:
    print("Testing AudioPlayer real overlay + volume...")

    player_module.AudioDecoder = FakeDecoder

    print()
    print("Main PCM:")
    print(f"  {MAIN_PCM}")

    print("Overlay PCM:")
    print(f"  {OVERLAY_PCM}")

    print()
    print("Expected mixed PCM:")
    print(f"  {expected_mix()}")

    # ---------------------------------------------------------
    # Volume = 1.0
    # ---------------------------------------------------------

    print()
    print("Testing volume = 1.0 with real overlay...")

    player = AudioPlayer(MAIN_FILE)
    player.volume = 1.0
    player.play_overlay(OVERLAY_FILE)

    result = read_output(player)

    expected = expected_mix()

    print(f"Result:   {result}")
    print(f"Expected: {expected}")

    assert result == expected

    print(
        "Volume 1.0 preserves the mixed overlay output."
    )

    # ---------------------------------------------------------
    # Volume = 0.5
    # ---------------------------------------------------------

    print()
    print("Testing volume = 0.5 with real overlay...")

    player = AudioPlayer(MAIN_FILE)
    player.volume = 0.5
    player.play_overlay(OVERLAY_FILE)

    result = read_output(player)

    expected = array(
        "h",
        [
            550,
            -550,
            10500,
            -10500,
        ],
    )

    print(f"Result:   {result}")
    print(f"Expected: {expected}")

    assert result == expected

    print(
        "Volume 0.5 correctly scales the mixed output."
    )

    # ---------------------------------------------------------
    # Volume = 0.0
    # ---------------------------------------------------------

    print()
    print("Testing volume = 0.0 with real overlay...")

    player = AudioPlayer(MAIN_FILE)
    player.volume = 0.0
    player.play_overlay(OVERLAY_FILE)

    result = read_output(player)

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

    print(
        "Volume 0.0 produces silence even with overlay."
    )

    # ---------------------------------------------------------
    # Overlay count
    # ---------------------------------------------------------

    print()
    print("Testing overlay request count...")

    player = AudioPlayer(MAIN_FILE)

    assert player.overlay_count == 0

    player.play_overlay(OVERLAY_FILE)

    assert player.overlay_count == 1

    print(f"Overlay count: {player.overlay_count}")

    print()
    print("AudioPlayer real overlay + volume test passed.")


if __name__ == "__main__":
    main()
