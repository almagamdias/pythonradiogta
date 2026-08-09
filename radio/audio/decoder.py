from __future__ import annotations

from array import array
from collections.abc import Generator
from pathlib import Path

import miniaudio

from radio.constants import AUDIO_CHANNELS, AUDIO_SAMPLE_RATE


AudioStream = Generator[array, int, None]


class AudioDecoder:
    """Stream decoded audio from a file."""

    def __init__(
        self,
        path: Path,
        *,
        start_frame: int = 0,
    ) -> None:
        self._path = path
        self._start_frame = start_frame

    def stream(self) -> AudioStream:
        """Create a new PCM stream."""
        return miniaudio.stream_file(
            filename=str(self._path),
            output_format=miniaudio.SampleFormat.SIGNED16,
            nchannels=AUDIO_CHANNELS,
            sample_rate=AUDIO_SAMPLE_RATE,
            frames_to_read=4096,
            seek_frame=self._start_frame,
        )
