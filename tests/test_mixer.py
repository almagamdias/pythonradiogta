from array import array

from radio.audio.mixer import mix_pcm


def main() -> None:
    main_audio = array(
        "h",
        [1000, 2000, -3000, 30000],
    )

    overlay_audio = array(
        "h",
        [500, -500, -1000, 10000],
    )

    result = mix_pcm(
        main_audio,
        overlay_audio,
    )

    expected = array(
        "h",
        [1500, 1500, -4000, 32767],
    )

    assert result == expected

    print("PCM mixer test passed.")


if __name__ == "__main__":
    main()
