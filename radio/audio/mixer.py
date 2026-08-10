from __future__ import annotations

from array import array
from collections.abc import Generator

AudioStream = Generator[array, int, None]

MIN_INT16 = -32768
MAX_INT16 = 32767


def mix_pcm(
    main: array,
    overlay: array,
) -> array:
    """Mix two signed 16-bit PCM buffers."""
    length = min(len(main), len(overlay))

    output = array("h", main)

    for index in range(length):
        value = main[index] + overlay[index]

        if value > MAX_INT16:
            value = MAX_INT16
        elif value < MIN_INT16:
            value = MIN_INT16

        output[index] = value

    return output
