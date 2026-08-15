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
    print("Testing independent station EOF timelines...")

    engine = create_engine()

    engine.play()

    assert engine.state is StationState.ON_AIR

    print()
    print("Radio started.")
    print(
        f"Initial station: "
        f"{engine.current_station.name}"
    )

    # ---------------------------------------------------------
    # Save the initial independent timeline positions.
    # ---------------------------------------------------------

    massiveb_index = 0
    thebeat_index = 1
    ramjam_index = 2

    massiveb = engine.stations[massiveb_index]
    thebeat = engine.stations[thebeat_index]
    ramjam = engine.stations[ramjam_index]

    print()
    print("Station durations:")
    print(
        f"{massiveb.name}: "
        f"{massiveb.songs[0].duration} ms"
    )
    print(
        f"{thebeat.name}: "
        f"{thebeat.songs[0].duration} ms"
    )
    print(
        f"{ramjam.name}: "
        f"{ramjam.songs[0].duration} ms"
    )

    # ---------------------------------------------------------
    # The engine already creates an independent start position
    # for every station.
    # ---------------------------------------------------------

    start_positions = engine._station_start_positions.copy()

    assert massiveb_index in start_positions
    assert thebeat_index in start_positions
    assert ramjam_index in start_positions

    print()
    print("Initial station timeline positions:")

    print(
        f"{massiveb.name}: "
        f"{start_positions[massiveb_index]} ms"
    )
    print(
        f"{thebeat.name}: "
        f"{start_positions[thebeat_index]} ms"
    )
    print(
        f"{ramjam.name}: "
        f"{start_positions[ramjam_index]} ms"
    )

    # ---------------------------------------------------------
    # Move through several stations so that all three timelines
    # are participating in the same radio timeline.
    # ---------------------------------------------------------

    print()
    print("Switching to THEBEAT...")

    engine.next_station()
    wait_for_on_air(engine)

    assert engine.current_station.name == "12_THEBEAT"

    print(
        f"Current station: "
        f"{engine.current_station.name}"
    )

    time.sleep(1.0)

    print()
    print("Switching to RAMJAM...")

    engine.next_station()
    wait_for_on_air(engine)

    assert engine.current_station.name == "13_RAMJAM"

    print(
        f"Current station: "
        f"{engine.current_station.name}"
    )

    time.sleep(1.0)

    # ---------------------------------------------------------
    # Calculate positions before the artificial EOF test.
    # ---------------------------------------------------------

    before_thebeat = engine._station_position(
        thebeat_index
    )

    before_ramjam = engine._station_position(
        ramjam_index
    )

    print()
    print("Timeline positions before EOF test:")

    print(
        f"{thebeat.name}: "
        f"{before_thebeat} ms"
    )
    print(
        f"{ramjam.name}: "
        f"{before_ramjam} ms"
    )

    # ---------------------------------------------------------
    # We now simulate the exact condition we care about:
    #
    # MASSIVEB's cyclic timeline reaches EOF.
    #
    # Only MASSIVEB must wrap.
    # THEBEAT and RAMJAM must continue their own timelines.
    # ---------------------------------------------------------

    print()
    print("Testing MASSIVEB EOF wrap...")

    massiveb_duration = massiveb.songs[0].duration

    assert massiveb_duration > 0

    # Force the timeline calculation to the point where
    # MASSIVEB has completed one complete cycle.
    #
    # The actual engine formula is:
    #
    # (start_position + elapsed) % duration
    #
    # Therefore MASSIVEB wraps to the beginning while the
    # other stations use their own duration.
    original_started_at = engine._radio_started_at

    assert original_started_at is not None

    # Calculate elapsed time required to reach MASSIVEB EOF.
    current_massiveb_position = engine._station_position(
        massiveb_index
    )

    remaining_to_eof = (
        massiveb_duration
        - current_massiveb_position
    )

    # ---------------------------------------------------------
    # Instead of sleeping for the complete audio duration,
    # move the radio timeline clock forward logically.
    # ---------------------------------------------------------

    engine._radio_started_at = (
        original_started_at
        - remaining_to_eof / 1000
    )

    massiveb_after_eof = engine._station_position(
        massiveb_index
    )

    thebeat_after_eof = engine._station_position(
        thebeat_index
    )

    ramjam_after_eof = engine._station_position(
        ramjam_index
    )

    print()
    print("Positions after MASSIVEB reaches EOF:")

    print(
        f"{massiveb.name}: "
        f"{massiveb_after_eof} ms"
    )
    print(
        f"{thebeat.name}: "
        f"{thebeat_after_eof} ms"
    )
    print(
        f"{ramjam.name}: "
        f"{ramjam_after_eof} ms"
    )

    # MASSIVEB must have wrapped to the beginning.
    assert (
        massiveb_after_eof
        < 100
    ), (
        "MASSIVEB did not wrap to the beginning "
        "after EOF"
    )

    # THEBEAT and RAMJAM must NOT reset to their initial
    # positions. Their timelines are independent.
    assert (
        thebeat_after_eof
        != start_positions[thebeat_index]
    ), (
        "THEBEAT incorrectly reset when "
        "MASSIVEB reached EOF"
    )

    assert (
        ramjam_after_eof
        != start_positions[ramjam_index]
    ), (
        "RAMJAM incorrectly reset when "
        "MASSIVEB reached EOF"
    )

    print()
    print(
        "MASSIVEB wrapped independently."
    )
    print(
        "THEBEAT timeline continued independently."
    )
    print(
        "RAMJAM timeline continued independently."
    )

    # ---------------------------------------------------------
    # Restore the real clock before stopping the engine.
    # ---------------------------------------------------------

    engine._radio_started_at = original_started_at

    engine.stop()

    assert engine.state is StationState.OFF

    print()
    print(
        "Final state: "
        f"{engine.state.value}"
    )

    print()
    print(
        "Independent station EOF timeline "
        "test passed."
    )


if __name__ == "__main__":
    main()
