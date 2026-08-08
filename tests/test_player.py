from pathlib import Path
import time

from radio.audio.player import AudioPlayer


AUDIO_FILE = Path(
    "test_data/GTA IV/04_MASSIVEB/MASSIVEB_MIX.ogg"
)


def main() -> None:
    player = AudioPlayer(AUDIO_FILE)

    try:
        print(f"Playing: {AUDIO_FILE.name}")
        print("Playing for 10 seconds...")

        player.play()
        time.sleep(10)

    finally:
        player.stop()
        print("Audio player stopped.")


if __name__ == "__main__":
    main()
