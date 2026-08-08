from __future__ import annotations

import math
import struct
import time
from collections.abc import Generator

from radio.audio.device import MiniaudioDevice


SAMPLE_RATE = 48_000
CHANNELS = 2
FREQUENCY = 440


def sine_generator() -> Generator[bytes, int, None]:
    phase = 0.0
    phase_step = 2.0 * math.pi * FREQUENCY / SAMPLE_RATE

    frames = yield b""

    while True:
        samples = bytearray()

        for _ in range(frames):
            sample = int(
                math.sin(phase) * 0.15 * 32767
            )

            phase += phase_step

            packed = struct.pack("<h", sample)

            samples.extend(packed)
            samples.extend(packed)

        frames = yield bytes(samples)


def main() -> None:
    generator = sine_generator()
    device = MiniaudioDevice(
        generator,
        sample_rate=SAMPLE_RATE,
        channels=CHANNELS,
    )

    try:
        device.start()

        print("Playing 440 Hz test tone...")
        time.sleep(2)

    finally:
        device.stop()
        device.close()

        print("Audio device stopped.")


if __name__ == "__main__":
    main()
