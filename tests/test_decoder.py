from pathlib import Path

from radio.audio.decoder import AudioDecoder


def main() -> None:
    path = Path(
        "test_data/GTA IV/04_MASSIVEB/MASSIVEB_MIX.ogg"
    )

    decoder = AudioDecoder(path)
    stream = decoder.stream()

    next(stream)

    frames = 4096

    pcm = stream.send(frames)

    print(f"PCM type: {type(pcm)}")
    print(f"Samples: {len(pcm)}")
    print(f"Expected samples: {frames * 2}")


if __name__ == "__main__":
    main()
