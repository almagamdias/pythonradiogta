from __future__ import annotations

from array import array
from pathlib import Path
from types import SimpleNamespace

import radio.audio.player as player_module
from radio.audio.player import (
    AudioPlayer,
    FADE_OUT_DURATION_MS,
)


class FakeDecoderStream:
    def __init__(
        self,
        chunks: list[array],
        on_close=None,
    ) -> None:
        self._chunks = iter(chunks)
        self._on_close = on_close
        self.closed = False

    def __next__(self) -> array:
        return next(self._chunks)

    def close(self) -> None:
        if self.closed:
            return

        self.closed = True

        if self._on_close is not None:
            self._on_close()


class FakeDecoder:
    instances: list[FakeDecoderStream] = []

    def __init__(
        self,
        path: Path,
        *,
        start_frame: int = 0,
    ) -> None:
        self.path = path
        self.start_frame = start_frame

    def stream(self) -> FakeDecoderStream:
        # 10 frames per chunk, stereo.
        #
        # The stream itself is infinite from the test's
        # perspective because every new decoder represents
        # another loop of the same file.
        stream = FakeDecoderStream(
            [
                array(
                    "h",
                    [1000, 1000] * 10,
                ),
                array(
                    "h",
                    [1000, 1000] * 10,
                ),
                array(
                    "h",
                    [1000, 1000] * 10,
                ),
                array(
                    "h",
                    [1000, 1000] * 10,
                ),
            ]
        )

        self.instances.append(stream)

        return stream


def _next_output(
    stream,
    frames: int,
) -> array:
    return stream.send(frames)


def _install_fakes():
    original_decoder = (
        player_module.AudioDecoder
    )
    original_info = (
        player_module.miniaudio.get_file_info
    )
    original_sample_rate = (
        player_module.AUDIO_SAMPLE_RATE
    )

    player_module.AudioDecoder = FakeDecoder

    # 4-second test file.
    player_module.miniaudio.get_file_info = (
        lambda path: SimpleNamespace(
            duration=4.0,
        )
    )

    # 10 output frames per second.
    player_module.AUDIO_SAMPLE_RATE = 10

    FakeDecoder.instances.clear()

    return (
        original_decoder,
        original_info,
        original_sample_rate,
    )


def _restore_fakes(
    original_decoder,
    original_info,
    original_sample_rate,
) -> None:
    player_module.AudioDecoder = (
        original_decoder
    )

    player_module.miniaudio.get_file_info = (
        original_info
    )

    player_module.AUDIO_SAMPLE_RATE = (
        original_sample_rate
    )


def test_fade_out_starts_two_seconds_before_eof() -> None:
    """
    A 4-second file must start fading at 2 seconds.

    Test sample rate:
        10 frames/sec

    Therefore:
        total = 40 frames
        fade  = 20 frames
    """
    (
        original_decoder,
        original_info,
        original_sample_rate,
    ) = _install_fakes()

    try:
        player = AudioPlayer(
            Path("test_loop.ogg"),
        )

        stream = player._audio_stream()

        next(stream)

        # First 20 frames are unaffected.
        output = _next_output(
            stream,
            frames=10,
        )

        assert output == array(
            "h",
            [1000, 1000] * 10,
        )

        output = _next_output(
            stream,
            frames=10,
        )

        assert output == array(
            "h",
            [1000, 1000] * 10,
        )

        # Frames 20..29:
        #
        # gain:
        # 1.00, 0.95, 0.90, ... 0.55
        expected = []

        for frame in range(20, 30):
            value = int(
                1000
                * (
                    (40 - frame)
                    / 20
                )
            )

            expected.extend(
                [value, value]
            )

        output = _next_output(
            stream,
            frames=10,
        )

        assert output == array(
            "h",
            expected,
        )

        # Frames 30..39:
        #
        # gain:
        # 0.50, 0.45, ... 0.05
        expected = []

        for frame in range(30, 40):
            value = int(
                1000
                * (
                    (40 - frame)
                    / 20
                )
            )

            expected.extend(
                [value, value]
            )

        output = _next_output(
            stream,
            frames=10,
        )

        assert output == array(
            "h",
            expected,
        )

    finally:
        _restore_fakes(
            original_decoder,
            original_info,
            original_sample_rate,
        )


