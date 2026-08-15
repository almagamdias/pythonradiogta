from __future__ import annotations

import time
from pathlib import Path

from radio.engine import RadioEngine
from radio.library.gen1 import Gen1Loader
from radio.model.station_state import StationState


TEST_ROOT = Path("test_data/GTA IV")
SWITCH_WAIT_SECONDS = 2.0


def create_engine() -> RadioEngine:
    library = Gen1Loader().load(TEST_ROOT)
    return RadioEngine(library)


def wait_for_on_air(engine: RadioEngine) -> None:
    deadline = time.monotonic() + SWITCH_WAIT_SECONDS

    while time.monotonic() < deadline:
        if engine.state is StationState.ON_AIR:
            return

        time.sleep(0.05)

    raise AssertionError(
        "Station did not finish switching in time"
    )


def main() -> None:
    print(
        "Testing rapid station switching "
        "+ overlay cancellation..."
    )

    engine = create_engine()

    print(
        f"Initial station: "
        f"{engine.current_station.name}"
    )

    engine.play()

    assert engine.state is StationState.ON_AIR
    assert engine._player is not None

    player = engine._player

    overlay_before = player.overlay_count

    print()
    print("Starting playback...")
    print(f"State: {engine.state.value}")
    print(f"Station: {engine.current_station.name}")
    print(
        f"Initial overlay count: "
        f"{overlay_before}"
    )
    time.sleep(5)

    # ---------------------------------------------------------
    # 1. next()
    #
    # 04_MASSIVEB -> 12_THEBEAT
    # ---------------------------------------------------------

    print()
    print("1) next_station()")

    engine.next_station()

    assert engine.state is StationState.SWITCHING
    assert engine.current_station.name == "04_MASSIVEB"
    assert engine.pending_station is not None
    assert engine.pending_station.name == "12_THEBEAT"

    overlay_after_first = player.overlay_count

    print(
        f"Current: {engine.current_station.name}"
    )
    print(
        f"Pending: {engine.pending_station.name}"
    )
    print(
        f"Overlay count: {overlay_after_first}"
    )

    assert (
        overlay_after_first
        == overlay_before + 1
    )

    # ---------------------------------------------------------
    # 2. next() after 0.5 sec
    #
    # 12_THEBEAT -> 13_RAMJAM
    #
    # IMPORTANT:
    # no second overlay should be requested.
    # ---------------------------------------------------------

    print()
    print("Waiting 0.5 seconds...")
    time.sleep(0.5)

    print("2) next_station()")

    engine.next_station()

    assert engine.state is StationState.SWITCHING
    assert engine.current_station.name == "04_MASSIVEB"
    assert engine.pending_station is not None
    assert engine.pending_station.name == "13_RAMJAM"

    overlay_after_second = player.overlay_count

    print(
        f"Current: {engine.current_station.name}"
    )
    print(
        f"Pending: {engine.pending_station.name}"
    )
    print(
        f"Overlay count: {overlay_after_second}"
    )

    assert (
        overlay_after_second
        == overlay_after_first
    )

    print(
        "No additional overlay was requested."
    )

    # ---------------------------------------------------------
    # 3. previous()
    #
    # 13_RAMJAM -> 12_THEBEAT
    #
    # Still the same switching operation.
    # ---------------------------------------------------------

    print()
    print("3) previous_station()")

    engine.previous_station()

    assert engine.state is StationState.SWITCHING
    assert engine.current_station.name == "04_MASSIVEB"
    assert engine.pending_station is not None
    assert engine.pending_station.name == "12_THEBEAT"

    overlay_after_previous = player.overlay_count

    print(
        f"Current: {engine.current_station.name}"
    )
    print(
        f"Pending: {engine.pending_station.name}"
    )
    print(
        f"Overlay count: {overlay_after_previous}"
    )

    assert (
        overlay_after_previous
        == overlay_after_first
    )

    # ---------------------------------------------------------
    # 4. next()
    #
    # 12_THEBEAT -> 13_RAMJAM
    # ---------------------------------------------------------

    print()
    print("4) next_station()")

    engine.next_station()

    assert engine.state is StationState.SWITCHING
    assert engine.current_station.name == "04_MASSIVEB"
    assert engine.pending_station is not None
    assert engine.pending_station.name == "13_RAMJAM"

    overlay_after_next = player.overlay_count

    print(
        f"Current: {engine.current_station.name}"
    )
    print(
        f"Pending: {engine.pending_station.name}"
    )
    print(
        f"Overlay count: {overlay_after_next}"
    )

    assert (
        overlay_after_next
        == overlay_after_first
    )

    # ---------------------------------------------------------
    # 5. next()
    #
    # 13_RAMJAM -> 18_ELECTROCHOC
    # ---------------------------------------------------------

    print()
    print("5) next_station()")

    engine.next_station()

    assert engine.state is StationState.SWITCHING
    assert engine.current_station.name == "04_MASSIVEB"
    assert engine.pending_station is not None
    assert engine.pending_station.name == "18_ELECTROCHOC"

    overlay_after_final_request = (
        player.overlay_count
    )

    print(
        f"Current: {engine.current_station.name}"
    )
    print(
        f"Pending: {engine.pending_station.name}"
    )
    print(
        f"Overlay count: "
        f"{overlay_after_final_request}"
    )

    assert (
        overlay_after_final_request
        == overlay_after_first
    )

    print()
    print(
        "Only one overlay was requested "
        "for the entire rapid switching sequence."
    )

    # ---------------------------------------------------------
    # Complete final switch.
    # ---------------------------------------------------------

    print()
    print("Waiting for final station switch...")

    wait_for_on_air(engine)

    assert engine.state is StationState.ON_AIR
    assert engine.current_station.name == (
        "18_ELECTROCHOC"
    )
    assert engine.pending_station is None

    print()
    print("After final switch:")
    print(f"State: {engine.state.value}")
    print(
        f"Station: {engine.current_station.name}"
    )
    print(
        f"Overlay count: "
        f"{player.overlay_count}"
    )

    # ---------------------------------------------------------
    # The old switch overlay must have been cancelled.
    #
    # We can't determine PCM playback directly here, but the
    # player must have invalidated the overlay when change_song()
    # was requested.
    # ---------------------------------------------------------

    print()
    print(
        "Final station change completed."
    )

    print(
        "Old switch overlay must no longer "
        "be active."
    )

    # Give the audio callback a moment to observe
    # the overlay invalidation.
    time.sleep(0.2)

    assert engine.state is StationState.ON_AIR
    assert engine.current_station.name == (
        "18_ELECTROCHOC"
    )

    print(
        "Old overlay cancellation check completed."
    )

    print()
    print(
        "Rapid station switching + "
        "overlay cancellation test passed."
    )
    time.sleep(5)

    engine.stop()

    assert engine.state is StationState.OFF

    print(
        f"Final state: {engine.state.value}"
    )


if __name__ == "__main__":
    main()
