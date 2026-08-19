from __future__ import annotations

from array import array
from collections.abc import Generator
from pathlib import Path
from threading import Lock, Thread

import miniaudio

from radio.audio.decoder import AudioDecoder
from radio.audio.device import MiniaudioDevice
from radio.audio.mixer import mix_pcm
from radio.constants import AUDIO_SAMPLE_RATE
from radio.model.types import Milliseconds


AudioStream = Generator[array, int, None]

FADE_OUT_DURATION_MS = 2_000
CHANNELS = 2


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
        self._overlay_loop = False
        self._overlay_lock = Lock()
        self._overlay_count = 0
        self._overlay_generation = 0

        self._change_lock = Lock()
        self._pending_change: tuple[
            Path,
            Milliseconds,
        ] | None = None

        self._volume = 1.0

        self._duration_cache: dict[
            Path,
            int,
        ] = {}

        self._duration_lock = Lock()

        self._prepared_paths: set[Path] = set()
        self._preparing_paths: set[Path] = set()
        self._prepare_lock = Lock()

    @property
    def overlay_count(self) -> int:
        """Return the number of requested overlays."""
        return self._overlay_count

    @property
    def volume(self) -> float:
        """Return the current output volume."""
        return self._volume

    @volume.setter
    def volume(self, value: float) -> None:
        """Set the output volume."""
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

        self.stop_overlay()

        with self._change_lock:
            self._pending_change = None

    def prepare_song(
        self,
        path: Path,
    ) -> None:
        """
        Prepare a song in the background.

        This is intended to be called as soon as a station becomes
        the pending switch destination. While the switch overlay is
        playing, the file metadata and initial file access are warmed
        up without blocking the audio callback.
        """
        with self._prepare_lock:
            if path in self._prepared_paths:
                return

            if path in self._preparing_paths:
                return

            self._preparing_paths.add(path)

        thread = Thread(
            target=self._prepare_song,
            args=(path,),
            daemon=True,
        )

        thread.start()

    def _prepare_song(
        self,
        path: Path,
    ) -> None:
        """Perform blocking song preparation outside audio playback."""
        try:
            self._duration_frames(path)

            with path.open("rb") as source:
                source.read(64 * 1024)

        except OSError:
            return

        finally:
            with self._prepare_lock:
                self._preparing_paths.discard(path)

        with self._prepare_lock:
            self._prepared_paths.add(path)

    def change_song(
        self,
        path: Path,
        start_position_ms: Milliseconds = 0,
    ) -> None:
        """
        Change the current audio source without stopping
        the audio device.
        """
        with self._change_lock:
            self._pending_change = (
                path,
                start_position_ms,
            )

    def play_overlay(
        self,
        path: Path,
        *,
        loop: bool = False,
    ) -> None:
        """
        Start an overlay.

        If loop=True, the overlay restarts from the beginning
        whenever its decoder reaches EOF.
        """
        with self._overlay_lock:
            self._overlay_generation += 1
            self._overlay_path = path
            self._overlay_loop = loop
            self._overlay_count += 1

    def stop_overlay(self) -> None:
        """Stop the current overlay immediately."""
        with self._overlay_lock:
            self._overlay_generation += 1
            self._overlay_path = None
            self._overlay_loop = False

    def _take_overlay(
        self,
    ) -> tuple[
        Path | None,
        bool,
        int,
    ]:
        with self._overlay_lock:
            path = self._overlay_path
            loop = self._overlay_loop
            generation = self._overlay_generation

            self._overlay_path = None

        return path, loop, generation

    def _overlay_is_current(
        self,
        generation: int,
    ) -> bool:
        with self._overlay_lock:
            return (
                generation
                == self._overlay_generation
            )

    def _take_song_change(
        self,
    ) -> tuple[Path, Milliseconds] | None:
        with self._change_lock:
            change = self._pending_change
            self._pending_change = None

        return change

    def _duration_frames(
        self,
        path: Path,
    ) -> int:
        """
        Return the decoded output duration in frames.

        The result is cached because station switching may return
        to the same audio file many times.
        """
        with self._duration_lock:
            cached = self._duration_cache.get(path)

        if cached is not None:
            return cached

        info = miniaudio.get_file_info(
            str(path),
        )

        duration_frames = max(
            1,
            round(
                info.duration
                * AUDIO_SAMPLE_RATE
            ),
        )

        with self._duration_lock:
            self._duration_cache[path] = (
                duration_frames
            )

        return duration_frames

    def _fade_pcm(
        self,
        pcm: array,
        *,
        start_frame: int,
        duration_frames: int,
    ) -> array:
        """
        Apply a linear fade-out to PCM near the end
        of the current song.

        The fade is applied before overlay mixing, so an
        active switch overlay is not faded together with
        the station audio.
        """
        fade_frames = (
            FADE_OUT_DURATION_MS
            * AUDIO_SAMPLE_RATE
            // 1000
        )

        if fade_frames <= 0:
            return pcm

        fade_start = max(
            0,
            duration_frames - fade_frames,
        )

        fade_length = (
            duration_frames - fade_start
        )

        if fade_length <= 0:
            return pcm

        result = array(
            pcm.typecode,
            pcm,
        )

        frame_count = (
            len(result) // CHANNELS
        )

        for frame_offset in range(
            frame_count
        ):
            frame = (
                start_frame
                + frame_offset
            )

            if frame < fade_start:
                continue

            if frame >= duration_frames:
                continue

            gain = (
                duration_frames - frame
            ) / fade_length

            base = (
                frame_offset * CHANNELS
            )

            for channel in range(
                CHANNELS
            ):
                result[base + channel] = int(
                    result[base + channel]
                    * gain
                )

        return result

    def _loop_stream(self) -> AudioStream:
        """Backward-compatible stream entry point."""
        return self._audio_stream()

    def _audio_stream(self) -> AudioStream:
        decoder_stream = None
        overlay_stream = None

        buffer = array("h")
        overlay_buffer = array("h")

        current_path = self._path
        current_start_position_ms = (
            self._start_position_ms
        )

        main_duration_frames = (
            self._duration_frames(current_path)
        )

        main_position_frames = (
            current_start_position_ms
            * AUDIO_SAMPLE_RATE
            // 1000
        )

        main_position_frames %= main_duration_frames

        active_overlay_generation: int | None = None
        active_overlay_path: Path | None = None
        active_overlay_loop = False

        try:
            requested_frames = yield array("h")

            while True:
                required_samples = (
                    requested_frames
                    * CHANNELS
                )

                # -------------------------------------------------
                # SONG CHANGE
                # -------------------------------------------------

                song_change = (
                    self._take_song_change()
                )

                if song_change is not None:
                    (
                        current_path,
                        current_start_position_ms,
                    ) = song_change

                    if decoder_stream is not None:
                        decoder_stream.close()

                    decoder_stream = None
                    buffer = array("h")

                    main_duration_frames = (
                        self._duration_frames(
                            current_path,
                        )
                    )

                    main_position_frames = (
                        current_start_position_ms
                        * AUDIO_SAMPLE_RATE
                        // 1000
                    )

                    main_position_frames %= (
                        main_duration_frames
                    )

                # -------------------------------------------------
                # OVERLAY INVALIDATION
                # -------------------------------------------------

                if (
                    active_overlay_generation
                    is not None
                    and not self._overlay_is_current(
                        active_overlay_generation,
                    )
                ):
                    if overlay_stream is not None:
                        overlay_stream.close()

                    overlay_stream = None
                    overlay_buffer = array("h")

                    active_overlay_generation = None
                    active_overlay_path = None
                    active_overlay_loop = False

                # -------------------------------------------------
                # MAIN AUDIO
                # -------------------------------------------------

                while len(buffer) < required_samples:
                    if decoder_stream is None:
                        if (
                            main_position_frames
                            >= main_duration_frames
                        ):
                            main_position_frames = 0

                        decoder = AudioDecoder(
                            current_path,
                            start_frame=(
                                main_position_frames
                            ),
                        )

                        decoder_stream = (
                            decoder.stream()
                        )

                    try:
                        chunk = next(
                            decoder_stream
                        )

                    except StopIteration:
                        decoder_stream.close()
                        decoder_stream = None

                        main_position_frames = 0

                        continue

                    chunk_frames = (
                        len(chunk)
                        // CHANNELS
                    )

                    if chunk_frames <= 0:
                        continue

                    remaining_frames = (
                        main_duration_frames
                        - main_position_frames
                    )

                    if remaining_frames <= 0:
                        decoder_stream.close()
                        decoder_stream = None
                        main_position_frames = 0
                        continue

                    take_frames = min(
                        chunk_frames,
                        remaining_frames,
                    )

                    chunk_samples = (
                        take_frames
                        * CHANNELS
                    )

                    chunk_pcm = array(
                        "h",
                        chunk[
                            :chunk_samples
                        ],
                    )

                    chunk_pcm = self._fade_pcm(
                        chunk_pcm,
                        start_frame=(
                            main_position_frames
                        ),
                        duration_frames=(
                            main_duration_frames
                        ),
                    )

                    buffer.extend(
                        chunk_pcm
                    )

                    main_position_frames += (
                        take_frames
                    )

                    if (
                        main_position_frames
                        >= main_duration_frames
                    ):
                        decoder_stream.close()
                        decoder_stream = None
                        main_position_frames = 0

                output = array(
                    "h",
                    buffer[:required_samples],
                )

                del buffer[:required_samples]

                # -------------------------------------------------
                # NEW OVERLAY
                # -------------------------------------------------

                (
                    overlay_path,
                    overlay_loop,
                    overlay_generation,
                ) = self._take_overlay()

                if overlay_path is not None:
                    if overlay_stream is not None:
                        overlay_stream.close()

                    overlay_stream = (
                        AudioDecoder(
                            overlay_path,
                        ).stream()
                    )

                    overlay_buffer = array("h")

                    active_overlay_path = (
                        overlay_path
                    )
                    active_overlay_loop = (
                        overlay_loop
                    )
                    active_overlay_generation = (
                        overlay_generation
                    )

                # -------------------------------------------------
                # OVERLAY AUDIO
                # -------------------------------------------------

                if overlay_stream is not None:
                    if (
                        active_overlay_generation
                        is None
                        or not self._overlay_is_current(
                            active_overlay_generation,
                        )
                    ):
                        overlay_stream.close()
                        overlay_stream = None
                        overlay_buffer = array("h")

                        active_overlay_generation = None
                        active_overlay_path = None
                        active_overlay_loop = False

                    else:
                        while (
                            len(overlay_buffer)
                            < required_samples
                        ):
                            if not self._overlay_is_current(
                                active_overlay_generation,
                            ):
                                overlay_stream.close()
                                overlay_stream = None
                                overlay_buffer = array("h")

                                active_overlay_generation = None
                                active_overlay_path = None
                                active_overlay_loop = False

                                break

                            try:
                                chunk = next(
                                    overlay_stream,
                                )

                            except StopIteration:
                                if (
                                    active_overlay_loop
                                    and active_overlay_path
                                    is not None
                                    and self._overlay_is_current(
                                        active_overlay_generation,
                                    )
                                ):
                                    overlay_stream.close()

                                    overlay_stream = (
                                        AudioDecoder(
                                            active_overlay_path,
                                        ).stream()
                                    )

                                    continue

                                overlay_stream.close()
                                overlay_stream = None

                                # Do not discard the active generation
                                # yet. overlay_buffer may still contain
                                # decoded samples that must be mixed.
                                break

                            overlay_buffer.extend(
                                chunk
                            )

                # -------------------------------------------------
                # MIX
                # -------------------------------------------------

                if overlay_buffer:
                    if (
                        active_overlay_generation
                        is not None
                        and self._overlay_is_current(
                            active_overlay_generation,
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
                            output[
                                :overlay_samples
                            ],
                            overlay,
                        )

                        output[
                            :overlay_samples
                        ] = mixed

                        del overlay_buffer[
                            :overlay_samples
                        ]

                    else:
                        overlay_buffer = array("h")

                if (
                    overlay_stream is None
                    and not overlay_buffer
                    and active_overlay_generation
                    is not None
                    and not active_overlay_loop
                ):
                    active_overlay_generation = None
                    active_overlay_path = None

                # -------------------------------------------------
                # VOLUME
                # -------------------------------------------------

                output = self._apply_volume(
                    output,
                )

                requested_frames = yield output

        finally:
            if decoder_stream is not None:
                decoder_stream.close()

            if overlay_stream is not None:
                overlay_stream.close()

    def _apply_volume(
        self,
        pcm: array,
    ) -> array:
        """Apply the current master volume."""
        if self._volume == 1.0:
            return pcm

        return array(
            pcm.typecode,
            (
                int(
                    sample * self._volume
                )
                for sample in pcm
            ),
        )
