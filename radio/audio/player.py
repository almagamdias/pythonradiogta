from __future__ import annotations

from array import array
from collections.abc import Generator
from pathlib import Path

from radio.audio.decoder import AudioDecoder
from radio.audio.device import MiniaudioDevice


AudioStream = Generator[array, int, None]


class AudioPlayer:
    """Play one audio file continuously."""

    def __init__(self, path: Path) -> None:
        self._decoder = AudioDecoder(path)
        self._device: MiniaudioDevice | None = None
        self._stream: AudioStream | None = None

    def play(self) -> None:
        """Start playback."""
        if self._device is not None:
            return

        self._stream = self._loop_stream()
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
        decoder_stream = None
        buffer = array("h")

        try:
            requested_frames = yield array("h")

            while True:
                required_samples = requested_frames * 2

                while len(buffer) < required_samples:
                    if decoder_stream is None:
                        decoder_stream = self._decoder.stream()

                    try:
                        chunk = next(decoder_stream)
                    except StopIteration:
                        decoder_stream.close()
                        decoder_stream = None
                        continue

                    buffer.extend(chunk)

                output = array(
                    "h",
                    buffer[:required_samples],
                )

                del buffer[:required_samples]

                requested_frames = yield output

        finally:
            if decoder_stream is not None:
                decoder_stream.close()
