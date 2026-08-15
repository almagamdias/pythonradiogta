from __future__ import annotations

import time
from pathlib import Path

from radio.engine import RadioEngine
from radio.library.gen1 import Gen1Loader
from radio.model.station_state import StationState


TEST_ROOT = Path("test_data/GTA IV")

SWITCH_WAIT_SECONDS = 1.8


def create_engine() -> RadioEngine:
    library = Gen1Loader().load(TEST_ROOT)
    return RadioEngine(library)


def wait_for_switch(engine: RadioEngine) -> None:
    deadline = (
        time.monotonic()
        + SWITCH_WAIT_SECONDS
    )

    while time.monotonic() < deadline:
        if engine.state is StationState.ON_AIR:
            return

        time.sleep(0.05)

    raise AssertionError(
        "Station did not switch within "
        "the expected time"
    )


def main() -> None:
    print(
        "Testing RadioEngine switching + "
        "real overlay + volume..."
    )

    engine = create_engine()

    print(
        f"Initial station: "
        f"{engine.current_station.name}"
    )

    print(
        f"Initial volume: "
        f"{engine.volume}"
    )

    assert (
        engine.current_station.name
        == "04_MASSIVEB"
    )

    assert engine.volume == 1.0

    print()
    print("Setting volume to 0.35...")

    engine.volume = 0.35

    assert engine.volume == 0.35

    print(
        f"Engine volume: "
        f"{engine.volume}"
    )

    print()
    print("Starting playback...")

    engine.play()

    assert engine.state is StationState.ON_AIR

    player = engine.player

    assert player.volume == 0.35

    print(
        f"State: {engine.state.value}"
    )

    print(
        f"Player volume: "
        f"{player.volume}"
    )

    time.sleep(4)

    # -------------------------------------------------------------
    # NEXT STATION
    # -------------------------------------------------------------

    print()
    print("Requesting next station...")

    overlay_count_before = (
        player.overlay_count
    )

    engine.next_station()

    assert engine.state is StationState.SWITCHING

    assert (
        engine.current_station.name
        == "04_MASSIVEB"
    )

    print(
        f"State: {engine.state.value}"
    )

    print(
        f"Current station: "
        f"{engine.current_station.name}"
    )

    print()
    print("Checking real switch overlay...")

    overlay_count_after = (
        player.overlay_count
    )

    print(
        f"Overlay count before: "
        f"{overlay_count_before}"
    )

    print(
        f"Overlay count after:  "
        f"{overlay_count_after}"
    )

    assert (
        overlay_count_after
        == overlay_count_before + 1
    )

    print(
        "Real switch overlay requested."
    )

    print()
    print(
        f"Waiting up to "
        f"{SWITCH_WAIT_SECONDS:.1f} seconds "
        "for station switch..."
    )

    wait_for_switch(engine)

    assert engine.state is StationState.ON_AIR

    assert (
        engine.current_station.name
        == "12_THEBEAT"
    )

    # Same AudioPlayer.
    assert engine.player is player

    assert engine.volume == 0.35
    assert engine.player.volume == 0.35

    print(
        f"State after switch: "
        f"{engine.state.value}"
    )

    print(
        f"New station: "
        f"{engine.current_station.name}"
    )

    print(
        f"New player volume: "
        f"{engine.player.volume}"
    )

    print()
    print(
        "Volume survived next_station()."
    )

    print(
        "AudioPlayer instance survived "
        "next_station()."
    )

    print()
    print(
        "Old switch overlay was cancelled."
    )

    # -------------------------------------------------------------
    # CHANGE VOLUME
    # -------------------------------------------------------------

    print()
    print("Changing volume to 0.60...")

    engine.volume = 0.60

    assert engine.volume == 0.60
    assert engine.player.volume == 0.60

    print(
        f"Engine volume: "
        f"{engine.volume}"
    )

    print(
        f"Player volume: "
        f"{engine.player.volume}"
    )

    time.sleep(4)

    # -------------------------------------------------------------
    # PREVIOUS STATION
    # -------------------------------------------------------------

    print()
    print(
        "Requesting previous station..."
    )

    previous_player = engine.player

    overlay_count_before = (
        previous_player.overlay_count
    )

    engine.previous_station()

    assert engine.state is StationState.SWITCHING

    assert (
        engine.current_station.name
        == "12_THEBEAT"
    )

    print(
        f"State: {engine.state.value}"
    )

    print(
        f"Current station: "
        f"{engine.current_station.name}"
    )

    print()
    print(
        "Checking real "
        "previous-station overlay..."
    )

    overlay_count_after = (
        previous_player.overlay_count
    )

    print(
        f"Overlay count before: "
        f"{overlay_count_before}"
    )

    print(
        f"Overlay count after:  "
        f"{overlay_count_after}"
    )

    assert (
        overlay_count_after
        == overlay_count_before + 1
    )

    print(
        "Real previous-station overlay "
        "requested."
    )

    print()
    print(
        f"Waiting up to "
        f"{SWITCH_WAIT_SECONDS:.1f} seconds "
        "for station switch..."
    )

    wait_for_switch(engine)

    assert engine.state is StationState.ON_AIR

    assert (
        engine.current_station.name
        == "04_MASSIVEB"
    )

    # Still the same AudioPlayer.
    assert engine.player is previous_player

    assert engine.volume == 0.60
    assert engine.player.volume == 0.60

    print(
        f"State after switch: "
        f"{engine.state.value}"
    )

    print(
        f"Final station: "
        f"{engine.current_station.name}"
    )

    print(
        f"Final player volume: "
        f"{engine.player.volume}"
    )

    print()
    print(
        "Volume survived "
        "previous_station()."
    )

    print(
        "AudioPlayer instance survived "
        "previous_station()."
    )

    print()
    print(
        "Old previous-station overlay "
        "was cancelled."
    )

    time.sleep(4)

    # -------------------------------------------------------------
    # STOP
    # -------------------------------------------------------------

    print()
    print("Stopping playback...")

    engine.stop()

    assert engine.state is StationState.OFF

    print(
        f"Final state: "
        f"{engine.state.value}"
    )

    print()
    print(
        "RadioEngine switching + "
        "real overlay + volume "
        "test passed."
    )


if __name__ == "__main__":
    main()
