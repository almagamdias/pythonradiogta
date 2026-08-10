from __future__ import annotations

import time
from pathlib import Path

from radio.audio.player import AudioPlayer


MAIN_FILE = Path("test_data/GTA IV/04_MASSIVEB/MASSIVEB_MIX.ogg")
OVERLAY_FILE = Path("assets/sounds/switch_noise.ogg")


def main() -> None:
    player = AudioPlayer(
        MAIN_FILE,
        start_position_ms=0,
    )

    print(f"Main file:    {MAIN_FILE}")
    print(f"Overlay file: {OVERLAY_FILE}")

    print()
    print("Starting main playback...")

    player.play()

    time.sleep(2)

    print("Playing switch noise...")
    player.play_overlay(OVERLAY_FILE)

    print("Main playback continues underneath.")
    print("Waiting 3 seconds...")

    time.sleep(3)

    player.stop()

    print("Player mix test finished.")


if __name__ == "__main__":
    main()
