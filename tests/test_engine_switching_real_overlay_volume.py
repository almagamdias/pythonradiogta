from __future__ import annotations

import time
from pathlib import Path

from radio.engine import RadioEngine
from radio.library.gen1 import Gen1Loader
from radio.model.station_state import StationState


TEST_ROOT = Path("test_data/GTA IV")

# У вас задержка переключения была увеличена до 1500 мс.
# Берём небольшой запас.
SWITCH_WAIT_SECONDS = 1.8


def create_engine() -> RadioEngine:
    library = Gen1Loader().load(TEST_ROOT)
    return RadioEngine(library)


def wait_for_switch(engine: RadioEngine) -> None:
    deadline = time.monotonic() + SWITCH_WAIT_SECONDS

    while time.monotonic() < deadline:
        if engine.state is StationState.ON_AIR:
            return

        time.sleep(0.05)

    raise AssertionError(
        "Station did not switch within the expected time"
    )


def main() -> None:
    print(
        "Testing RadioEngine switching + "
        "real overlay + volume..."
    )

    engine = create_engine()

    print(f"Initial station: {engine.current_station.name}")
    print(f"Initial volume: {engine.volume}")

    assert engine.current_station.name == "04_MASSIVEB"
    assert engine.volume == 1.0

    print()
    print("Setting volume to 0.35...")

    engine.volume = 0.35

    assert engine.volume == 0.35

    print(f"Engine volume: {engine.volume}")

    print()
    print("Starting playback...")

    engine.play()

    assert engine.state is StationState.ON_AIR
    assert engine._player is not None
    assert engine._player.volume == 0.35

    print(f"State: {engine.state.value}")
    print(f"Player volume: {engine._player.volume}")

    old_player = engine._player
    overlay_count_before = old_player.overlay_count

    time.sleep(4)

    print()
    print("Requesting next station...")

    engine.next_station()

    assert engine.state is StationState.SWITCHING
    assert engine.current_station.name == "04_MASSIVEB"

    print(f"State: {engine.state.value}")
    print(f"Current station: {engine.current_station.name}")

    print()
    print("Checking real switch overlay...")

    overlay_count_after = old_player.overlay_count

    print(f"Overlay count before: {overlay_count_before}")
    print(f"Overlay count after:  {overlay_count_after}")

    assert overlay_count_after == overlay_count_before + 1

    print("Real switch overlay requested.")

    print()
    print(
        f"Waiting up to {SWITCH_WAIT_SECONDS:.1f} seconds "
        "for station switch..."
    )

    wait_for_switch(engine)

    assert engine.state is StationState.ON_AIR
    assert engine.current_station.name == "12_THEBEAT"
    assert engine._player is not None

    new_player = engine._player

    print(f"State after switch: {engine.state.value}")
    print(f"New station: {engine.current_station.name}")
    print(f"New player volume: {new_player.volume}")

    assert new_player is not old_player
    assert engine.volume == 0.35
    assert new_player.volume == 0.35

    print()
    print("Volume survived next_station().")

    print()
    print("Changing volume to 0.60...")

    engine.volume = 0.60

    assert engine.volume == 0.60
    assert engine._player.volume == 0.60

    print(f"Engine volume: {engine.volume}")
    print(f"Player volume: {engine._player.volume}")

    time.sleep(4)

    print()
    print("Requesting previous station...")

    previous_player = engine._player
    overlay_count_before = previous_player.overlay_count

    engine.previous_station()

    assert engine.state is StationState.SWITCHING
    assert engine.current_station.name == "12_THEBEAT"

    print(f"State: {engine.state.value}")
    print(f"Current station: {engine.current_station.name}")

    print()
    print("Checking real previous-station overlay...")

    overlay_count_after = previous_player.overlay_count

    print(f"Overlay count before: {overlay_count_before}")
    print(f"Overlay count after:  {overlay_count_after}")

    assert overlay_count_after == overlay_count_before + 1

    print("Real previous-station overlay requested.")

    print()
    print(
        f"Waiting up to {SWITCH_WAIT_SECONDS:.1f} seconds "
        "for station switch..."
    )

    wait_for_switch(engine)

    assert engine.state is StationState.ON_AIR
    assert engine.current_station.name == "04_MASSIVEB"
    assert engine._player is not None

    final_player = engine._player

    print(f"State after switch: {engine.state.value}")
    print(f"Final station: {engine.current_station.name}")
    print(f"Final player volume: {final_player.volume}")

    assert final_player is not previous_player
    assert engine.volume == 0.60
    assert final_player.volume == 0.60

    print()
    print("Volume survived previous_station().")

    time.sleep(4)

    print()
    print("Stopping playback...")

    engine.stop()

    assert engine.state is StationState.OFF

    print(f"Final state: {engine.state.value}")

    print()
    print(
        "RadioEngine switching + real overlay + "
        "volume test passed."
    )


if __name__ == "__main__":
    main()
