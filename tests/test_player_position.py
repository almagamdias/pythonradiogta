from __future__ import annotations

from pathlib import Path

from radio.audio.player import AudioPlayer


TEST_FILE = Path(
    "test_data/GTA IV/04_MASSIVEB/MASSIVEB_MIX.ogg"
)


def read_samples(position_ms: int) -> list[int]:
    player = AudioPlayer(
        TEST_FILE,
        start_position_ms=position_ms,
    )

    stream = player._loop_stream()

    try:
        next(stream)
        pcm = stream.send(4096)
    finally:
        stream.close()

    return pcm[:32].tolist()


def main() -> None:
    start = read_samples(0)
    middle = read_samples(10_000)

    print(f"0 ms     : {start}")
    print(f"10 sec   : {middle}")
    print(f"Different: {start != middle}")

    assert start != middle


if __name__ == "__main__":
    main()
