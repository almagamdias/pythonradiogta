from __future__ import annotations

import math
import time
import wave
from pathlib import Path

from radio.engine import RadioEngine
from radio.model.song import Song
from radio.model.station import Station
from radio.model.station_library import StationLibrary
from radio.model.station_state import StationState


TEST_FILE = Path("tests/test_loop.wav")


def create_test_wav() -> None:
    sample_rate = 48_000
    duration = 2
    frames = sample_rate * duration

    with wave.open(str(TEST_FILE), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)

        for i in range(frames):
            phase = i / sample_rate

            sample = int(
                0.2
                * 32767
                * math.sin(2 * math.pi * 440 * phase)
            )

            data = sample.to_bytes(
                2,
                "little",
                signed=True,
            )

            wav.writeframes(data + data)


def create_test_library() -> StationLibrary:
    song = Song(
        title="TEST_LOOP",
        path=TEST_FILE,
        duration=2000,
    )

    station = Station(
        name="TEST_LOOP",
        songs=[song],
    )

    return StationLibrary([station])


def main() -> None:
    create_test_wav()

    library = create_test_library()
    engine = RadioEngine(library)

    station = engine.current_station
    song = engine.current_song

    print(f"Station: {station.name}")
    print(f"Song: {song.path}")
    print("The file is 2 seconds long.")
    print("Playback will run for 10 seconds.")
    print("Expected: approximately 5 loops.")

    try:
        engine.play()

        time.sleep(10)

        print(f"State: {engine.state.value}")
        print(
            f"Station after playback: "
            f"{engine.current_station.name}"
        )
        print(
            f"Song after playback: "
            f"{engine.current_song.path}"
        )

        assert engine.state is StationState.ON_AIR
        assert engine.current_station is station
        assert engine.current_song is song

        print()
        print("Engine loop test passed.")

    finally:
        engine.stop()


if __name__ == "__main__":
    main()
