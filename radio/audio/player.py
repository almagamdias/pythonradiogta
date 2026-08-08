from __future__ import annotations

from array import array
from collections.abc import Generator
from pathlib import Path

import miniaudio

from radio.audio.decoder import AudioDecoder
from radio.audio.device import MiniaudioDevice


AudioStream = Generator[array, int, None]


class AudioPlayer:
    """Play one audio file continuously."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._decoder = AudioDecoder(path)
        self._device: MiniaudioDevice | None = None
        self._stream: AudioStream | None = None

    def play(self) -> None:
        """Start continuous playback."""
        if self._device is not None:
            return

        self._stream = self._loop_stream()
        next(self._stream)

        self._device = MiniaudioDevice(self._stream)
        self._device.start()

    def stop(self) -> None:
        """Stop playback."""
        if self._device is None:
            return

        self._device.stop()
        self._device.close()

        self._device = None
        self._stream = None

    def _loop_stream(self) -> AudioStream:
        """Create an endless stream that restarts at EOF."""
        while True:
            stream = self._decoder.stream()

            try:
                yield from stream
            except GeneratorExit:
                stream.close()
                raise
