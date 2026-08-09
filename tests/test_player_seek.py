from __future__ import annotations

from pathlib import Path

from radio.audio.decoder import AudioDecoder


TEST_FILE = Path("test_data/GTA IV/04_MASSIVEB/MASSIVEB_MIX.ogg")


def read_first_samples(start_frame: int) -> list[int]:
    decoder = AudioDecoder(
        TEST_FILE,
        start_frame=start_frame,
    )

    stream = decoder.stream()

    try:
        pcm = next(stream)
    finally:
        stream.close()

    return pcm[:16].tolist()


def main() -> None:
    start = read_first_samples(0)
    middle = read_first_samples(100_000)

    print(f"Start samples : {start}")
    print(f"Seek samples  : {middle}")
    print(f"Different     : {start != middle}")

    assert start != middle


if __name__ == "__main__":
    main()
