from __future__ import annotations

import time
from pathlib import Path

from radio.audio.decoder import AudioDecoder
from radio.audio.device import MiniaudioDevice


AUDIO_FILE = Path(
    "test_data/GTA IV/04_MASSIVEB/MASSIVEB_MIX.ogg"
)


def main() -> None:
    decoder = AudioDecoder(AUDIO_FILE)
    stream = decoder.stream()

    device = MiniaudioDevice(stream)

    try:
        device.start()

        print(f"Playing: {AUDIO_FILE.name}")
        print("Playing for 5 seconds...")

        time.sleep(5)

    finally:
        device.stop()
        device.close()

        print("Audio device stopped.")


if __name__ == "__main__":
    main()