def test_loop_restarts_at_full_volume_after_fade() -> None:
    """
    After the faded final frames, the next loop must start
    from the beginning at full volume.
    """
    (
        original_decoder,
        original_info,
        original_sample_rate,
    ) = _install_fakes()

    try:
        player = AudioPlayer(
            Path("test_loop.ogg"),
        )

        stream = player._audio_stream()

        next(stream)

        # Consume the complete 4-second file.
        for _ in range(4):
            _next_output(
                stream,
                frames=10,
            )

        # The next callback belongs to the new loop.
        output = _next_output(
            stream,
            frames=10,
        )

        assert output == array(
            "h",
            [1000, 1000] * 10,
        )

        # A new decoder must have been created.
        assert len(
            FakeDecoder.instances
        ) >= 2

        # The newest decoder is active.
        assert (
            FakeDecoder.instances[-1].closed
            is False
        )

    finally:
        _restore_fakes(
            original_decoder,
            original_info,
            original_sample_rate,
        )


def test_start_position_inside_fade_window() -> None:
    """
    Starting a song inside its final 2 seconds must immediately
    use the appropriate fade level.
    """
    (
        original_decoder,
        original_info,
        original_sample_rate,
    ) = _install_fakes()

    try:
        player = AudioPlayer(
            Path("test_loop.ogg"),
            start_position_ms=3_000,
        )

        stream = player._audio_stream()

        next(stream)

        # 4-second file.
        #
        # Start at 3 seconds.
        #
        # Fade progress:
        # (3 - 2) / 2 = 50%
        #
        # Therefore the first frame starts at 0.50 gain.
        output = _next_output(
            stream,
            frames=10,
        )

        expected = []

        for frame in range(30, 40):
            value = int(
                1000
                * (
                    (40 - frame)
                    / 20
                )
            )

            expected.extend(
                [value, value]
            )

        assert output == array(
            "h",
            expected,
        )

    finally:
        _restore_fakes(
            original_decoder,
            original_info,
            original_sample_rate,
        )


def test_volume_is_applied_after_fade() -> None:
    """
    Player volume must remain independent from the EOF fade.

    A 0.5 player volume is applied after the fade calculation.
    """
    (
        original_decoder,
        original_info,
        original_sample_rate,
    ) = _install_fakes()

    try:
        player = AudioPlayer(
            Path("test_loop.ogg"),
        )

        player.volume = 0.5

        stream = player._audio_stream()

        next(stream)

        # Skip the first 20 frames.
        _next_output(
            stream,
            frames=10,
        )
        _next_output(
            stream,
            frames=10,
        )

        output = _next_output(
            stream,
            frames=10,
        )

        expected = []

        for frame in range(20, 30):
            fade_gain = (
                (40 - frame)
                / 20
            )

            value = int(
                1000
                * fade_gain
                * 0.5
            )

            expected.extend(
                [value, value]
            )

        assert output == array(
            "h",
            expected,
        )

    finally:
        _restore_fakes(
            original_decoder,
            original_info,
            original_sample_rate,
        )


def test_fade_constant_is_two_seconds() -> None:
    """The production fade duration must be exactly 2 seconds."""
    assert FADE_OUT_DURATION_MS == 2_000


def run_all_tests() -> None:
    tests = [
        test_fade_out_starts_two_seconds_before_eof,
        test_loop_restarts_at_full_volume_after_fade,
        test_start_position_inside_fade_window,
        test_volume_is_applied_after_fade,
        test_fade_constant_is_two_seconds,
    ]

    for test in tests:
        test()
        print(
            f"{test.__name__}: passed"
        )


if __name__ == "__main__":
    run_all_tests()

    print()
    print("Player loop tests passed.")
