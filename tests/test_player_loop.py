from __future__ import annotations

import math
import time
import wave
from pathlib import Path

from radio.audio.player import AudioPlayer


TEST_FILE = Path("tests/test_loop.wav")


def create_test_wav() -> None:
    sample_rate = 48_000
    duration = 2
    frames = sample_rate * duration

    with wave.open(str(TEST_FILE), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)

        for i in range(frames):
            phase = i / sample_rate

            # 440 Hz tone.
            sample = int(
                0.2
                * 32767
                * math.sin(2 * math.pi * 440 * phase)
            )

            data = sample.to_bytes(2, "little", signed=True)
            wav.writeframes(data + data)


def main() -> None:
    create_test_wav()

    player = AudioPlayer(TEST_FILE)

    try:
        print("Playing loop test...")
        print("The file is 2 seconds long.")
        print("Playback will run for 10 seconds.")
        print("Expected: approximately 5 loops.")

        player.play()
        time.sleep(10)

    finally:
        player.stop()
        print("Loop test finished.")


if __name__ == "__main__":
    main()
