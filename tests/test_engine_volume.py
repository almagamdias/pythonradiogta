from __future__ import annotations

from pathlib import Path

from radio.audio.player import AudioPlayer
from radio.engine import RadioEngine
from radio.model.song import Song
from radio.model.station import Station
from radio.model.station_library import StationLibrary


TEST_FILE = Path(
    "test_data/GTA IV/04_MASSIVEB/MASSIVEB_MIX.ogg"
)


def create_test_library() -> StationLibrary:
    song = Song(
        title="MASSIVEB_MIX",
        path=TEST_FILE,
        duration=1_958_361,
    )

    station = Station(
        name="04_MASSIVEB",
        songs=[song],
    )

    return StationLibrary([station])


def main() -> None:
    print("Testing RadioEngine volume API...")

    engine = RadioEngine(create_test_library())

    print(f"Initial volume: {engine.volume}")
    assert engine.volume == 1.0

    print()
    print("Setting volume before playback...")
    engine.volume = 0.5

    assert engine.volume == 0.5
    print(f"Volume: {engine.volume}")

    print()
    print("Starting playback...")
    engine.play()

    assert engine.state.value == "on_air"
    assert engine._player is not None
    assert engine._player.volume == 0.5

    print(f"Engine volume:  {engine.volume}")
    print(f"Player volume:  {engine._player.volume}")

    print()
    print("Changing volume during playback...")
    engine.volume = 0.25

    assert engine.volume == 0.25
    assert engine._player.volume == 0.25

    print(f"Engine volume:  {engine.volume}")
    print(f"Player volume:  {engine._player.volume}")

    print()
    print("Testing mute...")
    engine.volume = 0.0

    assert engine.volume == 0.0
    assert engine._player.volume == 0.0

    print(f"Engine volume:  {engine.volume}")
    print(f"Player volume:  {engine._player.volume}")

    print()
    print("Testing volume limits...")

    try:
        engine.volume = -0.1
    except ValueError:
        print("Negative volume rejected.")
    else:
        raise AssertionError(
            "Negative volume must raise ValueError"
        )

    try:
        engine.volume = 1.1
    except ValueError:
        print("Volume above 1.0 rejected.")
    else:
        raise AssertionError(
            "Volume above 1.0 must raise ValueError"
        )

    print()
    print("Stopping playback...")
    engine.stop()

    print(f"State: {engine.state.value}")

    print()
    print("Testing volume persistence after restart...")

    engine.volume = 0.75
    engine.play()

    assert engine.volume == 0.75
    assert engine._player is not None
    assert engine._player.volume == 0.75

    print(f"Engine volume:  {engine.volume}")
    print(f"Player volume:  {engine._player.volume}")

    engine.stop()

    print()
    print("RadioEngine volume test passed.")


if __name__ == "__main__":
    main()
