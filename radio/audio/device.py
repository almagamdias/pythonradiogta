from __future__ import annotations
import miniaudio

from array import array
from collections.abc import Generator

AudioGenerator = Generator[array, int, None]


class MiniaudioDevice:
    """Audio output device backed by miniaudio."""

    def __init__(
        self,
        generator: AudioGenerator,
        *,
        sample_rate: int = 48_000,
        channels: int = 2,
        buffersize_msec: int = 50,
    ) -> None:
        self._device = miniaudio.PlaybackDevice(
            output_format=miniaudio.SampleFormat.SIGNED16,
            nchannels=channels,
            sample_rate=sample_rate,
            buffersize_msec=buffersize_msec,
            app_name="GTA Radio Simulator",
        )

        self._generator = generator

    def start(self) -> None:
        next(self._generator)
        self._device.start(self._generator)

    def stop(self) -> None:
        self._device.stop()

    def close(self) -> None:
        self._device.close()
