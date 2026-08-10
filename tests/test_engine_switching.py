from __future__ import annotations

import time
from pathlib import Path

from radio.engine import RadioEngine
from radio.library.gen1 import Gen1Loader
from radio.model.station_state import StationState


TEST_ROOT = Path("test_data/GTA IV")


def main() -> None:
    library = Gen1Loader().load(TEST_ROOT)
    engine = RadioEngine(library)

    assert engine.state is StationState.OFF
    assert engine.current_station.name == "04_MASSIVEB"

    engine.play()

    assert engine.state is StationState.ON_AIR
    assert engine.current_station.name == "04_MASSIVEB"

    engine.next_station()

    assert engine.state is StationState.SWITCHING
    assert engine.current_station.name == "04_MASSIVEB"

    time.sleep(0.5)

    # Станция ещё не должна переключиться.
    assert engine.current_station.name == "04_MASSIVEB"
    assert engine.state is StationState.SWITCHING

    engine.next_station()

    # Повторное нажатие должно оставить нас
    # в switching и сбросить таймер.
    assert engine.state is StationState.SWITCHING
    assert engine.current_station.name == "04_MASSIVEB"

    time.sleep(0.7)

    # После первого таймера прошло бы 1.2 сек,
    # но второй start() сбросил его.
    assert engine.current_station.name == "04_MASSIVEB"
    assert engine.state is StationState.SWITCHING

    time.sleep(0.5)

    assert engine.current_station.name == "13_RAMJAM"
    assert engine.state is StationState.ON_AIR

    engine.stop()

    print("Engine switching test passed.")


if __name__ == "__main__":
    main()
