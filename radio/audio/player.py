from __future__ import annotations

from array import array
from collections.abc import Generator
from pathlib import Path
from threading import Lock

from radio.audio.decoder import AudioDecoder
from radio.audio.device import MiniaudioDevice
from radio.audio.mixer import mix_pcm
from radio.constants import AUDIO_SAMPLE_RATE
from radio.model.types import Milliseconds


AudioStream = Generator[array, int, None]


class AudioPlayer:
    """Play one audio file continuously with optional PCM overlay."""

    def __init__(
        self,
        path: Path,
        *,
        start_position_ms: Milliseconds = 0,
    ) -> None:
        self._path = path
        self._start_position_ms = start_position_ms

        self._device: MiniaudioDevice | None = None
        self._stream: AudioStream | None = None

        self._overlay_path: Path | None = None
        self._overlay_lock = Lock()
        self._overlay_count = 0

    @property
    def overlay_count(self) -> int:
        """Return the number of requested overlays."""
        return self._overlay_count

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

        with self._overlay_lock:
            self._overlay_path = None

    def play_overlay(self, path: Path) -> None:
        """Queue a short audio file to be mixed over the main stream."""
        with self._overlay_lock:
            self._overlay_path = path
            self._overlay_count += 1

    def _take_overlay_path(self) -> Path | None:
        with self._overlay_lock:
            path = self._overlay_path
            self._overlay_path = None

        return path

    def _loop_stream(self) -> AudioStream:
        decoder_stream = None
        overlay_stream = None

        buffer = array("h")
        overlay_buffer = array("h")

        first_stream = True

        start_frame = (
            self._start_position_ms * AUDIO_SAMPLE_RATE // 1000
        )

        try:
            requested_frames = yield array("h")

            while True:
                required_samples = requested_frames * 2

                while len(buffer) < required_samples:
                    if decoder_stream is None:
                        decoder = AudioDecoder(
                            self._path,
                            start_frame=(
                                start_frame
                                if first_stream
                                else 0
                            ),
                        )

                        decoder_stream = decoder.stream()
                        first_stream = False

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

                overlay_path = self._take_overlay_path()

                if overlay_path is not None:
                    if overlay_stream is not None:
                        overlay_stream.close()

                    overlay_stream = AudioDecoder(
                        overlay_path
                    ).stream()

                    overlay_buffer = array("h")

                if overlay_stream is not None:
                    while len(overlay_buffer) < required_samples:
                        try:
                            chunk = next(overlay_stream)
                        except StopIteration:
                            overlay_stream.close()
                            overlay_stream = None
                            break

                        overlay_buffer.extend(chunk)

                if overlay_buffer:
                    overlay_samples = min(
                        len(overlay_buffer),
                        required_samples,
                    )

                    overlay = array(
                        "h",
                        overlay_buffer[:overlay_samples],
                    )

                    mixed = mix_pcm(
                        output[:overlay_samples],
                        overlay,
                    )

                    output[:overlay_samples] = mixed

                    del overlay_buffer[:overlay_samples]

                requested_frames = yield output

        finally:
            if decoder_stream is not None:
                decoder_stream.close()

            if overlay_stream is not None:
                overlay_stream.close()
