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
    """Play one audio source continuously with optional PCM overlay."""

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
        self._overlay_generation = 0

        self._change_lock = Lock()
        self._pending_change: tuple[
            Path,
            Milliseconds,
        ] | None = None

        self._volume = 1.0

    @property
    def overlay_count(self) -> int:
        """Return the number of requested overlays."""
        return self._overlay_count

    @property
    def volume(self) -> float:
        return self._volume

    @volume.setter
    def volume(self, value: float) -> None:
        if not 0.0 <= value <= 1.0:
            raise ValueError(
                "Volume must be between 0.0 and 1.0"
            )

        self._volume = float(value)

    def play(self) -> None:
        """Start playback."""
        if self._device is not None:
            return

        self._stream = self._audio_stream()
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

        self._clear_overlay()

        with self._change_lock:
            self._pending_change = None

    def change_song(
        self,
        path: Path,
        start_position_ms: Milliseconds = 0,
    ) -> None:
        """
        Change the current audio source without stopping playback.

        The audio device remains alive.

        Any overlay belonging to the previous source is cancelled
        immediately from the control side and invalidated for the
        audio stream.
        """
        self._clear_overlay()

        with self._change_lock:
            self._pending_change = (
                path,
                start_position_ms,
            )

    def play_overlay(self, path: Path) -> None:
        """
        Queue a short audio file to be mixed over the main stream.

        A new overlay replaces a previously queued overlay.
        """
        with self._overlay_lock:
            self._overlay_generation += 1
            self._overlay_path = path
            self._overlay_count += 1

    def _clear_overlay(self) -> None:
        """
        Cancel the current overlay.

        The audio stream owns the decoder, so invalidation is done
        through the generation counter.
        """
        with self._overlay_lock:
            self._overlay_generation += 1
            self._overlay_path = None

    def _take_overlay(
        self,
    ) -> tuple[Path | None, int]:
        with self._overlay_lock:
            path = self._overlay_path
            generation = self._overlay_generation
            self._overlay_path = None

        return path, generation

    def _overlay_is_current(
        self,
        generation: int,
    ) -> bool:
        with self._overlay_lock:
            return (
                generation == self._overlay_generation
            )

    def _take_song_change(
        self,
    ) -> tuple[Path, Milliseconds] | None:
        with self._change_lock:
            change = self._pending_change
            self._pending_change = None

        return change

    def _apply_volume(self, pcm: array) -> array:
        if self._volume == 1.0:
            return pcm

        return array(
            pcm.typecode,
            (
                int(sample * self._volume)
                for sample in pcm
            ),
        )

    def _loop_stream(self) -> AudioStream:
        """
        Backward-compatible stream entry point.

        Some existing tests use _loop_stream() directly.
        """
        return self._audio_stream()

    def _audio_stream(self) -> AudioStream:
        decoder_stream = None
        overlay_stream = None

        buffer = array("h")
        overlay_buffer = array("h")

        current_path = self._path
        current_start_position_ms = self._start_position_ms

        active_overlay_generation: int | None = None

        try:
            requested_frames = yield array("h")

            while True:
                required_samples = requested_frames * 2

                # -------------------------------------------------
                # SONG CHANGE
                # -------------------------------------------------

                song_change = self._take_song_change()

                if song_change is not None:
                    (
                        current_path,
                        current_start_position_ms,
                    ) = song_change

                    if decoder_stream is not None:
                        decoder_stream.close()

                    decoder_stream = None
                    buffer = array("h")

                    # A station change immediately invalidates
                    # the old switch overlay.
                    if overlay_stream is not None:
                        overlay_stream.close()

                    overlay_stream = None
                    overlay_buffer = array("h")
                    active_overlay_generation = None

                # -------------------------------------------------
                # OVERLAY INVALIDATION
                # -------------------------------------------------

                if (
                    active_overlay_generation is not None
                    and not self._overlay_is_current(
                        active_overlay_generation
                    )
                ):
                    if overlay_stream is not None:
                        overlay_stream.close()

                    overlay_stream = None
                    overlay_buffer = array("h")
                    active_overlay_generation = None

                # -------------------------------------------------
                # MAIN AUDIO
                # -------------------------------------------------

                while len(buffer) < required_samples:
                    if decoder_stream is None:
                        start_frame = (
                            current_start_position_ms
                            * AUDIO_SAMPLE_RATE
                            // 1000
                        )

                        decoder = AudioDecoder(
                            current_path,
                            start_frame=start_frame,
                        )

                        decoder_stream = decoder.stream()

                        # Seek is used only for the first decoder
                        # after a song change.
                        #
                        # Every EOF restart begins from zero.
                        current_start_position_ms = 0

                    try:
                        chunk = next(decoder_stream)

                    except StopIteration:
                        decoder_stream.close()
                        decoder_stream = None

                        # Only the current song restarts.
                        current_start_position_ms = 0

                        continue

                    buffer.extend(chunk)

                output = array(
                    "h",
                    buffer[:required_samples],
                )

                del buffer[:required_samples]

                # -------------------------------------------------
                # OVERLAY
                # -------------------------------------------------

                (
                    overlay_path,
                    overlay_generation,
                ) = self._take_overlay()

                if overlay_path is not None:
                    if overlay_stream is not None:
                        overlay_stream.close()

                    overlay_stream = AudioDecoder(
                        overlay_path
                    ).stream()

                    overlay_buffer = array("h")

                    active_overlay_generation = (
                        overlay_generation
                    )

                if overlay_stream is not None:
                    if (
                        active_overlay_generation is None
                        or not self._overlay_is_current(
                            active_overlay_generation
                        )
                    ):
                        overlay_stream.close()
                        overlay_stream = None
                        overlay_buffer = array("h")
                        active_overlay_generation = None

                    else:
                        while len(overlay_buffer) < required_samples:
                            if not self._overlay_is_current(
                                active_overlay_generation
                            ):
                                overlay_stream.close()
                                overlay_stream = None
                                overlay_buffer = array("h")
                                active_overlay_generation = None
                                break

                            try:
                                chunk = next(
                                    overlay_stream
                                )

                            except StopIteration:
                                overlay_stream.close()
                                overlay_stream = None
                                overlay_buffer = array("h")
                                active_overlay_generation = None
                                break

                            overlay_buffer.extend(chunk)

                if overlay_buffer:
                    if (
                        active_overlay_generation is not None
                        and self._overlay_is_current(
                            active_overlay_generation
                        )
                    ):
                        overlay_samples = min(
                            len(overlay_buffer),
                            required_samples,
                        )

                        overlay = array(
                            "h",
                            overlay_buffer[
                                :overlay_samples
                            ],
                        )

                        mixed = mix_pcm(
                            output[:overlay_samples],
                            overlay,
                        )

                        output[:overlay_samples] = mixed

                        del overlay_buffer[
                            :overlay_samples
                        ]

                    else:
                        overlay_buffer = array("h")

                        if overlay_stream is not None:
                            overlay_stream.close()

                        overlay_stream = None
                        active_overlay_generation = None

                # -------------------------------------------------
                # VOLUME
                # -------------------------------------------------

                output = self._apply_volume(output)

                requested_frames = yield output

        finally:
            if decoder_stream is not None:
                decoder_stream.close()

            if overlay_stream is not None:
                overlay_stream.close()
