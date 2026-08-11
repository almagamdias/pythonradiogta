from __future__ import annotations

from pathlib import Path

from radio.engine import RadioEngine
from radio.library.gen1 import Gen1Loader
from radio.model.station import Station
from radio.model.song import Song
from radio.model.station_library import StationLibrary
from radio.model.station_state import StationState


TEST_ROOT = Path("test_data/GTA IV")


def create_engine() -> RadioEngine:
    library = Gen1Loader().load(TEST_ROOT)
    return RadioEngine(library)


def main() -> None:
    engine = create_engine()

    print("Testing RadioEngine public API...")

    # stations
    stations = engine.stations

    assert isinstance(stations, StationLibrary)
    assert len(stations) > 0

    print(f"Stations: {len(stations)}")

    # current_station
    station = engine.current_station

    assert isinstance(station, Station)

    print(f"Current station: {station.name}")

    # current_song
    song = engine.current_song

    assert isinstance(song, Song)

    print(f"Current song: {song.title}")
    print(f"Song path: {song.path}")

    # initial state
    assert engine.state is StationState.OFF

    print(f"Initial state: {engine.state.value}")

    # play()
    print()
    print("Calling play()...")

    engine.play()

    assert engine.state is StationState.ON_AIR

    print(f"State after play: {engine.state.value}")

    # Calling play() again must not create another playback
    print("Calling play() again...")

    engine.play()

    assert engine.state is StationState.ON_AIR

    print(f"State after second play: {engine.state.value}")

    # next_station()
    print()
    print("Testing next_station()...")

    initial_station = engine.current_station

    engine.stop()

    assert engine.state is StationState.OFF

    engine.next_station()

    next_station = engine.current_station

    assert next_station is not initial_station
    assert engine.state is StationState.OFF

    print(f"Initial station: {initial_station.name}")
    print(f"Next station: {next_station.name}")

    # previous_station()
    print()
    print("Testing previous_station()...")

    engine.previous_station()

    previous_station = engine.current_station

    assert previous_station is initial_station
    assert engine.state is StationState.OFF

    print(f"Previous station: {previous_station.name}")

    # play after station navigation
    print()
    print("Testing play() after station navigation...")

    engine.play()

    assert engine.state is StationState.ON_AIR
    assert engine.current_station is initial_station

    print(f"Playing station: {engine.current_station.name}")
    print(f"Playing song: {engine.current_song.title}")

    # stop()
    print()
    print("Testing stop()...")

    engine.stop()

    assert engine.state is StationState.OFF

    print(f"Final state: {engine.state.value}")

    # stop() must be safe when already stopped
    print("Calling stop() again...")

    engine.stop()

    assert engine.state is StationState.OFF

    print("Second stop() is safe.")

    print()
    print("RadioEngine public API test passed.")


if __name__ == "__main__":
    main()
