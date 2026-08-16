from __future__ import annotations

from array import array
from pathlib import Path

import radio.audio.player as player_module
from radio.audio.player import AudioPlayer


class FakeDecoderStream:
    def __init__(
        self,
        *,
        path: Path,
        chunks: list[array],
        on_close,
    ) -> None:
        self.path = path
        self._chunks = iter(chunks)
        self._on_close = on_close
        self.closed = False

    def __next__(self) -> array:
        return next(self._chunks)

    def close(self) -> None:
        if self.closed:
            return

        self.closed = True
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
        if self.path.name == "overlay.ogg":
            # Two samples, then EOF.
            #
            # With required_samples=4 this forces:
            #
            # loop=True:
            #   chunk -> EOF -> restart -> chunk
            #
            # loop=False:
            #   chunk -> EOF
            #
            stream = FakeDecoderStream(
                path=self.path,
                chunks=[
                    array(
                        "h",
                        [1000, 1000],
                    ),
                ],
                on_close=lambda: None,
            )

        else:
            # Main audio continuously provides enough samples.
            stream = FakeDecoderStream(
                path=self.path,
                chunks=[
                    array(
                        "h",
                        [0, 0, 0, 0],
                    ),
                ],
                on_close=lambda: None,
            )

        self.instances.append(stream)

        return stream


def _next_output(
    stream,
    frames: int = 2,
) -> array:
    return stream.send(frames)


def test_overlay_loops_after_eof() -> None:
    FakeDecoder.instances.clear()

    original_decoder = player_module.AudioDecoder
    player_module.AudioDecoder = FakeDecoder

    try:
        player = AudioPlayer(
            Path("main.ogg"),
        )

        stream = player._audio_stream()

        next(stream)

        player.play_overlay(
            Path("overlay.ogg"),
            loop=True,
        )

        output = _next_output(stream)

        assert output == array(
            "h",
            [
                1000,
                1000,
                1000,
                1000,
            ],
        )

        overlay_streams = [
            instance
            for instance in FakeDecoder.instances
            if instance.path.name == "overlay.ogg"
        ]

        # The first decoder reached EOF and was closed.
        assert len(overlay_streams) == 2
        assert overlay_streams[0].closed is True

        # The second decoder is currently active.
        assert overlay_streams[1].closed is False

    finally:
        player_module.AudioDecoder = original_decoder


def test_overlay_does_not_loop_when_disabled() -> None:
    FakeDecoder.instances.clear()

    original_decoder = player_module.AudioDecoder
    player_module.AudioDecoder = FakeDecoder

    try:
        player = AudioPlayer(
            Path("main.ogg"),
        )

        stream = player._audio_stream()

        next(stream)

        player.play_overlay(
            Path("overlay.ogg"),
            loop=False,
        )

        output = _next_output(stream)

        # The overlay contains only two samples.
        # The remaining two samples must remain main audio.
        assert output == array(
            "h",
            [
                1000,
                1000,
                0,
                0,
            ],
        )

        # Overlay must not restart.
        overlay_streams = [
            instance
            for instance in FakeDecoder.instances
            if instance.path.name == "overlay.ogg"
        ]

        assert len(overlay_streams) == 1
        assert overlay_streams[0].closed is True

        # Next callback must contain only main audio.
        output = _next_output(stream)

        assert output == array(
            "h",
            [
                0,
                0,
                0,
                0,
            ],
        )

    finally:
        player_module.AudioDecoder = original_decoder


def test_stop_overlay_stops_loop() -> None:
    FakeDecoder.instances.clear()

    original_decoder = player_module.AudioDecoder
    player_module.AudioDecoder = FakeDecoder

    try:
        player = AudioPlayer(
            Path("main.ogg"),
        )

        stream = player._audio_stream()

        next(stream)

        player.play_overlay(
            Path("overlay.ogg"),
            loop=True,
        )

        output = _next_output(stream)

        assert output == array(
            "h",
            [
                1000,
                1000,
                1000,
                1000,
            ],
        )

        # This is what engine.py should do when
        # pending_station becomes None.
        player.stop_overlay()

        output = _next_output(stream)

        assert output == array(
            "h",
            [
                0,
                0,
                0,
                0,
            ],
        )

        # Every overlay decoder must now be closed.
        overlay_streams = [
            instance
            for instance in FakeDecoder.instances
            if instance.path.name == "overlay.ogg"
        ]

        assert overlay_streams
        assert all(
            instance.closed
            for instance in overlay_streams
        )

    finally:
        player_module.AudioDecoder = original_decoder


if __name__ == "__main__":
    test_overlay_loops_after_eof()
    test_overlay_does_not_loop_when_disabled()
    test_stop_overlay_stops_loop()

    print("Overlay tests passed.")
