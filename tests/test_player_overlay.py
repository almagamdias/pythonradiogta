from __future__ import annotations

from array import array
from pathlib import Path
from types import SimpleNamespace

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
            stream = FakeDecoderStream(
                path=self.path,
                chunks=[
                    array("h", [1000, 1000]),
                ],
                on_close=lambda: None,
            )

        else:
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


def _install_fakes() -> object:
    """
    Replace AudioDecoder and miniaudio.get_file_info.

    The current AudioPlayer asks for the main source duration
    even in overlay tests. The test paths are fake paths, so
    get_file_info must be mocked as well.
    """
    original_decoder = player_module.AudioDecoder
    original_get_file_info = (
        player_module.miniaudio.get_file_info
    )

    player_module.AudioDecoder = FakeDecoder

    player_module.miniaudio.get_file_info = (
        lambda path: SimpleNamespace(
            duration=10.0,
        )
    )

    FakeDecoder.instances.clear()

    return (
        original_decoder,
        original_get_file_info,
    )


def _restore_fakes(
    original_decoder,
    original_get_file_info,
) -> None:
    """Restore the real decoder and file-info function."""
    player_module.AudioDecoder = original_decoder

    player_module.miniaudio.get_file_info = (
        original_get_file_info
    )


def test_overlay_loops_after_eof() -> None:
    """
    A looping overlay must restart after EOF.
    """
    (
        original_decoder,
        original_get_file_info,
    ) = _install_fakes()

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
            [1000, 1000, 1000, 1000],
        )

        overlay_streams = [
            instance
            for instance in FakeDecoder.instances
            if instance.path.name == "overlay.ogg"
        ]

        assert len(overlay_streams) == 2

        assert overlay_streams[0].closed is True

        assert overlay_streams[1].closed is False

    finally:
        _restore_fakes(
            original_decoder,
            original_get_file_info,
        )


def test_overlay_does_not_loop_when_disabled() -> None:
    """
    A non-looping overlay must stop after EOF.
    """
    (
        original_decoder,
        original_get_file_info,
    ) = _install_fakes()

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

        assert output == array(
            "h",
            [1000, 1000, 0, 0],
        )

        output = _next_output(stream)

        assert output == array(
            "h",
            [0, 0, 0, 0],
        )

        overlay_streams = [
            instance
            for instance in FakeDecoder.instances
            if instance.path.name == "overlay.ogg"
        ]

        assert len(overlay_streams) == 1

        assert overlay_streams[0].closed is True

    finally:
        _restore_fakes(
            original_decoder,
            original_get_file_info,
        )


def test_stop_overlay_stops_loop() -> None:
    """
    stop_overlay() must immediately stop a looping overlay.
    """
    (
        original_decoder,
        original_get_file_info,
    ) = _install_fakes()

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
            [1000, 1000, 1000, 1000],
        )

        player.stop_overlay()

        output = _next_output(stream)

        assert output == array(
            "h",
            [0, 0, 0, 0],
        )

        assert all(
            instance.closed
            for instance in FakeDecoder.instances
            if instance.path.name == "overlay.ogg"
        )

    finally:
        _restore_fakes(
            original_decoder,
            original_get_file_info,
        )


def run_all_tests() -> None:
    tests = [
        test_overlay_loops_after_eof,
        test_overlay_does_not_loop_when_disabled,
        test_stop_overlay_stops_loop,
    ]

    for test in tests:
        test()
        print(
            f"{test.__name__}: passed"
        )


if __name__ == "__main__":
    run_all_tests()

    print()
    print("Overlay tests passed.")
